"""AI Services Package - Modular AI processing components.

This package provides focused AI services extracted from the original
monolithic AIProcessor for better maintainability and testability.
"""

from .context_manager import UserContextManager
from .classification_service import EmailClassificationService
from .extraction_service import EmailExtractionService
from .analysis_service import EmailAnalysisService

__all__ = [
    'UserContextManager',
    'EmailClassificationService',
    'EmailExtractionService',
    'EmailAnalysisService'
]
