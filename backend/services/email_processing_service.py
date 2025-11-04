"""Email processing service for business logic operations.

This service coordinates between specialized email processing services,
providing a unified interface for the API layer. It delegates to:
- EmailSyncService: Database synchronization
- EmailClassificationService: AI classification and bulk operations  
- EmailTaskExtractionService: Task creation from emails
- EmailAccuracyService: Accuracy tracking

This follows the Single Responsibility Principle by delegating to
focused services rather than handling everything in one large class.
"""

import logging
from typing import Dict, Any, List, Optional

from backend.services.ai_service import AIService
from backend.services.email_provider import EmailProvider
from backend.services.task_service import TaskService
from backend.services.email_sync_service import EmailSyncService
from backend.services.email_classification_service import EmailClassificationService
from backend.services.email_task_extraction_service import EmailTaskExtractionService
from backend.services.email_accuracy_service import EmailAccuracyService


# Configure module logger
logger = logging.getLogger(__name__)


# Re-export exceptions for backward compatibility
class EmailProcessingError(Exception):
    """Base exception for email processing errors."""
    pass


class EmailNotFoundError(EmailProcessingError):
    """Raised when an email is not found."""
    pass


class DatabaseError(EmailProcessingError):
    """Raised when database operations fail."""
    pass


class AIProcessingError(EmailProcessingError):
    """Raised when AI processing fails."""
    pass


class RateLimitError(EmailProcessingError):
    """Raised when rate limits are exceeded."""
    pass


class ContentFilterError(EmailProcessingError):
    """Raised when content is blocked by filters."""
    pass


class EmailProcessingService:
    """Coordinating service for email processing operations.

    This service delegates to specialized services for different concerns:
    - sync_service: Database operations
    - classification_service: AI classification  
    - task_extraction_service: Task extraction
    - accuracy_service: Accuracy tracking
    """

    def __init__(
        self,
        ai_service: AIService,
        email_provider: EmailProvider,
        task_service: TaskService
    ):
        """Initialize the email processing coordinator.

        Args:
            ai_service: AI service for classification and analysis
            email_provider: Email provider for Outlook operations
            task_service: Task service for task management
        """
        # Initialize specialized services
        self.sync_service = EmailSyncService()
        self.classification_service = EmailClassificationService(ai_service, email_provider)
        self.task_extraction_service = EmailTaskExtractionService(
            ai_service, email_provider, task_service
        )
        self.accuracy_service = EmailAccuracyService()

        # Keep references for backward compatibility
        self.ai_service = ai_service
        self.email_provider = email_provider
        self.task_service = task_service

        logger.info("[EmailProcessing] Initialized with specialized services")

    # Database Operations - delegated to EmailSyncService

    async def get_emails_from_database(
        self,
        limit: int = 50000,
        offset: int = 0,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get emails from database with optional filtering.

        Delegates to EmailSyncService.
        """
        return await self.sync_service.get_emails_from_database(
            limit=limit,
            offset=offset,
            category=category,
            search=search
        )

    async def sync_emails_to_database(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync emails from Outlook to database.

        Delegates to EmailSyncService.
        """
        return await self.sync_service.sync_emails_to_database(emails)

    async def calculate_conversation_counts(
        self,
        conversation_ids: List[str]
    ) -> Dict[str, int]:
        """Calculate email counts per conversation.

        Delegates to EmailSyncService.
        """
        return await self.sync_service.calculate_conversation_counts(conversation_ids)

    # Classification Operations - delegated to EmailClassificationService

    async def analyze_holistically(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform holistic analysis across multiple emails.

        Delegates to EmailClassificationService.
        """
        return await self.classification_service.analyze_holistically(emails)

    async def bulk_apply_classifications(
        self,
        email_ids: List[str],
        apply_to_outlook: bool = True
    ) -> Dict[str, Any]:
        """Bulk apply AI classifications to Outlook folders.

        Delegates to EmailClassificationService.
        """
        return await self.classification_service.bulk_apply_classifications(
            email_ids=email_ids,
            apply_to_outlook=apply_to_outlook
        )

    async def update_email_classification(
        self,
        email_id: str,
        category: str,
        apply_to_outlook: bool = True
    ) -> Dict[str, Any]:
        """Update an email's classification.

        Delegates to EmailClassificationService.
        """
        return await self.classification_service.update_email_classification(
            email_id=email_id,
            category=category,
            apply_to_outlook=apply_to_outlook
        )

    def get_category_mappings(self) -> List[Dict[str, Any]]:
        """Get list of available category to folder mappings.

        Delegates to EmailClassificationService.
        """
        return self.classification_service.get_category_mappings()

    # Task Extraction Operations - delegated to EmailTaskExtractionService

    async def extract_tasks_from_emails(
        self,
        email_ids: List[str],
        user_id: int = 1
    ) -> Dict[str, Any]:
        """Extract tasks and summaries from emails.

        Delegates to EmailTaskExtractionService.
        """
        return await self.task_extraction_service.extract_tasks_from_emails(
            email_ids=email_ids,
            user_id=user_id
        )

    # Accuracy Tracking Operations - delegated to EmailAccuracyService

    async def get_accuracy_statistics(self) -> Dict[str, Any]:
        """Calculate AI classification accuracy statistics.

        Delegates to EmailAccuracyService.
        """
        return await self.accuracy_service.get_accuracy_statistics()


# Factory function for dependency injection
def get_email_processing_service() -> EmailProcessingService:
    """Factory function to get EmailProcessingService instance.

    Note: This is a placeholder. In production, this should be replaced
    with proper dependency injection that provides the required services.
    """
    # This will be replaced by proper DI container
    from backend.core.dependencies import get_ai_service, get_email_provider, get_task_service

    ai_service = get_ai_service()
    email_provider = get_email_provider()
    task_service = get_task_service()

    return EmailProcessingService(ai_service, email_provider, task_service)
