"""Email task extraction service for creating tasks from emails.

This service handles extracting tasks from emails based on their category,
including action items, job listings, events, and summaries.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from backend.database.connection import db_manager
from backend.models.task import TaskCreate, TaskPriority, TaskStatus
from backend.services.ai_service import AIService
from backend.services.email_provider import EmailProvider
from backend.services.task_service import TaskService
from backend.core.rate_limiter import get_rate_limiter


# Configure module logger
logger = logging.getLogger(__name__)


class TaskExtractionError(Exception):
    """Base exception for task extraction errors."""
    pass


class EmailTaskExtractionService:
    """Service for extracting tasks from emails."""

    def __init__(
        self,
        ai_service: AIService,
        email_provider: EmailProvider,
        task_service: TaskService
    ):
        """Initialize the task extraction service.

        Args:
            ai_service: AI service for task extraction
            email_provider: Email provider for fetching email content
            task_service: Task service for creating tasks
        """
        self.ai_service = ai_service
        self.email_provider = email_provider
        self.task_service = task_service
        self.rate_limiter = get_rate_limiter()

        self.actionable_categories = ['required_personal_action', 'team_action', 'optional_action']
        self.job_categories = ['job_listing']
        self.event_categories = ['optional_event']
        self.summary_categories = ['fyi', 'newsletter']

    async def extract_tasks_from_emails(
        self,
        email_ids: List[str],
        user_id: int = 1
    ) -> Dict[str, Any]:
        """Extract tasks and summaries from emails with rate limiting.

        Args:
            email_ids: List of email IDs to process
            user_id: User ID for task ownership

        Returns:
            Dictionary with processing results and statistics

        Raises:
            TaskExtractionError: If processing fails
        """
        if not email_ids:
            return {
                'status': 'completed',
                'tasks_created': 0,
                'summaries_created': 0,
                'errors': [],
                'processed_count': 0
            }

        try:
            logger.info(f"[TaskExtract] Starting task extraction for {len(email_ids)} emails")

            tasks_created = 0
            summaries_created = 0
            errors = []
            processed_count = 0

            # Fetch email bodies and cache them
            email_body_cache = await self._fetch_email_bodies(email_ids)

            # Process each email individually
            for email_id in email_ids:
                try:
                    # Get email from database
                    email = await self._get_email_from_database(email_id)
                    if not email:
                        logger.warning(f"[TaskExtract] Email {email_id[:30]}... not found in database")
                        continue

                    ai_category = email.get('ai_category', '').lower()

                    # Process based on category
                    result = await self._process_email_by_category(
                        email, ai_category, user_id, email_body_cache
                    )

                    if result.get('task_created'):
                        tasks_created += 1
                    if result.get('summary_created'):
                        summaries_created += 1
                    if result.get('error'):
                        errors.append(result['error'])

                    processed_count += 1

                except Exception as e:
                    error_msg = self._diagnose_processing_error(e, email_id)
                    errors.append(error_msg)
                    logger.error(f"[TaskExtract] {error_msg}")
                    continue

            result = {
                'status': 'completed',
                'tasks_created': tasks_created,
                'summaries_created': summaries_created,
                'errors': errors,
                'processed_count': processed_count,
                'total_requested': len(email_ids)
            }

            logger.info(f"[TaskExtract] Completed: {tasks_created} tasks, "
                       f"{summaries_created} summaries, {len(errors)} errors")

            return result

        except Exception as e:
            logger.error(f"[TaskExtract] Critical failure: {e}", exc_info=True)
            raise TaskExtractionError(f"Task extraction failed: {str(e)}")

    async def _fetch_email_bodies(self, email_ids: List[str]) -> Dict[str, str]:
        """Fetch email bodies from Outlook and cache them.

        Args:
            email_ids: List of email IDs to fetch

        Returns:
            Dictionary mapping email IDs to bodies
        """
        loop = asyncio.get_event_loop()

        def _fetch_all_bodies():
            """Fetch all email bodies in one COM thread context."""
            bodies = {}
            for email_id in email_ids:
                try:
                    body = self.email_provider.adapter.get_email_body(email_id)
                    bodies[email_id] = body or ''
                except Exception as e:
                    logger.warning(f"[TaskExtract] Could not fetch body for {email_id[:30]}...: {e}")
                    bodies[email_id] = ''
            return bodies

        return await loop.run_in_executor(None, _fetch_all_bodies)

    async def _get_email_from_database(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get email metadata from database by ID."""
        loop = asyncio.get_event_loop()

        def _get_email_sync():
            with db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, subject, sender, ai_category, conversation_id FROM emails WHERE id = ?",
                    (email_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None

        return await loop.run_in_executor(None, _get_email_sync)

    async def _process_email_by_category(
        self,
        email: Dict[str, Any],
        ai_category: str,
        user_id: int,
        body_cache: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Process email based on its AI category."""
        if ai_category in self.actionable_categories:
            return await self._create_action_task(email, ai_category, user_id, body_cache)
        elif ai_category in self.job_categories:
            return await self._create_job_task(email, user_id, body_cache)
        elif ai_category in self.event_categories:
            return await self._create_event_task(email, user_id, body_cache)
        elif ai_category in self.summary_categories:
            return await self._create_summary_task(email, ai_category, user_id, body_cache)

        logger.info(f"[TaskExtract] [SKIP] No processing needed for category '{ai_category}': {email.get('id', '')[:30]}...")
        return {'task_created': False, 'summary_created': False}

    async def _create_action_task(
        self,
        email: Dict[str, Any],
        ai_category: str,
        user_id: int,
        body_cache: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Create task from actionable email."""
        try:
            email_id = email.get('id')
            body = body_cache.get(email_id, '') if body_cache else ''

            # Extract action items using AI
            await self.rate_limiter.ai_request_delay()

            email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{body}"
            action_result = await self.ai_service.extract_action_items(
                email_content=email_text
            )

            action_items = action_result.get('action_items', [])

            if not action_items or self._is_fallback_response(action_text=email_text, action_result=action_result):
                logger.info(f"[ActionTask] No valid action items found for {email_id[:30]}...")
                return {'task_created': False}

            # Create task from first action item
            action = action_items[0]

            task_data = TaskCreate(
                title=action.get('title', email.get('subject', 'Untitled Task')),
                description=action.get('description', ''),
                due_date=self._parse_due_date(action.get('due_date')),
                priority=self._map_priority(action.get('priority', 'medium')),
                status=TaskStatus.TODO,
                category=ai_category,
                source_email_id=email_id,
                user_id=user_id
            )

            await self.task_service.create_task(task_data)
            logger.info(f"[ActionTask] Created task for email {email_id[:30]}...")

            return {'task_created': True}

        except Exception as e:
            error_msg = f"Failed to create action task: {str(e)}"
            logger.error(f"[ActionTask] {error_msg}")
            return {'task_created': False, 'error': error_msg}

    async def _create_job_task(
        self,
        email: Dict[str, Any],
        user_id: int,
        body_cache: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Create task from job listing email."""
        try:
            email_id = email.get('id')

            task_data = TaskCreate(
                title=f"Job: {email.get('subject', 'Job Opportunity')}",
                description=f"From: {email.get('sender', '')}\n\nCheck email for details.",
                due_date=datetime.now() + timedelta(days=30),
                priority=TaskPriority.LOW,
                status=TaskStatus.TODO,
                category='job_listing',
                source_email_id=email_id,
                user_id=user_id
            )

            await self.task_service.create_task(task_data)
            logger.info(f"[JobTask] Created job task for email {email_id[:30]}...")

            return {'task_created': True}

        except Exception as e:
            error_msg = f"Failed to create job task: {str(e)}"
            logger.error(f"[JobTask] {error_msg}")
            return {'task_created': False, 'error': error_msg}

    async def _create_event_task(
        self,
        email: Dict[str, Any],
        user_id: int,
        body_cache: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Create task from event email."""
        try:
            email_id = email.get('id')

            task_data = TaskCreate(
                title=f"Event: {email.get('subject', 'Event')}",
                description=f"From: {email.get('sender', '')}\n\nCheck email for event details.",
                due_date=datetime.now() + timedelta(days=7),
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.TODO,
                category='optional_event',
                source_email_id=email_id,
                user_id=user_id
            )

            await self.task_service.create_task(task_data)
            logger.info(f"[EventTask] Created event task for email {email_id[:30]}...")

            return {'task_created': True}

        except Exception as e:
            error_msg = f"Failed to create event task: {str(e)}"
            logger.error(f"[EventTask] {error_msg}")
            return {'task_created': False, 'error': error_msg}

    async def _create_summary_task(
        self,
        email: Dict[str, Any],
        ai_category: str,
        user_id: int,
        body_cache: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Create summary task for FYI/newsletter email."""
        try:
            email_id = email.get('id')
            body = body_cache.get(email_id, '') if body_cache else ''

            # Generate summary using AI
            await self.rate_limiter.ai_request_delay()

            email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{body}"
            summary_result = await self.ai_service.generate_summary(
                email_content=email_text
            )

            summary = summary_result.get('summary', 'See email for details')

            task_data = TaskCreate(
                title=f"Summary: {email.get('subject', 'Email Summary')}",
                description=summary,
                due_date=None,
                priority=TaskPriority.LOW,
                status=TaskStatus.TODO,
                category=ai_category,
                source_email_id=email_id,
                user_id=user_id
            )

            await self.task_service.create_task(task_data)
            logger.info(f"[SummaryTask] Created summary for email {email_id[:30]}...")

            return {'summary_created': True}

        except Exception as e:
            error_msg = f"Failed to create summary: {str(e)}"
            logger.error(f"[SummaryTask] {error_msg}")
            return {'summary_created': False, 'error': error_msg}

    def _is_fallback_response(self, action_text: str, action_result: Dict[str, Any]) -> bool:
        """Check if AI response is a fallback/error response."""
        action_items = action_result.get('action_items', [])
        if not action_items:
            return True

        first_action = action_items[0]
        title = first_action.get('title', '').lower()
        description = first_action.get('description', '').lower()

        fallback_indicators = [
            'no action needed',
            'no specific action',
            'review email',
            'read email',
            'no clear action'
        ]

        for indicator in fallback_indicators:
            if indicator in title or indicator in description:
                return True

        return False

    def _parse_due_date(self, due_date_str: Optional[str]) -> Optional[datetime]:
        """Parse due date string to datetime."""
        if not due_date_str:
            return None

        try:
            # Try ISO format first
            return datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        except:
            pass

        try:
            # Try common date formats
            from dateutil import parser
            return parser.parse(due_date_str)
        except:
            logger.warning(f"[TaskExtract] Could not parse due date: {due_date_str}")
            return None

    def _map_priority(self, priority_str: str) -> TaskPriority:
        """Map priority string to TaskPriority enum."""
        priority_map = {
            'high': TaskPriority.HIGH,
            'medium': TaskPriority.MEDIUM,
            'low': TaskPriority.LOW
        }
        return priority_map.get(priority_str.lower(), TaskPriority.MEDIUM)

    def _diagnose_processing_error(self, error: Exception, email_id: str) -> str:
        """Diagnose processing error and return descriptive message."""
        error_msg = str(error).lower()

        if 'content_filter' in error_msg or 'responsibleaipolicyviolation' in error_msg:
            return f"[FILTER] Email {email_id[:30]}... blocked by content policy"
        elif 'rate' in error_msg or 'quota' in error_msg or '429' in error_msg:
            return f"[RATE] Rate limit hit processing {email_id[:30]}..."
        elif 'timeout' in error_msg:
            return f"[TIMEOUT] Processing timeout for {email_id[:30]}..."
        else:
            return f"Error processing {email_id[:30]}...: {str(error)}"
