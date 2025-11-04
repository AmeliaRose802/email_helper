"""AI Orchestrator - Main coordination facade for AI operations.

This module provides a facade coordinating specialized AI engines:
- PromptExecutor: Prompty template execution
- UserContextManager: User context and configuration  
- ClassificationEngine: Email categorization with confidence
- ExtractionEngine: Summaries and action item extraction
- AnalysisEngine: Deduplication and holistic analysis

The AIOrchestrator maintains backward compatibility while delegating
to focused, single-responsibility engine modules.

This is PURE BUSINESS LOGIC - no async, no FastAPI, no framework dependencies.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any

from backend.core.infrastructure.data_utils import load_csv_or_empty
from backend.core.infrastructure.analytics.accuracy_tracker import AccuracyTracker
from backend.core.infrastructure.analytics.session_tracker import SessionTracker
from backend.core.infrastructure.analytics.data_recorder import DataRecorder

from .prompt_executor import PromptExecutor
from .context_manager import UserContextManager
from .classification_engine import ClassificationEngine
from .extraction_engine import ExtractionEngine
from .analysis_engine import AnalysisEngine

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """AI processing orchestrator coordinating specialized engines.

    This refactored class maintains backward compatibility while delegating
    to focused engine modules. It serves as a thin coordination layer.

    Pure business logic - no async, no FastAPI dependencies.

    Attributes:
        prompt_executor: Handles prompty template execution
        context_manager: Manages user context and configuration
        classification_engine: Email classification with confidence
        extraction_engine: Summaries and action extraction
        analysis_engine: Deduplication and holistic analysis
    """

    # Expose confidence thresholds for backward compatibility
    CONFIDENCE_THRESHOLDS = ClassificationEngine.CONFIDENCE_THRESHOLDS
    AVAILABLE_CATEGORIES = ClassificationEngine.AVAILABLE_CATEGORIES

    def __init__(self, azure_config, prompts_dir: Optional[str] = None,
                 user_data_dir: Optional[str] = None, runtime_data_dir: Optional[str] = None):
        """Initialize AI orchestrator with engine delegation.

        Args:
            azure_config: Azure OpenAI configuration object
            prompts_dir: Optional path to prompts directory
            user_data_dir: Optional path to user-specific data
            runtime_data_dir: Optional path to runtime data directory
        """
        # Determine directories
        if prompts_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
            prompts_dir = os.path.join(project_root, 'prompts')

        if user_data_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))))
            user_data_dir = os.path.join(project_root, 'user_specific_data')

        if runtime_data_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))))
            runtime_data_dir = os.path.join(project_root, 'runtime_data', 'user_feedback')

        os.makedirs(runtime_data_dir, exist_ok=True)

        self.prompts_dir = prompts_dir
        self.user_data_dir = user_data_dir
        self.runtime_data_dir = runtime_data_dir
        self.learning_file = os.path.join(runtime_data_dir, 'ai_learning_feedback.csv')

        # Analytics
        runtime_base_dir = os.path.dirname(runtime_data_dir)
        self.accuracy_tracker = AccuracyTracker(runtime_base_dir)
        self.session_tracker = SessionTracker(self.accuracy_tracker)
        self.data_recorder = DataRecorder(runtime_data_dir)

        # Initialize engines
        self.prompt_executor = PromptExecutor(prompts_dir, azure_config)
        self.context_manager = UserContextManager(user_data_dir)
        self.classification_engine = ClassificationEngine(self.prompt_executor, self.context_manager)
        self.extraction_engine = ExtractionEngine(self.prompt_executor, self.context_manager)
        self.analysis_engine = AnalysisEngine(self.prompt_executor, self.context_manager)

    # ========== Context & Configuration Methods ==========

    def get_username(self) -> str:
        """Get configured username."""
        return self.context_manager.get_username()

    def get_available_categories(self) -> List[str]:
        """Get list of available email categories."""
        return self.AVAILABLE_CATEGORIES

    def get_job_context(self) -> str:
        """Get user's job context."""
        return self.context_manager.get_job_context()

    def get_job_skills(self) -> str:
        """Get user's skills profile."""
        return self.context_manager.get_job_skills()

    def get_job_role_context(self) -> str:
        """Get user's detailed role context."""
        return self.context_manager.get_job_role_context()

    def get_standard_context(self) -> str:
        """Get combined standard context for AI prompts."""
        return self.context_manager.get_standard_context()

    def _create_email_inputs(self, email_content: dict, context: str) -> dict:
        """Create standardized input dict for email processing prompts."""
        return self.context_manager.create_email_inputs(email_content, context)

    # ========== Classification Methods ==========

    def classify_email(self, email_content: dict, learning_data) -> str:
        """Classify email returning only category.

        Args:
            email_content: Dict with email data
            learning_data: DataFrame of historical decisions

        Returns:
            str: Category name
        """
        return self.classification_engine.classify_email(email_content, learning_data)

    def classify_email_with_explanation(
        self,
        email_content: dict,
        learning_data,
        job_role_context: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        """Classify email and provide detailed explanation.

        Args:
            email_content: Dict with email data
            learning_data: DataFrame of historical classification decisions
            job_role_context: Optional explicit role context override
            **kwargs: Additional legacy keyword arguments

        Returns:
            dict: {'category': str, 'explanation': str}
        """
        return self.classification_engine.classify_email_with_explanation(
            email_content,
            learning_data,
            job_role_context=job_role_context,
            **kwargs,
        )

    def get_few_shot_examples(self, email_content: dict, learning_data, max_examples: int = 5) -> List[Dict]:
        """Get relevant few-shot examples from learning data."""
        return self.classification_engine._get_few_shot_examples(email_content, learning_data, max_examples)

    def apply_confidence_thresholds(self, classification_result: Dict, confidence_score: Optional[float] = None) -> Dict:
        """Apply asymmetric confidence thresholds for auto-approval."""
        return self.classification_engine.apply_confidence_thresholds(classification_result, confidence_score)

    def generate_explanation(self, email_content: dict, category: str) -> str:
        """Generate fallback explanation when AI fails."""
        return self.classification_engine._generate_explanation(email_content, category)

    # ========== Extraction Methods ==========

    def extract_action_item_details(self, email_content: dict, context: str = "") -> Dict:
        """Extract structured action item details from email."""
        return self.extraction_engine.extract_action_item_details(email_content, context)

    def generate_email_summary(self, email_content: dict) -> str:
        """Generate concise one-line email summary."""
        return self.extraction_engine.generate_email_summary(email_content)

    def generate_fyi_summary(self, email_content: dict, context: str) -> str:
        """Generate FYI-specific summary with bullet point."""
        return self.extraction_engine.generate_fyi_summary(email_content, context)

    def generate_newsletter_summary(self, email_content: dict, context: str) -> str:
        """Generate newsletter-specific summary."""
        return self.extraction_engine.generate_newsletter_summary(email_content, context)

    def assess_event_relevance(self, subject: str, body: str, context: str) -> str:
        """Assess relevance of event invitation."""
        return self.extraction_engine.assess_event_relevance(subject, body, context)

    # ========== Analysis Methods ==========

    def advanced_deduplicate_action_items(self, action_items: List[Dict]) -> List[Dict]:
        """Use AI to intelligently deduplicate action items."""
        return self.analysis_engine.advanced_deduplicate_action_items(action_items)

    def check_optional_item_deadline(self, email_content: dict, action_details: Optional[Dict] = None) -> Tuple[bool, str]:
        """Check if optional item's deadline has passed."""
        return self.analysis_engine.check_optional_item_deadline(email_content, action_details)

    def detect_resolved_team_action(self, email_content: dict, thread_context: str = "") -> Tuple[bool, str]:
        """Detect if team action already handled by someone else."""
        return self.analysis_engine.detect_resolved_team_action(email_content, thread_context)

    def analyze_inbox_holistically(self, all_email_data: List[Dict]) -> Tuple[Optional[Dict], str]:
        """Analyze entire inbox to identify truly relevant actions and relationships."""
        return self.analysis_engine.analyze_inbox_holistically(all_email_data)

    # ========== Analytics Methods ==========

    def load_learning_data(self):
        """Load historical learning data from CSV."""
        return load_csv_or_empty(self.learning_file)

    def save_learning_feedback(self, feedback_entries):
        """Save learning feedback entries."""
        self.data_recorder.record_learning_feedback(feedback_entries)

    def record_batch_processing(self, success_count: int, error_count: int, categories_used: Dict):
        """Record batch processing statistics."""
        self.data_recorder.record_batch_processing(success_count, error_count, categories_used)
        self.session_tracker.finalize_session(success_count, error_count, categories_used)

    def start_accuracy_session(self, total_emails: int):
        """Start accuracy tracking session."""
        self.session_tracker.start_accuracy_session(total_emails)

    def record_suggestion_modification(self, email_data: dict, old_category: str, new_category: str, user_explanation: str):
        """Record user modification of AI suggestion."""
        self.data_recorder.record_suggestion_modification(email_data, old_category, new_category, user_explanation)
        self.session_tracker.add_modification(old_category, new_category)

    def record_accepted_suggestions(self, email_suggestions: List[Dict]):
        """Record accepted AI suggestions."""
        self.data_recorder.record_accepted_suggestions(email_suggestions)

    def finalize_accuracy_session(self, success_count: Optional[int] = None, error_count: Optional[int] = None,
                                   categories_used: Optional[Dict] = None):
        """Finalize accuracy tracking session."""
        self.session_tracker.finalize_session(success_count, error_count, categories_used)

    # ========== Prompty Execution (Core Infrastructure) ==========

    def parse_prompty_file(self, file_path: str) -> str:
        """Parse prompty file content."""
        return self.prompt_executor.parse_prompty_file(file_path)

    def _repair_json_response(self, response_text: str) -> Optional[str]:
        """Repair malformed JSON responses."""
        return self.prompt_executor.repair_json_response(response_text)

    def execute_prompty(self, prompty_file: str, inputs: Optional[Dict[str, Any]] = None) -> Any:
        """Execute prompty template with fallback handling."""
        return self.prompt_executor.execute_prompty(prompty_file, inputs)
