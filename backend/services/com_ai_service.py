"""COM AI Service Adapter for FastAPI Email Helper API.

This module provides a FastAPI-compatible adapter that wraps the AIOrchestrator
for COM-based integration. It delegates to specialized service modules for
different AI operations.

Migrated from src.ai_processor.AIProcessor to backend.core.business.AIOrchestrator
as part of Phase 2 consolidation (email_helper-164).

The COMAIService handles:
- Email classification using Azure OpenAI
- Action item extraction and analysis
- Email summarization for different types
- Duplicate detection across emails
- Batch email analysis for relationships
- Prompty template management

This adapter follows T1.2 requirements for Wave 1 foundation tasks.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

try:
    from backend.core.business import AIOrchestrator
    from backend.core.infrastructure.azure_config import get_azure_config
except ImportError as e:
    print(f"Warning: Could not import AI dependencies: {e}")
    AIOrchestrator = None
    get_azure_config = None

from backend.services.com_classification_service import COMClassificationService
from backend.services.com_action_extraction_service import COMActionExtractionService
from backend.services.com_summarization_service import COMSummarizationService
from backend.services.com_duplicate_detection_service import COMDuplicateDetectionService

logger = logging.getLogger(__name__)


class COMAIService:
    """COM AI service adapter for FastAPI integration.

    This service wraps the AIOrchestrator to provide async AI operations
    for COM-based email processing in the FastAPI backend.
    It delegates to specialized services for different operations.

    Attributes:
        ai_orchestrator (AIOrchestrator): Wrapped AI orchestrator instance
        azure_config: Azure OpenAI configuration
        _initialized (bool): Lazy initialization status flag
    """

    def __init__(self):
        """Initialize COM AI service with lazy loading."""
        self.ai_orchestrator = None
        self.azure_config = None
        self._initialized = False
        
        # Specialized service instances (lazy initialized)
        self._classification_service = None
        self._action_extraction_service = None
        self._summarization_service = None
        self._duplicate_detection_service = None

    def _ensure_initialized(self):
        """Lazy initialization of AI components.

        Raises:
            RuntimeError: If AI dependencies are not available or initialization fails
        """
        if not self._initialized:
            if AIOrchestrator is None or get_azure_config is None:
                raise RuntimeError("AI dependencies not available")

            try:
                self.azure_config = get_azure_config()
                self.ai_orchestrator = AIOrchestrator(self.azure_config)
                
                # Initialize specialized services
                self._classification_service = COMClassificationService(
                    self.ai_orchestrator, self.azure_config
                )
                self._action_extraction_service = COMActionExtractionService(
                    self.ai_orchestrator, self.azure_config
                )
                self._summarization_service = COMSummarizationService(
                    self.ai_orchestrator, self.azure_config
                )
                self._duplicate_detection_service = COMDuplicateDetectionService(
                    self.ai_orchestrator, self.azure_config
                )
                
                self._initialized = True
            except Exception as e:
                raise RuntimeError(f"Failed to initialize AI components: {e}")

    def invalidate_user_settings_cache(self):
        """Invalidate user settings cache in all services."""
        if self._classification_service:
            self._classification_service.invalidate_user_settings_cache()
        if self._action_extraction_service:
            self._action_extraction_service.invalidate_user_settings_cache()

    async def classify_email(
        self,
        email_content: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify an email and return structured results.

        Delegates to COMClassificationService.

        Args:
            email_content: Full email text including subject, sender, and body
            context: Optional additional context for classification

        Returns:
            Dictionary with classification results
        """
        self._ensure_initialized()
        return await self._classification_service.classify_email(email_content, context)

    async def extract_action_items(
        self,
        email_content: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract action items from email content.

        Delegates to COMActionExtractionService.

        Args:
            email_content: Full email text
            context: Optional additional context

        Returns:
            Dictionary with action item details
        """
        self._ensure_initialized()
        return await self._action_extraction_service.extract_action_items(email_content, context)

    async def generate_summary(
        self,
        email_content: str,
        summary_type: str = "brief"
    ) -> Dict[str, Any]:
        """Generate a summary of email content.

        Delegates to COMSummarizationService.

        Args:
            email_content: Full email text
            summary_type: Type of summary ("brief", "detailed", etc.)

        Returns:
            Dictionary with summary details
        """
        self._ensure_initialized()
        return await self._summarization_service.generate_summary(email_content, summary_type)

    async def detect_duplicates(
        self,
        emails: List[Dict[str, Any]]
    ) -> List[str]:
        """Detect duplicate emails in a list.

        Delegates to COMDuplicateDetectionService.

        Args:
            emails: List of email dictionaries with 'id', 'subject', 'content'

        Returns:
            List of email IDs that are duplicates
        """
        self._ensure_initialized()
        return await self._duplicate_detection_service.detect_duplicates(emails)

    async def deduplicate_content(
        self,
        content_items: List[Dict[str, Any]],
        content_type: str = "fyi"
    ) -> Dict[str, Any]:
        """Deduplicate similar content items using AI analysis.

        Delegates to COMDuplicateDetectionService.

        Args:
            content_items: List of content dictionaries
            content_type: Type of content being deduplicated

        Returns:
            Dictionary with deduplication results
        """
        self._ensure_initialized()
        return await self._duplicate_detection_service.deduplicate_content(
            content_items, content_type
        )

    def _requires_review(self, category: str, confidence: float) -> bool:
        """Determine if classification requires manual review.
        
        Delegates to classification service for backward compatibility with tests.
        
        Args:
            category: Classification category
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            True if manual review is required, False otherwise
        """
        self._ensure_initialized()
        return self._classification_service._requires_review(category, confidence)

    async def get_available_templates(self) -> Dict[str, Any]:
        """Get list of available prompty templates.

        Returns:
            Dictionary with template information
        """
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"

        if not prompts_dir.exists():
            return {
                "templates": [],
                "descriptions": {}
            }

        templates = []
        descriptions = {}

        for prompty_file in prompts_dir.glob("*.prompty"):
            templates.append(prompty_file.name)

            try:
                with open(prompty_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 2:
                            import re
                            desc_match = re.search(r'description:\s*(.+)', parts[1])
                            if desc_match:
                                descriptions[prompty_file.name] = desc_match.group(1).strip()
            except Exception:
                pass

        return {
            "templates": sorted(templates),
            "descriptions": descriptions
        }


def get_com_ai_service() -> COMAIService:
    """FastAPI dependency for COM AI service.

    Returns:
        COMAIService instance for dependency injection
    """
    return COMAIService()
