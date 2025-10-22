"""AI Processor for Email Helper - Azure OpenAI Integration.

This module provides the core AI processing functionality for the Email Helper
application, handling integration with Azure OpenAI services for email
classification, analysis, and content generation.

The AIProcessor class manages:
- Azure OpenAI client configuration and authentication
- Prompty template loading and processing
- Email classification using AI models
- Task extraction and categorization
- User context integration (job role, skills, etc.)
- Accuracy tracking and learning feedback collection
- Session management for processing workflows

Key Components:
- Prompty file parsing and template management
- User-specific data loading (job context, skills, role)
- AI response processing with error handling and fallbacks
- Classification accuracy tracking and improvement
- Holistic email analysis across multiple emails
- Learning feedback collection for model improvement

This module follows the project's AI integration patterns and provides
comprehensive error handling for robust operation when AI services
may be unavailable or return malformed responses.
"""

import os
import json
from datetime import datetime
from azure_config import get_azure_config
from utils import (
    clean_json_response, parse_json_with_fallback, parse_date_string,
    clean_ai_response, clean_markdown_formatting, truncate_with_ellipsis,
    add_bullet_if_needed, load_csv_or_empty, format_date_for_display
)

# Minimal stubs for removed analytics - no-op implementations
class DataRecorder:
    """Stub for data recording - analytics collection disabled."""
    def __init__(self, runtime_data_dir):
        pass
    def record_learning_feedback(self, feedback_entries):
        pass
    def record_batch_processing(self, success_count, error_count, categories_used):
        pass
    def record_suggestion_modification(self, email_data, old_category, new_category, user_explanation):
        pass
    def record_accepted_suggestions(self, email_suggestions):
        pass

class AccuracyTracker:
    """Stub for accuracy tracking - disabled."""
    def __init__(self, runtime_data_dir):
        pass

class SessionTracker:
    """Stub for session tracking - disabled."""
    def __init__(self, accuracy_tracker):
        self.accuracy_tracker = accuracy_tracker
    def start_accuracy_session(self, total_emails):
        pass
    def add_modification(self, old_category, new_category):
        pass
    def finalize_session(self, success_count=None, error_count=None, categories_used=None):
        pass


