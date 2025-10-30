"""Backend Core Business Logic Layer.

This package contains pure business logic for AI operations:
- AIOrchestrator: Main facade coordinating all AI operations
- PromptExecutor: Prompty template execution infrastructure
- UserContextManager: User-specific context and configuration
- ClassificationEngine: Email classification logic
- ExtractionEngine: Action item extraction and summarization
- AnalysisEngine: Deduplication and holistic analysis

All modules in this package are PURE BUSINESS LOGIC with:
- No async/await (synchronous operations)
- No FastAPI dependencies
- No framework-specific code
- Focused single responsibility

The orchestrator pattern provides a clean facade while maintaining
separation of concerns across specialized engines.
"""

from .ai_orchestrator import AIOrchestrator
from .prompt_executor import PromptExecutor
from .context_manager import UserContextManager
from .classification_engine import ClassificationEngine
from .extraction_engine import ExtractionEngine
from .analysis_engine import AnalysisEngine

__all__ = [
    'AIOrchestrator',
    'PromptExecutor',
    'UserContextManager',
    'ClassificationEngine',
    'ExtractionEngine',
    'AnalysisEngine',
]
