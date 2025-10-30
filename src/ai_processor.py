"""AI Processor for Email Helper - Refactored Facade.

This module provides a facade coordinating specialized AI services:
- UserContextManager: User context and configuration
- EmailClassificationService: Email categorization with confidence
- EmailExtractionService: Summaries and action item extraction
- EmailAnalysisService: Deduplication and holistic analysis

The AIProcessor maintains backward compatibility while delegating
to focused, single-responsibility service modules.
"""

import os
import json
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

from azure_config import get_azure_config
from utils import load_csv_or_empty
from analytics import AccuracyTracker, SessionTracker, DataRecorder

# Import refactored service modules
from ai.context_manager import UserContextManager
from ai.classification_service import EmailClassificationService
from ai.extraction_service import EmailExtractionService
from ai.analysis_service import EmailAnalysisService


class AIProcessor:
    """AI processing facade coordinating specialized services.
    
    This refactored class maintains backward compatibility while delegating
    to focused service modules. It serves as a thin coordination layer.
    
    Attributes:
        context_manager: Handles user context and configuration
        classification_service: Email classification with confidence
        extraction_service: Summaries and action extraction
        analysis_service: Deduplication and holistic analysis
    """
    
    # Expose confidence thresholds for backward compatibility
    CONFIDENCE_THRESHOLDS = EmailClassificationService.CONFIDENCE_THRESHOLDS
    
    def __init__(self, email_analyzer=None):
        """Initialize AI processor with service delegation."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.prompts_dir = os.path.join(project_root, 'prompts')
        user_data_dir = os.path.join(project_root, 'user_specific_data')
        runtime_data_dir = os.path.join(project_root, 'runtime_data', 'user_feedback')
        
        os.makedirs(runtime_data_dir, exist_ok=True)
        
        # Backward compatibility attributes
        self.user_data_dir = user_data_dir
        self.runtime_data_dir = runtime_data_dir
        self.user_feedback_dir = runtime_data_dir
        self.email_analyzer = email_analyzer
        self.learning_file = os.path.join(runtime_data_dir, 'ai_learning_feedback.csv')
        
        # Analytics
        runtime_base_dir = os.path.join(project_root, 'runtime_data')
        self.accuracy_tracker = AccuracyTracker(runtime_base_dir)
        self.session_tracker = SessionTracker(self.accuracy_tracker)
        self.data_recorder = DataRecorder(runtime_data_dir)
        
        # Service modules
        self.context_manager = UserContextManager(user_data_dir)
        self.classification_service = EmailClassificationService(self, self.context_manager)
        self.extraction_service = EmailExtractionService(self, self.context_manager)
        self.analysis_service = EmailAnalysisService(self, self.context_manager)
    
    # ========== Delegation Methods (Backward Compatibility) ==========
    
    def get_username(self):
        return self.context_manager.get_username()
    
    def get_available_categories(self):
        return EmailClassificationService.AVAILABLE_CATEGORIES
    
    def get_job_context(self):
        return self.context_manager.get_job_context()
    
    def get_job_skills(self):
        return self.context_manager.get_job_skills()
    
    def get_job_role_context(self):
        return self.context_manager.get_job_role_context()
    
    def get_standard_context(self) -> str:
        return self.context_manager.get_standard_context()
    
    def _create_email_inputs(self, email_content, context):
        return self.context_manager.create_email_inputs(email_content, context)
    
    def classify_email(self, email_content, learning_data):
        return self.classification_service.classify_email(email_content, learning_data)
    
    def classify_email_with_explanation(self, email_content, learning_data):
        return self.classification_service.classify_email_with_explanation(email_content, learning_data)
    
    def get_few_shot_examples(self, email_content, learning_data, max_examples=5):
        return self.classification_service._get_few_shot_examples(email_content, learning_data, max_examples)
    
    def apply_confidence_thresholds(self, classification_result, confidence_score=None):
        return self.classification_service.apply_confidence_thresholds(classification_result, confidence_score)
    
    def generate_explanation(self, email_content, category):
        return self.classification_service._generate_explanation(email_content, category)
    
    def extract_action_item_details(self, email_content, context=""):
        return self.extraction_service.extract_action_item_details(email_content, context)
    
    def generate_email_summary(self, email_content):
        return self.extraction_service.generate_email_summary(email_content)
    
    def generate_fyi_summary(self, email_content, context):
        return self.extraction_service.generate_fyi_summary(email_content, context)
    
    def generate_newsletter_summary(self, email_content, context):
        return self.extraction_service.generate_newsletter_summary(email_content, context)
    
    def assess_event_relevance(self, subject, body, context):
        return self.extraction_service.assess_event_relevance(subject, body, context)
    
    def advanced_deduplicate_action_items(self, action_items):
        return self.analysis_service.advanced_deduplicate_action_items(action_items)
    
    def check_optional_item_deadline(self, email_content, action_details=None):
        return self.analysis_service.check_optional_item_deadline(email_content, action_details)
    
    def detect_resolved_team_action(self, email_content, thread_context=""):
        return self.analysis_service.detect_resolved_team_action(email_content, thread_context)
    
    def analyze_inbox_holistically(self, all_email_data):
        return self.analysis_service.analyze_inbox_holistically(all_email_data)
    
    # ========== Analytics Methods ==========
    
    def load_learning_data(self):
        return load_csv_or_empty(self.learning_file)
    
    def save_learning_feedback(self, feedback_entries):
        self.data_recorder.record_learning_feedback(feedback_entries)
    
    def record_batch_processing(self, success_count, error_count, categories_used):
        self.data_recorder.record_batch_processing(success_count, error_count, categories_used)
        self.session_tracker.finalize_session(success_count, error_count, categories_used)
    
    def start_accuracy_session(self, total_emails):
        self.session_tracker.start_accuracy_session(total_emails)
    
    def record_suggestion_modification(self, email_data, old_category, new_category, user_explanation):
        self.data_recorder.record_suggestion_modification(email_data, old_category, new_category, user_explanation)
        self.session_tracker.add_modification(old_category, new_category)
    
    def record_accepted_suggestions(self, email_suggestions):
        self.data_recorder.record_accepted_suggestions(email_suggestions)
    
    def finalize_accuracy_session(self, success_count=None, error_count=None, categories_used=None):
        self.session_tracker.finalize_session(success_count, error_count, categories_used)
    
    # ========== Prompty Execution (Core Infrastructure) ==========
    
    def parse_prompty_file(self, file_path):
        """Parse prompty file - delegates to context_manager."""
        return self.context_manager._parse_prompty_file(file_path)
    
    def _repair_json_response(self, response_text):
        """Repair malformed JSON responses."""
        if not response_text or not response_text.strip():
            return None
        
        response_text = response_text.strip()
        
        try:
            json.loads(response_text)
            return response_text
        except json.JSONDecodeError:
            pass
        
        if not ('{' in response_text or '[' in response_text):
            return None
        
        repaired = response_text
        repaired = ''.join(char for char in repaired if ord(char) >= 32 or char in '\n\t\r')
        repaired = repaired.replace('\r\n', '\n').replace('\r', '\n')
        
        repaired = re.sub(
            r'"([^"]+)":\s*"([^"]*),\s*\n\s*"',
            lambda m: f'"{m.group(1)}": "{m.group(2)}",\n    "',
            repaired
        )
        
        open_braces = repaired.count('{')
        close_braces = repaired.count('}')
        open_brackets = repaired.count('[')
        close_brackets = repaired.count(']')
        
        if open_brackets > close_brackets:
            repaired += ']' * (open_brackets - close_brackets)
        if open_braces > close_braces:
            repaired += '}' * (open_braces - close_braces)
        
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            if 'truly_relevant_actions' in repaired:
                minimal = {
                    "truly_relevant_actions": [],
                    "superseded_actions": [],
                    "duplicate_groups": [],
                    "expired_items": []
                }
                return json.dumps(minimal)
            return None
    
    def execute_prompty(self, prompty_file, inputs=None):
        """Execute prompty template with fallback handling."""
        if inputs is None:
            inputs = {}
        
        prompty_path = os.path.join(self.prompts_dir, prompty_file)
        azure_config = get_azure_config()
        
        logger.debug(f"[AI] Executing {prompty_file}")
        
        try:
            from promptflow.core import Prompty
            model_config = azure_config.get_promptflow_config()
            prompty_instance = Prompty.load(prompty_path, model={'configuration': model_config})
            result = prompty_instance(**inputs)
            logger.info(f"[AI] OK {prompty_file}")
            return result
            
        except ImportError:
            try:
                import prompty
                import prompty.azure
                
                p = prompty.load(prompty_path)
                p.model.configuration["azure_endpoint"] = azure_config.endpoint
                p.model.configuration["azure_deployment"] = azure_config.deployment  
                p.model.configuration["api_version"] = azure_config.api_version
                
                json_required_prompts = [
                    'summerize_action_item', 'email_classifier', 'holistic_inbox_analyzer',
                    'action_item_deduplication', 'content_deduplication', 'email_duplicate_detection',
                    'event_relevance_assessment'
                ]
                if any(prompt_name in prompty_file for prompt_name in json_required_prompts):
                    if not hasattr(p.model, 'parameters'):
                        p.model.parameters = {}
                    p.model.parameters["response_format"] = {"type": "json_object"}
                
                if azure_config.use_azure_credential():
                    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
                    token_provider = get_bearer_token_provider(
                        DefaultAzureCredential(), 
                        "https://cognitiveservices.azure.com/.default"
                    )
                    p.model.configuration["azure_ad_token_provider"] = token_provider
                    if "api_key" in p.model.configuration:
                        del p.model.configuration["api_key"]
                else:
                    p.model.configuration["api_key"] = azure_config.get_api_key()
                
                result = prompty.run(p, inputs=inputs)
                return result
                
            except ImportError as e:
                logger.error(f"[AI] Prompty library unavailable: {e}")
                raise RuntimeError(f"Prompty library unavailable: {e}")
                
        except Exception as e:
            error_str = str(e).lower()
            is_content_filter = any(phrase in error_str for phrase in [
                'content_filter', 'content management policy', 'responsibleaipolicyviolation',
                'jailbreak', 'filtered', 'badrequeesterror'
            ])
            
            if is_content_filter or 'wrappedopenaierror' in type(e).__name__.lower():
                logger.warning(f"[AI] Content filter blocked {prompty_file}")
                return self._get_content_filter_fallback(prompty_file, inputs)
            else:
                logger.error(f"[AI] Execution failed {prompty_file}: {str(e)[:200]}")
                return self._get_execution_error_fallback(prompty_file, inputs)
    
    def _get_content_filter_fallback(self, prompty_file, inputs):
        """Fallback response when content filter triggers."""
        if 'email_one_line_summary' in prompty_file:
            subject = inputs.get('subject', 'Email')
            return f"Summary blocked by content filter - {subject[:80]}"
        elif 'event_relevance_assessment' in prompty_file:
            return "Unable to assess relevance - content filter triggered"
        elif 'email_classifier' in prompty_file:
            return '{"category": "fyi", "explanation": "Classification blocked by content filter"}'
        elif 'fyi_summary' in prompty_file:
            subject = inputs.get('subject', 'Email')
            return f"• Summary blocked by content filter - {subject[:80]}"
        elif 'newsletter_summary' in prompty_file:
            return "Newsletter summary blocked by content filter"
        elif 'summerize_action_item' in prompty_file:
            return '{"action_required": "Review email manually", "due_date": "No deadline", "explanation": "Content filter blocked analysis", "relevance": "Manual review needed", "links": []}'
        elif 'holistic_inbox_analyzer' in prompty_file:
            return '{"truly_relevant_actions": [], "superseded_actions": [], "duplicate_groups": [], "expired_items": []}'
        else:
            return "Content filter blocked - manual review required"
    
    def _get_execution_error_fallback(self, prompty_file, inputs):
        """Fallback response when AI execution fails."""
        if 'email_one_line_summary' in prompty_file:
            subject = inputs.get('subject', 'Email')
            return f"AI unavailable - {subject[:80]}"
        elif 'event_relevance_assessment' in prompty_file:
            return "Unable to assess relevance - AI service unavailable"
        elif 'email_classifier' in prompty_file:
            return '{"category": "fyi", "explanation": "AI service unavailable for classification"}'
        elif 'fyi_summary' in prompty_file:
            subject = inputs.get('subject', 'Email')
            return f"• AI unavailable - {subject[:80]}"
        elif 'newsletter_summary' in prompty_file:
            return "Newsletter summary unavailable - AI service error"
        elif 'summerize_action_item' in prompty_file:
            return '{"action_required": "Review email manually", "due_date": "No deadline", "explanation": "AI service unavailable", "relevance": "Manual review needed", "links": []}'
        elif 'holistic_inbox_analyzer' in prompty_file:
            return '{"truly_relevant_actions": [], "superseded_actions": [], "duplicate_groups": [], "expired_items": []}'
        else:
            return "AI processing unavailable"
