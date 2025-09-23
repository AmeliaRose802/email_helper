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
from accuracy_tracker import AccuracyTracker
from data_recorder import DataRecorder
from utils import (
    clean_json_response, parse_json_with_fallback, parse_date_string,
    clean_ai_response, clean_markdown_formatting, truncate_with_ellipsis,
    add_bullet_if_needed, SessionTracker, load_csv_or_empty, format_date_for_display
)


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
    
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.prompts_dir = os.path.join(project_root, 'prompts')
        self.user_data_dir = os.path.join(project_root, 'user_specific_data')
        self.runtime_data_dir = os.path.join(
            project_root, 'runtime_data', 'user_feedback'
        )
        
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
            print(f"\n🚨 PROMPTY EXECUTION FAILED")
            print(f"Error: {e}")
            print(f"Prompty file: {prompty_file}")
            print(f"Azure config: {azure_config}")
            print(f"Inputs: {inputs}")
            raise RuntimeError(f"Prompty execution failed: {e}")
    
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
        return f"Job Context: {self.get_job_context()}\nSkills Profile: {self.get_job_skills()}"
    
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
        
        # Asymmetric thresholds: FYI requires 90% confidence for auto-approval
        # Required actions always need manual review regardless of confidence
        auto_approve = False
        
        if category == 'fyi' and confidence_score >= 0.9:
            auto_approve = True
        elif category in ['required_personal_action', 'team_action']:
            auto_approve = False  # Always review high-priority items
        elif category in ['optional_action', 'work_relevant'] and confidence_score >= 0.8:
            auto_approve = True
        elif category in ['newsletter', 'spam_to_delete'] and confidence_score >= 0.7:
            auto_approve = True
        
        return {
            'category': category,
            'explanation': explanation,
            'confidence': confidence_score,
            'auto_approve': auto_approve,
            'review_reason': 'Low confidence' if not auto_approve and category != 'required_personal_action' else 'High priority category'
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
            raise RuntimeError(f"AI prompty execution failed - no response for: {email_content.get('subject', 'Unknown')}")
        
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
        result = self.execute_prompty('event_relevance_assessment.prompty', inputs)
        return result.strip() if result else "Professional development opportunity"
    
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
    
    
