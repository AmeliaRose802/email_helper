import os
import json
import re
import pandas as pd
from datetime import datetime
from src.azure_config import get_azure_config
from src.accuracy_tracker import AccuracyTracker


class AIProcessor:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.prompts_dir = os.path.join(project_root, 'prompts')
        self.user_data_dir = os.path.join(project_root, 'user_specific_data')
        self.runtime_data_dir = os.path.join(project_root, 'runtime_data', 'user_feedback')
        
        self.job_summary_file = os.path.join(self.user_data_dir, 'job_summery.md')
        self.job_skills_file = os.path.join(self.user_data_dir, 'job_skill_summery.md')
        self.job_role_context_file = os.path.join(self.user_data_dir, 'job_role_context.md')
        
        os.makedirs(self.runtime_data_dir, exist_ok=True)
        self.learning_file = os.path.join(self.runtime_data_dir, 'ai_learning_feedback.csv')
        self.modification_file = os.path.join(self.runtime_data_dir, 'suggestion_modifications.csv')
        
        runtime_base_dir = os.path.join(project_root, 'runtime_data')
        self.accuracy_tracker = AccuracyTracker(runtime_base_dir)
        
        self.session_start_time = datetime.now()
        self.session_total_emails = 0
        self.session_modifications = []
    
    def get_username(self):
        username_file = os.path.join(self.user_data_dir, 'username.txt')
        try:
            if os.path.exists(username_file):
                with open(username_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            return "user"
        except Exception:
            return "user"
    
    def parse_prompty_file(self, file_path):
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
        try:
            if os.path.exists(self.job_summary_file):
                return self.parse_prompty_file(self.job_summary_file)
            return "Job context unavailable"
        except Exception:
            return "Job context unavailable"
    
    def get_job_skills(self):
        try:
            if os.path.exists(self.job_skills_file):
                with open(self.job_skills_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            return "Job skills unavailable"
        except Exception:
            return "Job skills unavailable"
    
    def get_job_role_context(self):
        try:
            if os.path.exists(self.job_role_context_file):
                with open(self.job_role_context_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            return "Job role context unavailable"
        except Exception:
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
            'body': email_content.get('body', '')[:3000]
        }
    
    def classify_email(self, email_content, learning_data):
        context = f"""{self.get_standard_context()}
Learning History: {len(learning_data)} previous decisions"""
        
        inputs = self._create_email_inputs(email_content, context)
        result = self.execute_prompty('email_classifier_system.prompty', inputs)
        
        # CRASH HARD if AI classification failed  
        if not result or result in ["AI processing unavailable", "AI processing failed"]:
            print("\n" + "="*80)
            print("🚨 EMAIL CLASSIFICATION FAILURE - CRASH WITH DEBUG INFO")
            print("="*80)
            print(f"Subject: {email_content.get('subject', 'Unknown')}")
            print(f"Sender: {email_content.get('sender', 'Unknown')}")
            print(f"Learning Data Rows: {len(learning_data)}")
            print(f"\n--- EMAIL CONTENT ---")
            print(f"Body: {email_content.get('body', '')[:1000]}")
            print(f"\n--- CONTEXT ---")
            print(f"Context: {context[:500]}")
            print(f"\n--- AI RESPONSE ---")
            print(f"Result: '{result}'")
            print(f"\n--- INPUTS SENT ---")
            for key, value in inputs.items():
                print(f"{key}: {str(value)[:200]}...")
            print("="*80)
            raise RuntimeError(f"AI email classification failed for: {email_content.get('subject', 'Unknown')}")
            
        return result.strip().lower() if result else "general_information"
    
    def load_learning_data(self):
        """Load previous learning feedback for context"""
        try:
            if os.path.exists(self.learning_file):
                return pd.read_csv(self.learning_file, dtype=str)
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()
    
    def generate_email_summary(self, email_content):
        try:
            context = self.get_standard_context()
            inputs = self._create_email_inputs(email_content, context)
            result = self.execute_prompty('email_one_line_summary.prompty', inputs)
            
            if result and result.strip():
                summary = re.sub(r'^#+\s*|^\*+\s*|^-\s*|\*\*(.*?)\*\*|\*(.*?)\*', r'\1\2', result.strip().split('\n')[0])
                return summary[:120] + "..." if len(summary) > 120 else summary
            return f"No summary - {email_content.get('subject', 'Unknown')[:50]}"
        except Exception:
            return f"Summary error - {email_content.get('subject', 'Unknown')[:50]}"
    
    def extract_action_item_details(self, email_content, context=""):
        inputs = self._create_email_inputs(email_content, context)
        result = self.execute_prompty('summerize_action_item.prompty', inputs)
        
        # CRASH HARD if AI didn't respond properly
        if not result or not result.strip():
            print("\n" + "="*80)
            print("🚨 AI PROMPTY EXECUTION FAILURE - NO RESPONSE")
            print("="*80)
            print(f"Prompty File: summerize_action_item.prompty")
            print(f"Subject: {email_content.get('subject', 'Unknown')}")
            print(f"Sender: {email_content.get('sender', 'Unknown')}")
            print(f"Body Length: {len(email_content.get('body', ''))} chars")
            print(f"Context Length: {len(context)} chars")
            print("\n--- EMAIL CONTENT ---")
            print(f"Subject: {email_content.get('subject', '')}")
            print(f"Body: {email_content.get('body', '')[:1000]}")
            print(f"\n--- INPUTS SENT TO AI ---")
            for key, value in inputs.items():
                print(f"{key}: {str(value)[:200]}...")
            print(f"\n--- AI RESPONSE ---")
            print(f"Result: '{result}'")
            print("="*80)
            raise RuntimeError(f"AI prompty execution failed - no response for: {email_content.get('subject', 'Unknown')}")
        
        # Clean JSON markers
        original_result = result
        result = result.strip()
        result = re.sub(r'^```json\n?|^```\n?|```$', '', result).strip()
        
        try:
            return json.loads(result)
        except json.JSONDecodeError as e:
            print("\n" + "="*80)
            print("🚨 AI JSON PARSING FAILURE - CRASH WITH DEBUG INFO")
            print("="*80)
            print(f"Subject: {email_content.get('subject', 'Unknown')}")
            print(f"JSON Decode Error: {e}")
            print(f"\n--- ORIGINAL AI RESPONSE ---")
            print(f"Raw Response: '{original_result}'")
            print(f"\n--- CLEANED RESPONSE ---")
            print(f"Cleaned: '{result}'")
            print(f"\n--- EMAIL CONTENT ---")
            print(f"Subject: {email_content.get('subject', '')}")
            print(f"Body: {email_content.get('body', '')[:500]}")
            print(f"\n--- INPUTS SENT ---")
            for key, value in inputs.items():
                print(f"{key}: {str(value)[:100]}...")
            print("="*80)
            raise RuntimeError(f"AI returned invalid JSON for: {email_content.get('subject', 'Unknown')} - Error: {e}")
    
    def assess_event_relevance(self, subject, body, context):
        email_content = {
            'subject': subject,
            'sender': 'Unknown',
            'body': body[:500],
            'date': ''
        }
        
        try:
            inputs = self._create_email_inputs(email_content, context)
            result = self.execute_prompty('event_relevance_assessment.prompty', inputs)
            return result.strip() if result else "Professional development opportunity"
        except Exception:
            return "Professional development opportunity"
    
    def generate_fyi_summary(self, email_content, context):
        try:
            inputs = self._create_email_inputs(email_content, context)
            result = self.execute_prompty('fyi_summary.prompty', inputs)
            
            if result and result.strip():
                summary = result.strip().split('\n')[0]
                return f"• {summary}" if not summary.startswith('•') else summary
            return f"• {email_content.get('subject', 'Unknown')[:80]}"
        except Exception:
            return f"• {email_content.get('subject', 'Unknown')[:80]}"
    
    def generate_newsletter_summary(self, email_content, context):
        try:
            inputs = self._create_email_inputs(email_content, context)
            result = self.execute_prompty('newsletter_summary.prompty', inputs)
            
            if result and result.strip():
                summary = re.sub(r'^#+\s*|\*\*(.*?)\*\*|\*(.*?)\*', r'\1\2', result.strip())
                return summary[:300] + "..." if len(summary) > 300 else summary
            return f"Newsletter from {email_content.get('sender', 'Unknown')}: {email_content.get('subject', 'No summary')}"
        except Exception:
            return f"Newsletter from {email_content.get('sender', 'Unknown')}: {email_content.get('subject', 'No summary')}"

    def save_learning_feedback(self, feedback_entries):
        """Save learning feedback to improve AI over time"""
        processed_entries = []
        for entry in feedback_entries:
            processed_entry = entry.copy()
            # Convert datetime objects to strings
            for key, value in processed_entry.items():
                if hasattr(value, 'strftime'):
                    processed_entry[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif value is not None and not isinstance(value, (str, int, float, bool)):
                    processed_entry[key] = str(value)
            processed_entries.append(processed_entry)
            
        new_df = pd.DataFrame(processed_entries)
        
        try:
            if os.path.exists(self.learning_file):
                existing_df = pd.read_csv(self.learning_file)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                combined_df = new_df
            
            combined_df.to_csv(self.learning_file, index=False)
        except Exception:
            pass  # Continue without saving if file operations fail

    def record_batch_processing(self, success_count, error_count, categories_used):
        """Record batch processing results for learning and finalize accuracy"""
        batch_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'batch_categorization',
            'emails_processed': success_count + error_count,
            'successful': success_count,
            'errors': error_count,
            'categories_used': categories_used
        }
        
        try:
            batch_df = pd.DataFrame([batch_entry])
            
            if os.path.exists(self.learning_file):
                existing_df = pd.read_csv(self.learning_file)
                combined_df = pd.concat([existing_df, batch_df], ignore_index=True)
            else:
                combined_df = batch_df
                
            combined_df.to_csv(self.learning_file, index=False)
        except Exception:
            pass
        
        self.finalize_accuracy_session(success_count, error_count, categories_used)

    def start_accuracy_session(self, total_emails):
        self.session_start_time = datetime.now()
        self.session_total_emails = total_emails
        self.session_modifications = []
    
    def record_suggestion_modification(self, email_data, old_category, new_category, user_explanation):
        email_date = email_data.get('date', email_data.get('received_time', 'Unknown'))
        if hasattr(email_date, 'strftime'):
            email_date = email_date.strftime('%Y-%m-%d %H:%M:%S')
            
        modification_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'subject': email_data.get('subject', 'Unknown'),
            'sender': email_data.get('sender', 'Unknown'),
            'email_date': str(email_date),
            'old_suggestion': old_category,
            'new_suggestion': new_category,
            'user_explanation': user_explanation,
            'body_preview': email_data.get('body', '')[:200]
        }
        
        try:
            new_df = pd.DataFrame([modification_entry])
            
            if os.path.exists(self.modification_file):
                existing_df = pd.read_csv(self.modification_file)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                combined_df = new_df
                
            combined_df.to_csv(self.modification_file, index=False)
        except Exception:
            pass
        
        self.session_modifications.append({
            'old_category': old_category,
            'new_category': new_category,
            'timestamp': datetime.now()
        })
    
    def finalize_accuracy_session(self, success_count=None, error_count=None, categories_used=None):
        if self.session_total_emails == 0:
            return
            
        session_duration = (datetime.now() - self.session_start_time).total_seconds() / 60
        modifications_count = len(self.session_modifications)
        accuracy_rate = self.accuracy_tracker.calculate_accuracy_for_session(
            self.session_total_emails, self.session_modifications
        )
        
        category_modifications = {}
        for mod in self.session_modifications:
            old_cat = mod['old_category']
            category_modifications[old_cat] = category_modifications.get(old_cat, 0) + 1
        
        session_data = {
            'run_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'total_emails': self.session_total_emails,
            'modifications_count': modifications_count,
            'accuracy_rate': accuracy_rate,
            'category_modifications': category_modifications
        }
        
        self.accuracy_tracker.record_session_accuracy(session_data)
        print(f"Session: {self.session_total_emails} emails, {modifications_count} corrections, {accuracy_rate:.1f}% accuracy")
    
    def show_accuracy_report(self, days_back=30):
        self.accuracy_tracker.display_accuracy_report(days_back)
    
    @staticmethod
    def get_available_categories():
        return [
            'required_personal_action',
            'team_action', 
            'optional_action',
            'job_listing',
            'optional_event',
            'work_relevant',
            'fyi',
            'newsletter',
            'spam_to_delete'
        ]