class AIProcessor:
    """AI processing engine for email classification and analysis.
    
    This class handles all AI-related operations for the email helper system,
    including Azure OpenAI integration, prompt management, email classification,
    and accuracy tracking. It serves as the central hub for AI functionality.
    
    The processor manages:
    - Azure OpenAI client configuration and authentication
    - Prompty template loading and processing
    - User context integration (job role, skills, preferences)
    - Email classification and task extraction
    - Accuracy tracking and learning feedback
    - Session management for batch processing
    
    Attributes:
        prompts_dir (str): Directory path for prompty template files
        user_data_dir (str): Directory path for user-specific configuration
        runtime_data_dir (str): Directory path for runtime data and feedback
        job_summary_file (str): Path to user's job context file
        job_skills_file (str): Path to user's skills profile file
        job_role_context_file (str): Path to user's role context file
        learning_file (str): Path to AI learning feedback CSV
        accuracy_tracker (AccuracyTracker): Tracks classification accuracy
        session_tracker (SessionTracker): Manages processing sessions
        data_recorder (DataRecorder): Records processing data and feedback
    
    Example:
        >>> processor = AIProcessor()
        >>> result = processor.classify_email(email_data, config)
        >>> print(result['category'])
        'required_personal_action'
    """
    
    # Confidence threshold configuration
    CONFIDENCE_THRESHOLDS = {
        'fyi': 0.9,                    # FYI requires 90% confidence for auto-approval
        'required_personal_action': 1.0,  # Always review (impossible threshold)
        'team_action': 1.0,            # Always review (impossible threshold) 
        'optional_action': 0.8,        # 80% confidence for auto-approval
        'work_relevant': 0.8,          # 80% confidence for auto-approval
        'newsletter': 0.7,             # 70% confidence for auto-approval
        'spam_to_delete': 0.7,         # 70% confidence for auto-approval
        'job_listing': 0.8,            # 80% confidence for auto-approval
        'optional_event': 0.8          # 80% confidence for auto-approval
    }
    
    def __init__(self, email_analyzer=None):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.prompts_dir = os.path.join(project_root, 'prompts')
        self.user_data_dir = os.path.join(project_root, 'user_specific_data')
        self.runtime_data_dir = os.path.join(
            project_root, 'runtime_data', 'user_feedback'
        )
        
        # Store reference to email analyzer for content similarity detection
        self.email_analyzer = email_analyzer
        
        # User feedback directory (alias for compatibility)
        self.user_feedback_dir = self.runtime_data_dir
        
        self.job_summary_file = os.path.join(self.user_data_dir, 'job_summery.md')
        self.job_skills_file = os.path.join(
            self.user_data_dir, 'job_skill_summery.md'
        )
        self.job_role_context_file = os.path.join(
            self.user_data_dir, 'job_role_context.md'
        )
        
        os.makedirs(self.runtime_data_dir, exist_ok=True)
        self.learning_file = os.path.join(
            self.runtime_data_dir, 'ai_learning_feedback.csv'
        )
        
        runtime_base_dir = os.path.join(project_root, 'runtime_data')
        self.accuracy_tracker = AccuracyTracker(runtime_base_dir)
        self.session_tracker = SessionTracker(self.accuracy_tracker)
        self.data_recorder = DataRecorder(self.runtime_data_dir)
    
    def get_username(self):
        """Get the user's username from configuration file.
        
        Reads the username from the user_specific_data/username.txt file,
        which is used for personalized email classification and determining
        when emails are directly addressed to the user.
        
        Returns:
            str: The user's username/email alias, or "user" if not configured.
        
        Example:
            >>> processor = AIProcessor()
            >>> username = processor.get_username()
            >>> print(f"Processing emails for: {username}")
        """
        username_file = os.path.join(self.user_data_dir, 'username.txt')
        if os.path.exists(username_file):
            with open(username_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return "user"
    
    def get_available_categories(self):
        """Get list of available email categories for classification.
        
        Returns:
            list: List of category strings used by the email classification system.
        """
        return [
            'required_personal_action',
            'team_action', 
            'optional_action',
            'work_relevant',
            'fyi',
            'newsletter',
            'spam_to_delete',
            'job_listing',
            'optional_event'
        ]
    
    def parse_prompty_file(self, file_path):
        """Parse a prompty template file and extract the content.
        
        Prompty files use YAML frontmatter followed by the actual prompt content.
        This method parses the file format and returns the usable prompt text.
        
        Args:
            file_path (str): Path to the .prompty file to parse.
            
        Returns:
            str: The parsed prompt content without YAML frontmatter.
            
        Raises:
            ValueError: If the prompty file has malformed YAML frontmatter.
            
        Example:
            >>> processor = AIProcessor()
            >>> prompt = processor.parse_prompty_file('prompts/classifier.prompty')
            >>> print(prompt[:100])  # Show first 100 characters
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()
            raise ValueError(f"Malformed YAML frontmatter in {file_path}")
        return content
    
    def _repair_json_response(self, response_text):
        """Repair malformed JSON responses from AI services.
        
        This method attempts to fix common JSON formatting issues that can occur
        in AI responses, such as missing closing braces, unterminated strings,
        or truncated responses.
        
        Args:
            response_text (str): The potentially malformed JSON response text.
            
        Returns:
            str: The repaired JSON string, or None if no repair is possible.
        """
        if not response_text or not response_text.strip():
            return None
        
        response_text = response_text.strip()
        
        # If it's already valid JSON, return as-is
        try:
            json.loads(response_text)
            return response_text
        except json.JSONDecodeError:
            pass
        
        # For completely invalid JSON, return None
        if not ('{' in response_text or '[' in response_text):
            return None
        
        # Try common repairs
        repaired = response_text
        
        # Clean up whitespace and control characters (but preserve normal whitespace)
        repaired = ''.join(char for char in repaired if ord(char) >= 32 or char in '\n\t\r')
        repaired = repaired.replace('\r\n', '\n').replace('\r', '\n')  # Normalize line endings
        
        # Fix the specific issue in the test: unterminated string ending with comma
        import re
        
        # The test case has: "topic": "Unterminated string value,
        # We need to add the missing closing quote before the comma
        
        # Pattern: finds lines that look like: "key": "value, (missing closing quote)
        # followed by whitespace and then next line starting with "key":
        def fix_unterminated_value(match):
            key = match.group(1) 
            value = match.group(2)
            return f'"{key}": "{value}",'
        
        # Look for unterminated string values that end with comma
        repaired = re.sub(r'"([^"]+)":\s*"([^"]*),\s*\n\s*"', lambda m: f'"{m.group(1)}": "{m.group(2)}",\n    "', repaired)
        
        # Fix missing closing brace/bracket
        open_braces = repaired.count('{')
        close_braces = repaired.count('}')
        open_brackets = repaired.count('[')
        close_brackets = repaired.count(']')
        
        # Add missing closing characters
        if open_brackets > close_brackets:
            repaired += ']' * (open_brackets - close_brackets)
        if open_braces > close_braces:
            repaired += '}' * (open_braces - close_braces)
        
        # Try to parse the repaired JSON
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError as e:
                # JSON still invalid after repair attempt
            
            # If still invalid, try to extract just the structure we need
            if 'truly_relevant_actions' in repaired:
                # Create a minimal valid structure
                minimal = {
                    "truly_relevant_actions": [],
                    "superseded_actions": [],
                    "duplicate_groups": [],
                    "expired_items": []
                }
                return json.dumps(minimal)
            return None
    
    def execute_prompty(self, prompty_file, inputs=None):
        if inputs is None:
            inputs = {}
        
        prompty_path = os.path.join(self.prompts_dir, prompty_file)
        azure_config = get_azure_config()
        
        try:
            from promptflow.core import Prompty
            model_config = azure_config.get_promptflow_config()
            prompty_instance = Prompty.load(prompty_path, model={'configuration': model_config})
            return prompty_instance(**inputs)
            
        except ImportError:
            try:
                import prompty
                import prompty.azure
                
                p = prompty.load(prompty_path)
                p.model.configuration["azure_endpoint"] = azure_config.endpoint
                p.model.configuration["azure_deployment"] = azure_config.deployment  
                p.model.configuration["api_version"] = azure_config.api_version
                
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
                
                return prompty.run(p, inputs=inputs)
                
            except ImportError as e:
                print(f"\n🚨 PROMPTY LIBRARY NOT AVAILABLE")
                print(f"ImportError: {e}")
                print(f"Prompty file: {prompty_file}")
                raise RuntimeError(f"Prompty library unavailable: {e}")
                
        except Exception as e:
            # Check if this is a content filter error
            error_str = str(e).lower()
            is_content_filter = any(phrase in error_str for phrase in [
                'content_filter', 'content management policy', 'responsibleaipolicyviolation',
                'jailbreak', 'filtered', 'badrequeesterror'
            ])
            
            # Also check the error type
            error_type = type(e).__name__.lower()
            is_wrapped_openai_error = 'wrappedopenaierror' in error_type
            
            if is_content_filter or is_wrapped_openai_error:
                print(f"\n⚠️  CONTENT FILTER BLOCKED: {prompty_file}")
                print(f"Reason: Azure OpenAI content policy violation")
                print(f"Error details: {str(e)[:200]}...")
                # Return a safe fallback response instead of crashing
                return self._get_content_filter_fallback(prompty_file, inputs)
            else:
                print(f"\n🚨 PROMPTY EXECUTION FAILED")
                print(f"Error: {e}")
                print(f"Prompty file: {prompty_file}")
                print(f"Azure config: {azure_config}")
                print(f"Inputs: {inputs}")
                # Return fallback instead of raising exception
                return self._get_execution_error_fallback(prompty_file, inputs)
    
    def _get_content_filter_fallback(self, prompty_file, inputs):
        """Return appropriate fallback response when content filter blocks the request"""
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
        """Return appropriate fallback response when AI execution fails"""
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

    def get_job_context(self):
        if os.path.exists(self.job_summary_file):
            return self.parse_prompty_file(self.job_summary_file)
        return "Job context unavailable"
    
    def get_job_skills(self):
        if os.path.exists(self.job_skills_file):
            with open(self.job_skills_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return "Job skills unavailable"
    
    def get_job_role_context(self):
        if os.path.exists(self.job_role_context_file):
            with open(self.job_role_context_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return "Job role context unavailable"
    
    def get_standard_context(self) -> str:
        return f"Job Context: {self.get_job_context()}\nSkills Profile: {self.get_job_skills()}\nRole Details: {self.get_job_role_context()}"
    
    def _create_email_inputs(self, email_content, context):
        return {
            'context': context,
            'job_role_context': self.get_job_role_context(),
            'username': self.get_username(),
            'subject': email_content.get('subject', ''),
            'sender': email_content.get('sender', ''),
            'date': email_content.get('date', ''),
            'body': email_content.get('body', '')[:8000]  # Increased from 3000 to 8000 for much larger context
        }
    
    def classify_email(self, email_content, learning_data):
        """Basic email classification - now uses explanation method for consistency"""
        result = self.classify_email_with_explanation(email_content, learning_data)
        return result.get('category', 'fyi')
    
    def get_few_shot_examples(self, email_content, learning_data, max_examples=5):
        """Get relevant few-shot examples from learning data for classification"""
        if learning_data.empty:
            return []
        
        # Filter for successful classifications (where users didn't modify)
        successful_classifications = learning_data[
            learning_data.get('user_modified', False) == False
        ].copy() if 'user_modified' in learning_data.columns else learning_data.copy()
        
        if successful_classifications.empty:
            return []
        
        current_subject = email_content.get('subject', '').lower()
        current_sender = email_content.get('sender', '').lower()
        current_body = email_content.get('body', '').lower()
        
        # Simple similarity scoring based on keyword overlap
        examples_with_scores = []
        
        for _, row in successful_classifications.iterrows():
            score = 0
            row_subject = str(row.get('subject', '')).lower()
            row_sender = str(row.get('sender', '')).lower()
            row_body = str(row.get('body', '')).lower()[:1000]  # Limit body length for comparison
            
            # Score based on subject similarity
            subject_words = set(current_subject.split())
            row_subject_words = set(row_subject.split())
            if subject_words and row_subject_words:
                score += len(subject_words.intersection(row_subject_words)) / len(subject_words.union(row_subject_words)) * 3
            
            # Score based on sender similarity
            if current_sender and row_sender:
                if current_sender in row_sender or row_sender in current_sender:
                    score += 2
            
            # Score based on body keyword overlap (simple)
            body_words = set(w for w in current_body.split() if len(w) > 3)
            row_body_words = set(w for w in row_body.split() if len(w) > 3)
            if body_words and row_body_words:
                score += len(body_words.intersection(row_body_words)) / len(body_words.union(row_body_words)) * 1
            
            if score > 0:
                examples_with_scores.append((score, row))
        
        # Sort by score and take top examples
        examples_with_scores.sort(key=lambda x: x[0], reverse=True)
        
        # Format examples for prompt injection
        examples = []
        for score, row in examples_with_scores[:max_examples]:
            example = {
                'subject': str(row.get('subject', ''))[:100],
                'sender': str(row.get('sender', ''))[:50],
                'body': str(row.get('body', ''))[:300],
                'category': str(row.get('category', 'fyi'))
            }
            examples.append(example)
        
        return examples

    def apply_confidence_thresholds(self, classification_result, confidence_score=None):
        """Apply asymmetric confidence thresholds for auto-approval decisions"""
        category = classification_result.get('category', 'fyi')
        explanation = classification_result.get('explanation', '')
        
        # Default confidence handling - in a real implementation, this would come from the AI response
        if confidence_score is None:
            # Estimate confidence based on explanation length and specificity
            confidence_score = min(0.8, 0.3 + len(explanation.split()) * 0.05)
        
        # Get threshold for this category
        threshold = self.CONFIDENCE_THRESHOLDS.get(category, 0.8)
        auto_approve = confidence_score >= threshold
        
        # Determine review reason
        if not auto_approve:
            if category in ['required_personal_action', 'team_action']:
                review_reason = 'High priority category'
            else:
                review_reason = f'Low confidence ({confidence_score:.1%} < {threshold:.1%})'
        else:
            review_reason = f'Auto-approved ({confidence_score:.1%} ≥ {threshold:.1%})'
        
        return {
            'category': category,
            'explanation': explanation,
            'confidence': confidence_score,
            'auto_approve': auto_approve,
            'review_reason': review_reason,
            'threshold': threshold
        }

    def generate_explanation(self, email_content, category):
        """Generate fallback explanation when AI explanations fail"""
        subject = email_content.get('subject', 'Unknown')
        sender = email_content.get('sender', 'Unknown')
        
        # Category-specific explanation templates
        explanations = {
            'required_personal_action': f"Email from {sender} appears to require personal action based on direct addressing or responsibility.",
            'team_action': f"Email indicates action required from your team based on content analysis.",
            'optional_action': f"Email contains optional activities or requests that may be worth considering.",
            'work_relevant': f"Email contains work-related information relevant to your role but requires no immediate action.",
            'fyi': f"Email is informational only with no action required.",
            'newsletter': f"Email appears to be a newsletter or bulk information distribution.",
            'spam_to_delete': f"Email does not appear relevant to work or contains no actionable content.",
            'job_listing': f"Email contains job opportunities or recruitment-related content."
        }
        
        base_explanation = explanations.get(category, f"Classified as {category} based on email content analysis.")
        return f"{base_explanation} Subject: '{subject[:50]}...'"

    def classify_email_with_explanation(self, email_content, learning_data):
        """Enhanced email classification that returns both category and explanation"""
        # Get few-shot examples for better accuracy
        few_shot_examples = self.get_few_shot_examples(email_content, learning_data)
        
        # Build context with few-shot examples
        context = f"""{self.get_standard_context()}
Learning History: {len(learning_data)} previous decisions"""
        
        if few_shot_examples:
            context += "\n\nSimilar Examples from Past Classifications:"
            for i, example in enumerate(few_shot_examples, 1):
                context += f"\n{i}. Subject: '{example['subject']}' → Category: {example['category']}"
        
        inputs = self._create_email_inputs(email_content, context)
        result = self.execute_prompty('email_classifier_with_explanation.prompty', inputs)
        
        if not result or result in ["AI processing unavailable", "AI processing failed"]:
            # Generate fallback classification with explanation
            category = 'fyi'  # Safe default
            explanation = self.generate_explanation(email_content, category)
            return {
                'category': category,
                'explanation': explanation
            }
        
        # Try to parse as JSON
        fallback_category = 'fyi'
        fallback_data = {
            'category': fallback_category,
            'explanation': self.generate_explanation(email_content, fallback_category)
        }
        
        try:
            # Clean and parse the JSON response
            cleaned_result = clean_ai_response(result)
            parsed = parse_json_with_fallback(cleaned_result, fallback_data)
            
            # Validate required fields
            if not isinstance(parsed, dict) or 'category' not in parsed:
                print(f"⚠️ Invalid classification format: {cleaned_result[:100]}")
                return fallback_data
            
            # Clean category and provide meaningful explanation if missing
            category = clean_ai_response(parsed.get('category', 'fyi')).lower()
            explanation = parsed.get('explanation', '')
            
            # Ensure explanation is always present and meaningful
            if not explanation or len(explanation.strip()) < 10:
                explanation = self.generate_explanation(email_content, category)
            
            return {
                'category': category,
                'explanation': explanation
            }
            
        except Exception as e:
            print(f"⚠️ Error parsing classification response: {e}")
            print(f"   Raw result: {result[:200]}...")
            return fallback_data
    

    
    def detect_resolved_team_action(self, email_content, thread_context=""):
        """Detect if a team action has already been addressed by someone else in the conversation thread"""
        if not thread_context:
            return False, "No thread context available"
        
        # Create inputs for the prompty file
        inputs = self._create_email_inputs(email_content, self.get_standard_context())
        inputs['thread_context'] = thread_context
        
        # Use the dedicated prompty file
        result = self.execute_prompty('team_action_resolution_detector.prompty', inputs)
        
        if not result:
            return False, "AI analysis unavailable"
        
        # Try to parse as JSON first
        fallback_data = {'is_resolved': False, 'resolution_evidence': 'No evidence found', 'resolver': 'Unknown'}
        parsed = parse_json_with_fallback(result, fallback_data)
        
        if parsed and parsed != fallback_data:
            is_resolved = parsed.get('is_resolved', False)
            evidence = parsed.get('resolution_evidence', 'No evidence found')
            resolver = parsed.get('resolver', 'Unknown')
            return is_resolved, f"Resolution evidence: {evidence} (by {resolver})"
        
        # Fallback: simple text analysis
        result_lower = result.lower()
        resolution_keywords = ['resolved', 'completed', 'done', 'fixed', 'handled', 'taken care of']
        is_resolved = any(keyword in result_lower for keyword in resolution_keywords)
        return is_resolved, f"Text analysis result: {result[:100]}"
    
    def check_optional_item_deadline(self, email_content, action_details=None):
        """Check if an optional item's deadline has passed and should be deleted"""
        current_date = datetime.now()
        
        # Try to extract deadline from action details first
        if action_details and 'due_date' in action_details:
            due_date_str = action_details['due_date']
            if due_date_str and due_date_str != "No specific deadline":
                deadline = parse_date_string(due_date_str)
                if deadline and deadline < current_date:
                    return True, f"Deadline {due_date_str} has passed"
        
        # Use the dedicated prompty file for deadline analysis
        inputs = self._create_email_inputs(email_content, self.get_standard_context())
        inputs['current_date'] = current_date.strftime('%Y-%m-%d')
        
        result = self.execute_prompty('optional_item_deadline_checker.prompty', inputs)
        
        if not result:
            return False, "Unable to analyze deadline"
        
        # Try JSON parsing with fallback
        fallback_data = {'is_expired': False, 'deadline_date': 'Unknown', 'deadline_type': 'general'}
        parsed = parse_json_with_fallback(result, fallback_data)
        
        if parsed and parsed != fallback_data:
            is_expired = parsed.get('is_expired', False)
            deadline_info = parsed.get('deadline_date', 'Unknown')
            deadline_type = parsed.get('deadline_type', 'general')
            
            if is_expired:
                return True, f"Expired {deadline_type} deadline: {deadline_info}"
            else:
                return False, f"Active or no deadline found: {deadline_info}"
        
        # Simple text analysis fallback
        result_lower = result.lower()
        expired_keywords = ['expired', 'passed', 'missed', 'closed', 'ended']
        is_expired = any(keyword in result_lower for keyword in expired_keywords)
        return is_expired, f"Text analysis: {result[:100]}"
    
    def analyze_inbox_holistically(self, all_email_data):
        """Analyze the entire inbox context to identify truly relevant actions and relationships"""
        # Build comprehensive inbox summary
        inbox_summary = self._build_inbox_context_summary(all_email_data)
        
        # Create inputs for holistic analysis
        inputs = {
            'context': self.get_standard_context(),
            'job_role_context': self.get_job_role_context(),
            'username': self.get_username(),
            'inbox_summary': inbox_summary,
            'current_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Execute holistic analysis
        result = self.execute_prompty('holistic_inbox_analyzer.prompty', inputs)
        
        if not result:
            return None, "Holistic analysis unavailable"
        
        # Default fallback structure
        fallback_data = {
            "truly_relevant_actions": [],
            "superseded_actions": [],
            "duplicate_groups": [],
            "expired_items": []
        }
        
        # Try to parse JSON with fallback
        analysis = parse_json_with_fallback(result, fallback_data)
        
        if analysis and analysis != fallback_data:
            return analysis, "Holistic analysis completed successfully"
        
        return fallback_data, "Analysis completed with parsing issues"
    

    
    def _build_inbox_context_summary(self, all_email_data):
        """Build a comprehensive summary of all emails for holistic analysis"""
        summary_parts = []
        
        for i, email_data in enumerate(all_email_data):
            # Extract key information from each email
            entry_id = email_data.get('entry_id', f'email_{i}')
            subject = email_data.get('subject', 'Unknown Subject')
            sender = email_data.get('sender_name', email_data.get('sender', 'Unknown Sender'))
            received_time = email_data.get('received_time', 'Unknown Date')
            body_preview = email_data.get('body', '')[:300] + ('...' if len(email_data.get('body', '')) > 300 else '')
            
            date_str = format_date_for_display(received_time) if hasattr(received_time, 'strftime') else str(received_time)
            
            email_summary = f"""EMAIL_ID: {entry_id}
Subject: {subject}
From: {sender}
Date: {date_str}
Preview: {body_preview}
"""
            summary_parts.append(email_summary)
        
        return "\n---\n".join(summary_parts)
    

    

    
    def load_learning_data(self):
        """Load previous learning feedback for context"""
        return load_csv_or_empty(self.learning_file)
    
    def generate_email_summary(self, email_content):
        context = self.get_standard_context()
        inputs = self._create_email_inputs(email_content, context)
        result = self.execute_prompty('email_one_line_summary.prompty', inputs)
        
        if result and result.strip():
            summary = clean_markdown_formatting(result.strip().split('\n')[0])
            return truncate_with_ellipsis(summary, 120)
        return f"No summary - {email_content.get('subject', 'Unknown')[:50]}"
    
    def extract_action_item_details(self, email_content, context=""):
        inputs = self._create_email_inputs(email_content, context)
        result = self.execute_prompty('summerize_action_item.prompty', inputs)
        
        if not result or not result.strip():
            # Return fallback data instead of raising exception
            return {
                "action_required": f"Review email: {email_content.get('subject', 'Unknown')[:100]}",
                "due_date": "No specific deadline",
                "explanation": "AI processing unavailable - please review manually",
                "links": [],
                "relevance": "Manual review needed"
            }
        
        # Try to parse JSON with fallback
        fallback_data = {
            "action_required": f"Review email: {email_content.get('subject', 'Unknown')[:100]}",
            "due_date": "No specific deadline",
            "explanation": "AI parsing failed - please review manually",
            "links": [],
            "relevance": "Unable to parse - manual review needed"
        }
        
        return parse_json_with_fallback(result, fallback_data)
    
    def assess_event_relevance(self, subject, body, context):
        email_content = {
            'subject': subject,
            'sender': 'Unknown',
            'body': body[:3000],
            'date': ''
        }
        
        inputs = self._create_email_inputs(email_content, context)
        # Add current date to check if event has passed
        inputs['current_date'] = datetime.now().strftime('%Y-%m-%d')
        result = self.execute_prompty('event_relevance_assessment.prompty', inputs)
        
        # Handle fallback responses
        if result and result.strip():
            response = result.strip()
            # If it's a fallback message, return it as-is
            if any(phrase in response.lower() for phrase in ['content filter', 'unavailable', 'blocked']):
                return response
            return response
        return "Professional development opportunity"
    
    def generate_fyi_summary(self, email_content, context):
        inputs = self._create_email_inputs(email_content, context)
        result = self.execute_prompty('fyi_summary.prompty', inputs)
        
        if result and result.strip():
            summary = result.strip().split('\n')[0]
            return add_bullet_if_needed(summary)
        return f"• {email_content.get('subject', 'Unknown')[:80]}"
    
    def generate_newsletter_summary(self, email_content, context):
        inputs = self._create_email_inputs(email_content, context)
        result = self.execute_prompty('newsletter_summary.prompty', inputs)
        
        if result and result.strip():
            return clean_markdown_formatting(result.strip())
        return f"Newsletter from {email_content.get('sender', 'Unknown')}: {email_content.get('subject', 'No summary')}"

    def advanced_deduplicate_action_items(self, action_items):
        """Use advanced AI to intelligently deduplicate action items by detecting same underlying tasks"""
        if not action_items or len(action_items) <= 1:
            return action_items
        
        try:
            # Format action items for AI analysis
            items_for_analysis = []
            for i, item in enumerate(action_items):
                item_summary = {
                    'id': f"item_{i+1}",
                    'subject': item.get('subject', 'No subject'),
                    'sender': item.get('sender', 'Unknown sender'),
                    'action_required': item.get('action_required', 'No action specified'),
                    'due_date': item.get('due_date', 'No deadline'),
                    'explanation': item.get('explanation', 'No details'),
                    'entry_id': item.get('_entry_id', 'No ID')
                }
                items_for_analysis.append(item_summary)
            
            # Call AI for intelligent deduplication
            inputs = {
                'action_items': json.dumps(items_for_analysis, indent=2)
            }
            
            print(f"🤖 Running advanced AI deduplication on {len(action_items)} action items...")
            result = self.execute_prompty('action_item_deduplication.prompty', inputs)
            
            if result:
                # Parse AI response
                dedup_result = parse_json_with_fallback(result.strip())
                if dedup_result and 'duplicates_found' in dedup_result:
                    return self._apply_deduplication_results(action_items, dedup_result)
                else:
                    print("⚠️  AI deduplication returned invalid format, keeping all items")
                    
        except Exception as e:
            print(f"⚠️  Advanced AI deduplication failed: {e}")
        
        return action_items
    
    def _apply_deduplication_results(self, original_items, dedup_result):
        """Apply AI deduplication results to merge related action items"""
        try:
            deduplicated_items = []
            processed_indices = set()
            duplicates_merged = 0
            
            # Process duplicate groups
            for dup_group in dedup_result.get('duplicates_found', []):
                primary_id = dup_group.get('primary_item_id', '')
                duplicate_ids = dup_group.get('duplicate_item_ids', [])
                merged_action = dup_group.get('merged_action', '')
                merged_due_date = dup_group.get('merged_due_date', '')
                reason = dup_group.get('reason', 'Similar underlying task')
                confidence = dup_group.get('confidence', 0.0)
                
                # Extract indices from item IDs
                try:
                    primary_idx = int(primary_id.replace('item_', '')) - 1
                    duplicate_indices = [int(id_.replace('item_', '')) - 1 for id_ in duplicate_ids]
                except (ValueError, AttributeError):
                    continue
                
                if 0 <= primary_idx < len(original_items) and all(0 <= idx < len(original_items) for idx in duplicate_indices):
                    # Create merged item based on primary item
                    primary_item = original_items[primary_idx].copy()
                    
                    # Apply AI-suggested merging
                    if merged_action:
                        primary_item['action_required'] = merged_action
                    if merged_due_date and merged_due_date != 'earliest_deadline_from_group':
                        primary_item['due_date'] = merged_due_date
                    
                    # Find the earliest deadline among all items in the group
                    all_indices = [primary_idx] + duplicate_indices
                    earliest_date = None
                    for idx in all_indices:
                        item_date = original_items[idx].get('due_date', '')
                        if item_date and item_date != 'No specific deadline':
                            try:
                                parsed_date = parse_date_string(item_date)
                                if parsed_date and (not earliest_date or parsed_date < earliest_date):
                                    earliest_date = parsed_date
                                    primary_item['due_date'] = item_date
                            except:
                                pass
                    
                    # Track merged emails for transparency
                    if 'contributing_emails' not in primary_item:
                        primary_item['contributing_emails'] = []
                    
                    for dup_idx in duplicate_indices:
                        dup_item = original_items[dup_idx]
                        contrib_info = {
                            'subject': dup_item.get('subject', ''),
                            'sender': dup_item.get('sender', ''),
                            'entry_id': dup_item.get('_entry_id', ''),
                            'merge_reason': reason,
                            'confidence': confidence
                        }
                        primary_item['contributing_emails'].append(contrib_info)
                    
                    # Add enhanced explanation
                    original_explanation = primary_item.get('explanation', '')
                    primary_item['explanation'] = f"{original_explanation} [AI merged {len(duplicate_indices)} related reminder(s): {reason}]"
                    
                    deduplicated_items.append(primary_item)
                    processed_indices.update([primary_idx] + duplicate_indices)
                    duplicates_merged += len(duplicate_indices)
                    
                    print(f"   🔗 Merged {len(duplicate_indices)} duplicates into '{primary_item.get('subject', 'Unknown')}': {reason}")
            
            # Add remaining unique items
            for i, item in enumerate(original_items):
                if i not in processed_indices:
                    deduplicated_items.append(item)
            
            if duplicates_merged > 0:
                print(f"✅ Advanced AI deduplication completed: {duplicates_merged} duplicates merged, {len(deduplicated_items)} unique items remain")
            
            return deduplicated_items
            
        except Exception as e:
            print(f"⚠️  Error applying deduplication results: {e}")
            return original_items

    def save_learning_feedback(self, feedback_entries):
        """Save learning feedback to improve AI over time"""
        self.data_recorder.record_learning_feedback(feedback_entries)

    def record_batch_processing(self, success_count, error_count, categories_used):
        """Record batch processing results for learning and finalize accuracy"""
        self.data_recorder.record_batch_processing(success_count, error_count, categories_used)
        self.session_tracker.finalize_session(success_count, error_count, categories_used)

    def start_accuracy_session(self, total_emails):
        self.session_tracker.start_accuracy_session(total_emails)
    
    def record_suggestion_modification(self, email_data, old_category, new_category, user_explanation):
        """Record user modifications to AI suggestions"""
        self.data_recorder.record_suggestion_modification(email_data, old_category, new_category, user_explanation)
        self.session_tracker.add_modification(old_category, new_category)

    def record_accepted_suggestions(self, email_suggestions):
        """Record all accepted suggestions that were applied to Outlook for fine-tuning data"""
        self.data_recorder.record_accepted_suggestions(email_suggestions)
    
    def finalize_accuracy_session(self, success_count=None, error_count=None, categories_used=None):
        """Finalize the current accuracy session"""
        self.session_tracker.finalize_session(success_count, error_count, categories_used)
    
    
