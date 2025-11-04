"""COM Email Classification Service.

Handles email classification using Azure OpenAI with user context and confidence scoring.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class COMClassificationService:
    """Service for classifying emails with AI.

    Provides email classification with confidence scoring, explanation,
    and review requirement determination.
    """

    def __init__(self, ai_processor, azure_config):
        """Initialize classification service.

        Args:
            ai_processor: AIProcessor instance for AI operations
            azure_config: Azure OpenAI configuration
        """
        self.ai_processor = ai_processor
        self.azure_config = azure_config

        # Performance optimization: Cache user settings
        self._user_settings_cache: Optional[Tuple[str, str, str]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=10)

    def _get_cached_user_settings(self) -> Tuple[str, str, str]:
        """Get user settings with caching for performance optimization.

        User settings (job_role_context, custom_interests, username) rarely change
        but are loaded on EVERY email processing operation. Caching reduces:
        - Database queries from 3-5 per email to once per 10 minutes
        - File I/O operations when database is unavailable
        - Processing latency per email by ~10-20ms

        Returns:
            Tuple of (job_role_context, custom_interests, username)
        """
        from pathlib import Path

        # Check if cache is valid
        now = datetime.now()
        if (self._user_settings_cache is not None and
            self._cache_timestamp is not None and
            now < self._cache_timestamp + self._cache_ttl):
            logger.debug("[Classification Service] Using cached user settings")
            return self._user_settings_cache

        # Cache miss - load from database/files
        logger.debug("[Classification Service] Loading user settings (cache miss)")

        job_role_context = ""
        custom_interests = ""
        username = ""

        try:
            # Try database first
            import sqlite3
            db_path = Path(__file__).parent.parent.parent / 'runtime_data' / 'database' / 'email_helper_history.db'

            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT username, job_context, newsletter_interests FROM user_settings WHERE user_id = 1")
                row = cursor.fetchone()
                conn.close()

                if row:
                    username = row[0] or ""
                    job_role_context = row[1] or ""
                    custom_interests = row[2] or ""
                    logger.debug(f"[Classification Service] Loaded settings from database: username={username[:20]}...")
        except Exception as e:
            logger.debug(f"[Classification Service] Database load failed, using file fallback: {e}")

        # Fall back to files if database didn't provide values
        try:
            user_data_path = Path(__file__).parent.parent.parent / 'user_specific_data'

            if not job_role_context and (user_data_path / 'job_role_context.md').exists():
                job_role_context = (user_data_path / 'job_role_context.md').read_text(encoding='utf-8')
                logger.debug("[Classification Service] Loaded job_role_context from file")

            if not custom_interests and (user_data_path / 'custom_interests.md').exists():
                custom_interests = (user_data_path / 'custom_interests.md').read_text(encoding='utf-8')
                logger.debug("[Classification Service] Loaded custom_interests from file")

            if not username and (user_data_path / 'username.txt').exists():
                username = (user_data_path / 'username.txt').read_text(encoding='utf-8').strip()
                logger.debug("[Classification Service] Loaded username from file")
        except Exception as e:
            logger.warning(f"[Classification Service] File fallback failed: {e}")

        # Update cache
        self._user_settings_cache = (job_role_context, custom_interests, username)
        self._cache_timestamp = now
        logger.info(f"[Classification Service] ✅ Cached user settings (TTL: {self._cache_ttl.total_seconds()}s)")

        return self._user_settings_cache

    def invalidate_user_settings_cache(self):
        """Invalidate user settings cache to force reload on next access."""
        self._user_settings_cache = None
        self._cache_timestamp = None
        logger.info("[Classification Service] User settings cache invalidated")

    async def classify_email(
        self,
        email_content: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify an email and return structured results.

        Args:
            email_content: Full email text including subject, sender, and body
            context: Optional additional context for classification

        Returns:
            Dictionary with classification results:
            - category (str): Primary classification category
            - confidence (float): Confidence score (0.0 to 1.0)
            - reasoning (str): Explanation of classification decision
            - alternatives (List): Alternative category suggestions
            - requires_review (bool): Whether manual review is needed
            - error (str, optional): Error message if classification failed
        """
        loop = asyncio.get_event_loop()

        try:
            result = await loop.run_in_executor(
                None,
                self._classify_email_sync,
                email_content,
                context or ""
            )
            return result
        except Exception as e:
            return {
                "category": "work_relevant",
                "confidence": 0.5,
                "reasoning": f"Classification failed: {str(e)}",
                "alternatives": [],
                "requires_review": True,
                "error": str(e)
            }

    def _classify_email_sync(self, email_content: str, context: str) -> Dict[str, Any]:
        """Synchronous email classification for thread pool execution."""
        try:
            # Parse email content into components
            lines = email_content.split('\n')
            subject = ""
            sender = ""
            body = email_content

            # Extract subject and sender from email text
            for i, line in enumerate(lines[:10]):
                if line.startswith('Subject:'):
                    subject = line.replace('Subject:', '').strip()
                elif line.startswith('From:'):
                    sender = line.replace('From:', '').strip()
                elif line.strip() == '' and (subject or sender):
                    body = '\n'.join(lines[i+1:])
                    break

            if not subject and not sender:
                body = email_content

            # Import pandas if available for DataFrame support
            try:
                import pandas as pd
                learning_data = pd.DataFrame()
            except ImportError:
                learning_data = []

            # Use cached user settings
            job_role_context, _, _ = self._get_cached_user_settings()

            # Create email_content dict for AIProcessor
            email_dict = {
                'subject': subject,
                'sender': sender,
                'body': body
            }

            # Use the enhanced classification method with explanation AND job context
            result = self.ai_processor.classify_email_with_explanation(
                email_content=email_dict,
                learning_data=learning_data,
                job_role_context=job_role_context
            )

            # Ensure result is in expected format
            if isinstance(result, dict):
                category = result.get('category', 'work_relevant')
                confidence = result.get('confidence')

                # Determine if review is required based on confidence thresholds
                requires_review = self._requires_review(category, confidence) if confidence is not None else True

                return {
                    'category': category,
                    'confidence': confidence,
                    'reasoning': result.get('explanation', 'Email classified'),
                    'alternatives': result.get('alternatives', []),
                    'requires_review': requires_review
                }
            else:
                category = str(result) if result else 'work_relevant'
                return {
                    'category': category,
                    'confidence': 0.8,
                    'reasoning': 'Email classified successfully',
                    'alternatives': [],
                    'requires_review': True
                }

        except Exception:
            raise

    def _requires_review(self, category: str, confidence: float) -> bool:
        """Determine if classification requires manual review.

        Args:
            category: Classification category
            confidence: Confidence score (0.0 to 1.0)

        Returns:
            True if manual review is required, False otherwise
        """
        if not hasattr(self.ai_processor, 'CONFIDENCE_THRESHOLDS'):
            return True

        threshold = self.ai_processor.CONFIDENCE_THRESHOLDS.get(category, 1.0)
        return confidence < threshold
