"""Email classification service for AI-powered email categorization.

This service handles email classification, holistic analysis,
and bulk classification operations with rate limiting.
"""

import asyncio
import logging
from typing import Dict, Any, List

from backend.database.connection import db_manager
from backend.services.ai_service import AIService
from backend.services.email_provider import EmailProvider
from backend.core.rate_limiter import get_rate_limiter


# Configure module logger
logger = logging.getLogger(__name__)


class ClassificationError(Exception):
    """Base exception for classification errors."""
    pass


class AIProcessingError(ClassificationError):
    """Raised when AI processing fails."""
    pass


class RateLimitError(ClassificationError):
    """Raised when rate limits are exceeded."""
    pass


class ContentFilterError(ClassificationError):
    """Raised when content is blocked by filters."""
    pass


class EmailClassificationService:
    """Service for AI-powered email classification operations."""

    def __init__(self, ai_service: AIService, email_provider: EmailProvider):
        """Initialize the email classification service.

        Args:
            ai_service: AI service for classification
            email_provider: Email provider for Outlook operations
        """
        self.ai_service = ai_service
        self.email_provider = email_provider
        self.rate_limiter = get_rate_limiter()
        self._load_category_mappings()

    def _load_category_mappings(self) -> None:
        """Load category to folder mappings from COM email provider."""
        try:
            from backend.services.com_email_provider import INBOX_CATEGORIES, NON_INBOX_CATEGORIES
            self.inbox_categories = INBOX_CATEGORIES
            self.non_inbox_categories = NON_INBOX_CATEGORIES
            self.all_categories = {**INBOX_CATEGORIES, **NON_INBOX_CATEGORIES}
            logger.info("[Classification] Loaded category mappings successfully")
        except ImportError:
            logger.warning("[Classification] Could not load category mappings, using defaults")
            self.inbox_categories = {}
            self.non_inbox_categories = {}
            self.all_categories = {}

    async def analyze_holistically(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform holistic analysis across multiple emails.

        This identifies expired items, superseded actions, and duplicates
        by analyzing emails together rather than individually.

        Args:
            emails: List of emails to analyze holistically

        Returns:
            Dictionary with analysis results including expired_items,
            superseded_actions, and duplicate_groups

        Raises:
            AIProcessingError: If AI analysis fails
        """
        if not emails:
            return {
                'expired_items': [],
                'superseded_actions': [],
                'duplicate_groups': [],
                'truly_relevant_actions': []
            }

        try:
            logger.info(f"[Holistic] Starting holistic analysis for {len(emails)} emails")

            # Rate limiting before AI call
            await self.rate_limiter.holistic_analysis_delay()

            result = await self.ai_service.analyze_holistically(emails)

            # Log analysis results
            expired_count = len(result.get('expired_items', []))
            superseded_count = len(result.get('superseded_actions', []))
            duplicate_groups = len(result.get('duplicate_groups', []))

            logger.info(f"[Holistic] Analysis complete: {expired_count} expired, "
                       f"{superseded_count} superseded, {duplicate_groups} duplicate groups")

            return result

        except Exception as e:
            error_msg = str(e).lower()
            if 'content_filter' in error_msg or 'responsibleaipolicyviolation' in error_msg:
                logger.warning(f"[Holistic] [FILTER] Content filter blocked holistic analysis: {e}")
                raise ContentFilterError("Content blocked by AI content policy")
            elif 'rate' in error_msg or 'quota' in error_msg or '429' in error_msg:
                logger.warning(f"[Holistic] [RATE] Rate limit hit during holistic analysis: {e}")
                raise RateLimitError("AI service rate limit exceeded")
            else:
                logger.error(f"[Holistic] AI processing failed: {e}")
                raise AIProcessingError(f"Holistic analysis failed: {str(e)}")

    async def classify_email_if_needed(
        self,
        email: Dict[str, Any],
        body_cache: Dict[str, str] = None
    ) -> str:
        """Classify an email if it doesn't already have a category.

        Args:
            email: Email dictionary with metadata
            body_cache: Optional cache of email bodies by ID

        Returns:
            Email category

        Raises:
            AIProcessingError: If classification fails
        """
        # Return existing category if present
        if email.get('ai_category'):
            return email['ai_category']

        try:
            # Get email body
            body = email.get('body', '')
            if not body and body_cache:
                body = body_cache.get(email['id'], '')

            # Prepare email text for classification
            email_text = f"Subject: {email.get('subject', '')}\n"
            email_text += f"From: {email.get('sender', '')}\n\n"
            email_text += body

            # Classify with rate limiting
            await self.rate_limiter.classification_delay()

            classification_result = await self.ai_service.classify_email(
                email_content=email_text
            )

            category = classification_result.get('category', 'work_relevant')
            logger.info(f"[Classification] Classified email {email['id'][:20]}... as '{category}'")

            return category

        except Exception as e:
            logger.error(f"[Classification] Failed to classify email: {e}")
            raise AIProcessingError(f"Email classification failed: {str(e)}")

    async def bulk_apply_classifications(
        self,
        email_ids: List[str],
        apply_to_outlook: bool = True
    ) -> Dict[str, Any]:
        """Bulk apply AI classifications to Outlook folders.

        Args:
            email_ids: List of email IDs to process
            apply_to_outlook: Whether to move emails to Outlook folders

        Returns:
            Dictionary with processing results and statistics

        Raises:
            ClassificationError: If bulk processing fails
        """
        if not email_ids:
            return {
                'success': True,
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'errors': []
            }

        try:
            logger.info(f"[BulkApply] Starting bulk apply for {len(email_ids)} emails")

            successful = 0
            failed = 0
            errors = []

            # CRITICAL: COM operations must be serialized - no concurrent access
            loop = asyncio.get_event_loop()

            for email_id in email_ids:
                try:
                    # Get email data in executor to ensure proper COM threading
                    def _get_email():
                        return self.email_provider.get_email_by_id(email_id)

                    email = await loop.run_in_executor(None, _get_email)
                    if not email:
                        logger.warning(f"[BulkApply] Email {email_id[:20]}... not found, skipping")
                        continue

                    # Get or determine AI category
                    ai_category = email.get('ai_category')

                    if not ai_category:
                        # Classify the email first
                        email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('body', '')}"

                        try:
                            classification_result = await self.ai_service.classify_email(
                                email_content=email_text
                            )
                            ai_category = classification_result.get('category', 'work_relevant')
                        except Exception as classify_error:
                            errors.append(f"Failed to classify email {email_id}: {str(classify_error)}")
                            ai_category = 'work_relevant'  # Fallback category

                    # Apply to Outlook if requested
                    if apply_to_outlook:
                        folder_name = self.all_categories.get(ai_category.lower())

                        logger.info(f"[BulkApply] Email {email_id[:20]}... -> Category: '{ai_category}' -> Folder: '{folder_name}'")

                        if folder_name:
                            # Execute COM move operation in executor for thread safety
                            def _move_email():
                                return self.email_provider.move_email(email_id, folder_name)

                            move_success = await loop.run_in_executor(None, _move_email)

                            if move_success:
                                successful += 1
                                logger.info(f"[BulkApply] [OK] Successfully moved to {folder_name}")
                            else:
                                error_msg = f"Failed to move email {email_id} to {folder_name}"
                                errors.append(error_msg)
                                logger.error(f"[BulkApply] [FAIL] {error_msg}")
                                failed += 1
                        else:
                            # Category doesn't require folder move (stays in inbox)
                            logger.info(f"[BulkApply] Category '{ai_category}' has no folder mapping, skipping move")
                            successful += 1
                    else:
                        # Just classification without moving
                        successful += 1

                except Exception as e:
                    errors.append(f"Error processing email {email_id}: {str(e)}")
                    failed += 1

            result = {
                'success': failed == 0,
                'processed': len(email_ids),
                'successful': successful,
                'failed': failed,
                'errors': errors
            }

            logger.info(f"[BulkApply] Completed: {successful} successful, {failed} failed")
            return result

        except Exception as e:
            logger.error(f"[BulkApply] Critical failure: {e}")
            raise ClassificationError(f"Bulk apply failed: {str(e)}")

    async def update_email_classification(
        self,
        email_id: str,
        category: str,
        apply_to_outlook: bool = True
    ) -> Dict[str, Any]:
        """Update an email's classification in database and optionally Outlook.

        Args:
            email_id: Email ID to update
            category: New category for the email
            apply_to_outlook: Whether to move email to Outlook folder

        Returns:
            Dictionary with update results

        Raises:
            ClassificationError: If update fails
        """
        try:
            logger.info(f"[Update] Updating email {email_id[:20]}... to category '{category}'")

            # Update in database
            loop = asyncio.get_event_loop()

            def _update_category_sync():
                with db_manager.get_connection() as conn:
                    conn.execute(
                        "UPDATE emails SET category = ? WHERE id = ?",
                        (category, email_id)
                    )
                    conn.commit()

            await loop.run_in_executor(None, _update_category_sync)

            # Apply to Outlook if requested
            if apply_to_outlook:
                folder_name = self.all_categories.get(category.lower())

                if folder_name:
                    def _move_email():
                        return self.email_provider.move_email(email_id, folder_name)

                    move_success = await loop.run_in_executor(None, _move_email)

                    if not move_success:
                        logger.warning(f"[Update] Failed to move email to {folder_name}")

            return {
                'success': True,
                'email_id': email_id,
                'category': category
            }

        except Exception as e:
            logger.error(f"[Update] Failed to update email classification: {e}")
            raise ClassificationError(f"Update failed: {str(e)}")

    def get_category_mappings(self) -> List[Dict[str, Any]]:
        """Get list of available category to folder mappings.

        Returns:
            List of dictionaries with category info
        """
        mappings = []

        for category, folder in self.inbox_categories.items():
            mappings.append({
                'category': category,
                'folder': folder,
                'location': 'inbox'
            })

        for category, folder in self.non_inbox_categories.items():
            mappings.append({
                'category': category,
                'folder': folder,
                'location': 'non_inbox'
            })

        return mappings
