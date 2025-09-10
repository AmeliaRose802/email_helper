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
            'body': email_content.get('body', '')[:8000]  # Increased from 3000 to 8000 for much larger context
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
            
        # Clean result - strip markdown formatting and whitespace, convert to lowercase
        cleaned_result = result.strip()
        cleaned_result = cleaned_result.replace('**', '').replace('*', '')  # Remove markdown asterisks
        return cleaned_result.lower() if cleaned_result else "general_information"
    
    def classify_email_improved(self, email_content, learning_data):
        """Test the improved classification prompt"""
        context = f"""{self.get_standard_context()}
Learning History: {len(learning_data)} previous decisions"""
        
        inputs = self._create_email_inputs(email_content, context)
        result = self.execute_prompty('email_classifier_system_improved.prompty', inputs)
        
        if not result or result in ["AI processing unavailable", "AI processing failed"]:
            return "general_information"
            
        # Clean result - strip markdown formatting and whitespace, convert to lowercase
        cleaned_result = result.strip()
        cleaned_result = cleaned_result.replace('**', '').replace('*', '')  # Remove markdown asterisks
        return cleaned_result.lower() if cleaned_result else "general_information"
    
    def detect_resolved_team_action(self, email_content, thread_context=""):
        """Detect if a team action has already been addressed by someone else in the conversation thread"""
        if not thread_context:
            return False, "No thread context available"
        
        try:
            # Create inputs for the prompty file
            inputs = self._create_email_inputs(email_content, self.get_standard_context())
            inputs['thread_context'] = thread_context
            
            # Use the dedicated prompty file
            result = self.execute_prompty('team_action_resolution_detector.prompty', inputs)
            
            if not result:
                return False, "AI analysis unavailable"
            
            # Clean and parse JSON response
            result = result.strip()
            result = re.sub(r'^```json\n?|^```\n?|```$', '', result).strip()
            
            try:
                parsed = json.loads(result)
                is_resolved = parsed.get('is_resolved', False)
                evidence = parsed.get('resolution_evidence', 'No evidence found')
                resolver = parsed.get('resolver', 'Unknown')
                
                return is_resolved, f"Resolution evidence: {evidence} (by {resolver})"
                
            except json.JSONDecodeError:
                # Fallback: simple text analysis
                result_lower = result.lower()
                resolution_keywords = ['resolved', 'completed', 'done', 'fixed', 'handled', 'taken care of']
                is_resolved = any(keyword in result_lower for keyword in resolution_keywords)
                return is_resolved, f"Text analysis result: {result[:100]}"
                
        except Exception as e:
            return False, f"Analysis error: {str(e)}"
    
    def check_optional_item_deadline(self, email_content, action_details=None):
        """Check if an optional item's deadline has passed and should be deleted"""
        try:
            current_date = datetime.now()
            
            # Try to extract deadline from action details first
            if action_details and 'due_date' in action_details:
                due_date_str = action_details['due_date']
                if due_date_str and due_date_str != "No specific deadline":
                    deadline = self._parse_date_string(due_date_str)
                    if deadline and deadline < current_date:
                        return True, f"Deadline {due_date_str} has passed"
            
            # Use the dedicated prompty file for deadline analysis
            inputs = self._create_email_inputs(email_content, self.get_standard_context())
            inputs['current_date'] = current_date.strftime('%Y-%m-%d')
            
            result = self.execute_prompty('optional_item_deadline_checker.prompty', inputs)
            
            if not result:
                return False, "Unable to analyze deadline"
            
            # Clean and parse JSON response
            result = result.strip()
            result = re.sub(r'^```json\n?|^```\n?|```$', '', result).strip()
            
            try:
                parsed = json.loads(result)
                is_expired = parsed.get('is_expired', False)
                deadline_info = parsed.get('deadline_date', 'Unknown')
                deadline_type = parsed.get('deadline_type', 'general')
                
                if is_expired:
                    return True, f"Expired {deadline_type} deadline: {deadline_info}"
                else:
                    return False, f"Active or no deadline found: {deadline_info}"
                    
            except json.JSONDecodeError:
                # Simple text analysis fallback
                result_lower = result.lower()
                expired_keywords = ['expired', 'passed', 'missed', 'closed', 'ended']
                is_expired = any(keyword in result_lower for keyword in expired_keywords)
                return is_expired, f"Text analysis: {result[:100]}"
                
        except Exception as e:
            return False, f"Deadline analysis error: {str(e)}"
    
    def analyze_inbox_holistically(self, all_email_data):
        """Analyze the entire inbox context to identify truly relevant actions and relationships"""
        try:
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
            
            # Clean and parse JSON response
            result = result.strip()
            result = re.sub(r'^```json\n?|^```\n?|```$', '', result).strip()
            
            try:
                analysis = json.loads(result)
                return analysis, "Holistic analysis completed successfully"
                
            except json.JSONDecodeError as e:
                # Try to repair common JSON issues
                repaired_result = self._repair_json_response(result)
                if repaired_result:
                    try:
                        analysis = json.loads(repaired_result)
                        return analysis, f"Analysis completed with JSON repair applied: {str(e)}"
                    except json.JSONDecodeError:
                        pass
                
                # Return basic structure if JSON parsing fails
                return {
                    "truly_relevant_actions": [],
                    "superseded_actions": [],
                    "duplicate_groups": [],
                    "expired_items": []
                }, f"Analysis completed with parsing issues: {str(e)}"
                
        except Exception as e:
            return None, f"Holistic analysis error: {str(e)}"
    
    def _repair_json_response(self, json_str):
        """Attempt to repair common JSON parsing issues"""
        try:
            # Remove any trailing incomplete content after last complete structure
            json_str = json_str.strip()
            
            # Find the last complete closing brace
            last_brace = json_str.rfind('}')
            if last_brace > 0:
                json_str = json_str[:last_brace + 1]
            
            # Try to fix unterminated strings by adding closing quotes
            lines = json_str.split('\n')
            repaired_lines = []
            
            for line in lines:
                # Check if line has unmatched quotes
                quote_count = line.count('"')
                # Skip lines that are comments or contain escaped quotes
                if '//' not in line and '\\' not in line and quote_count % 2 == 1:
                    # Find the last quote and see if it needs closing
                    if line.rstrip().endswith(',') and line.count(':') > 0:
                        # Likely a value that needs closing quote before comma
                        line = line.rstrip(',') + '",'
                    elif line.rstrip() and not line.rstrip().endswith('"'):
                        # Add closing quote at end
                        line = line.rstrip() + '"'
                
                repaired_lines.append(line)
            
            repaired_json = '\n'.join(repaired_lines)
            
            # Ensure proper JSON structure
            if not repaired_json.strip().startswith('{'):
                return None
            if not repaired_json.strip().endswith('}'):
                repaired_json = repaired_json.rstrip() + '}'
            
            return repaired_json
            
        except Exception:
            return None
    
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
            
            if hasattr(received_time, 'strftime'):
                date_str = received_time.strftime('%Y-%m-%d %H:%M')
            else:
                date_str = str(received_time)
            
            email_summary = f"""EMAIL_ID: {entry_id}
Subject: {subject}
From: {sender}
Date: {date_str}
Preview: {body_preview}
"""
            summary_parts.append(email_summary)
        
        return "\n---\n".join(summary_parts)
    
    def _parse_date_string(self, date_str):
        """Parse various date string formats"""
        if not date_str or date_str == "No specific deadline":
            return None
            
        try:
            # Common date formats
            date_formats = [
                '%Y-%m-%d',
                '%m/%d/%Y', 
                '%d/%m/%Y',
                '%B %d, %Y',
                '%b %d, %Y',
                '%Y-%m-%d %H:%M',
                '%m/%d/%Y %H:%M'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If no format matches, return None
            return None
            
        except Exception:
            return None
    
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
            'body': body[:3000],  # Increased from 500 to 3000 for better context
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
                # Remove the 300 character truncation to allow full newsletter summaries
                return summary
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

    def record_accepted_suggestions(self, email_suggestions):
        """Record all accepted suggestions that were applied to Outlook for fine-tuning data"""
        # Create accepted suggestions file path
        accepted_file = os.path.join(self.runtime_data_dir, 'accepted_suggestions.csv')
        
        accepted_entries = []
        for suggestion_data in email_suggestions:
            email_data = suggestion_data.get('email_data', {})
            suggestion = suggestion_data.get('ai_suggestion', 'unknown')
            initial_classification = suggestion_data.get('initial_classification', suggestion)
            processing_notes = suggestion_data.get('processing_notes', [])
            ai_summary = suggestion_data.get('ai_summary', '')
            
            # Determine if this was modified or accepted as-is
            was_modified = suggestion != initial_classification
            modification_reason = "User modified in review" if was_modified else "Accepted as suggested"
            
            # Get email date
            email_date = email_data.get('received_time', email_data.get('date', 'Unknown'))
            if hasattr(email_date, 'strftime'):
                email_date = email_date.strftime('%Y-%m-%d %H:%M:%S')
            
            accepted_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'subject': email_data.get('subject', 'Unknown'),
                'sender': email_data.get('sender_name', email_data.get('sender', 'Unknown')),
                'email_date': str(email_date),
                'initial_ai_suggestion': initial_classification,
                'final_applied_category': suggestion,
                'was_modified': was_modified,
                'modification_reason': modification_reason,
                'processing_notes': '; '.join(processing_notes) if processing_notes else '',
                'ai_summary': ai_summary[:500],  # Truncate for storage
                'body_preview': email_data.get('body', '')[:300],
                'thread_count': suggestion_data.get('thread_data', {}).get('thread_count', 1)
            }
            accepted_entries.append(accepted_entry)
        
        if not accepted_entries:
            return
        
        try:
            new_df = pd.DataFrame(accepted_entries)
            
            # Append to existing file or create new one
            if os.path.exists(accepted_file):
                existing_df = pd.read_csv(accepted_file)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                combined_df = new_df
                
            combined_df.to_csv(accepted_file, index=False)
            print(f"📊 Recorded {len(accepted_entries)} accepted suggestions for fine-tuning data")
            
        except Exception as e:
            print(f"⚠️ Error recording accepted suggestions: {e}")
    
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
