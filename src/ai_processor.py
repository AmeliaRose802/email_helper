#!/usr/bin/env python3
"""
AI Processor - Handles all AI-related processing (prompts, classification, summaries)
"""

import os
import json
import re
import pandas as pd
from datetime import datetime
from azure_config import get_azure_config
from accuracy_tracker import AccuracyTracker


class AIProcessor:
    def __init__(self):
        # Set up paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.prompts_dir = os.path.join(project_root, 'prompts')
        self.user_data_dir = os.path.join(project_root, 'user_specific_data')
        self.runtime_data_dir = os.path.join(project_root, 'runtime_data', 'user_feedback')
        
        # File references (now in user_specific_data)
        self.job_summary_file = os.path.join(self.user_data_dir, 'job_summery.md')
        self.job_skills_file = os.path.join(self.user_data_dir, 'job_skill_summery.md')
        self.job_role_context_file = os.path.join(self.user_data_dir, 'job_role_context.md')
        self.email_classifier_system_file = 'email_classifier_system.prompty'
        
        # Learning files (now in runtime_data)
        os.makedirs(self.runtime_data_dir, exist_ok=True)
        self.learning_file = os.path.join(self.runtime_data_dir, 'ai_learning_feedback.csv')
        self.modification_file = os.path.join(self.runtime_data_dir, 'suggestion_modifications.csv')
        
        # Initialize accuracy tracker
        runtime_base_dir = os.path.join(project_root, 'runtime_data')
        self.accuracy_tracker = AccuracyTracker(runtime_base_dir)
        
        # Session tracking
        self.session_start_time = datetime.now()
        self.session_total_emails = 0
        self.session_modifications = []
    
    def get_username(self):
        """Load username from user_specific_data/username.txt"""
        username_file = os.path.join(self.user_data_dir, 'username.txt')
        try:
            if os.path.exists(username_file):
                with open(username_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            else:
                print(f"⚠️  Username file not found: {username_file}")
                return "user"  # fallback
        except Exception as e:
            print(f"⚠️  Error reading username file: {e}")
            return "user"  # fallback
    
    def load_learning_data(self):
        """Load previous learning feedback"""
        try:
            if os.path.exists(self.learning_file):
                # Load CSV and ensure no datetime parsing issues
                df = pd.read_csv(self.learning_file, dtype=str)  # Load all columns as strings
                return df
            return pd.DataFrame()
        except Exception as e:
            print(f"⚠️  Error loading learning data: {e}")
            return pd.DataFrame()
    
    def parse_prompty_file(self, file_path):
        """Parse prompty file content"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()
            else:
                raise ValueError(f"Malformed YAML frontmatter in {file_path}")
        else:
            return content
    
    def execute_prompty(self, prompty_file, inputs=None):
        """Execute a prompty file with given inputs using secure Azure authentication"""
        if inputs is None:
            inputs = {}
        
        prompty_path = os.path.join(self.prompts_dir, prompty_file)
        
        # Get secure Azure configuration
        azure_config = get_azure_config()
        
        # Try promptflow approach first (preferred method)
        try:
            from promptflow.core import Prompty
            
            # Get the model configuration
            model_config = azure_config.get_promptflow_config()
            
            # Load prompty with secure configuration
            prompty_instance = Prompty.load(prompty_path, model={'configuration': model_config})
            
            # Execute with inputs
            result = prompty_instance(**inputs)
            return result
            
        except ImportError as ie:
            print(f"⚠️  PromptFlow not available, falling back to prompty: {ie}")
            
            # Fallback to original prompty approach
            try:
                import prompty
                import prompty.azure
                
                # Load the prompty file
                p = prompty.load(prompty_path)
                
                # Override the configuration with secure settings
                p.model.configuration["azure_endpoint"] = azure_config.endpoint
                p.model.configuration["azure_deployment"] = azure_config.deployment  
                p.model.configuration["api_version"] = azure_config.api_version
                
                # Handle authentication method
                if azure_config.use_azure_credential():
                    # Use DefaultAzureCredential with token provider
                    try:
                        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
                        
                        token_provider = get_bearer_token_provider(
                            DefaultAzureCredential(), 
                            "https://cognitiveservices.azure.com/.default"
                        )
                        p.model.configuration["azure_ad_token_provider"] = token_provider
                        
                        # Remove API key if present since we're using token auth
                        if "api_key" in p.model.configuration:
                            del p.model.configuration["api_key"]
                            
                    except ImportError as ie2:
                        print(f"⚠️  Azure identity not available: {ie2}")
                        print("   Falling back to API key authentication")
                        p.model.configuration["api_key"] = azure_config.get_api_key()
                else:
                    # Use API key authentication
                    p.model.configuration["api_key"] = azure_config.get_api_key()
                    print("⚠️  Using API key authentication")
                
                # Execute the prompty with secure configuration and inputs
                result = prompty.run(p, inputs=inputs)
                return result
                
            except ImportError as e:
                print(f"⚠️  Prompty library not available: {e}")
                return "AI processing unavailable"
                
        except Exception as e:
            print(f"⚠️  Error executing prompty: {e}")
            print(f"   Prompty file: {prompty_file}")
            print(f"   Configuration: {azure_config}")
            return "AI processing failed"
    
    def get_job_context(self):
        """Get job context from file"""
        try:
            if os.path.exists(self.job_summary_file):
                return self.parse_prompty_file(self.job_summary_file)
            else:
                print(f"⚠️  Job summary file not found: {self.job_summary_file}")
                print("   Please create user_specific_data/job_summery.md with your job context")
                return "Job context unavailable - please create user_specific_data/job_summery.md"
        except Exception as e:
            print(f"⚠️  Could not load job context: {e}")
            return "Job context unavailable"
    
    def get_job_skills(self):
        """Get job skills from file"""
        try:
            if os.path.exists(self.job_skills_file):
                with open(self.job_skills_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            else:
                print(f"⚠️  Job skills file not found: {self.job_skills_file}")
                print("   Please create user_specific_data/job_skill_summery.md with your skills profile")
                return "Job skills unavailable - please create user_specific_data/job_skill_summery.md"
        except Exception as e:
            print(f"⚠️  Could not load job skills: {e}")
            return "Job skills unavailable"
    
    def get_job_role_context(self):
        """Get job role context from file"""
        try:
            if os.path.exists(self.job_role_context_file):
                with open(self.job_role_context_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            else:
                print(f"⚠️  Job role context file not found: {self.job_role_context_file}")
                print("   Please create user_specific_data/job_role_context.md with your role context")
                return "Job role context unavailable - please create user_specific_data/job_role_context.md"
        except Exception as e:
            print(f"⚠️  Could not load job role context: {e}")
            return "Job role context unavailable"
    
    def get_standard_context(self) -> str:
        """Get standard job context string used across the application"""
        return f"Job Context: {self.get_job_context()}\nSkills Profile: {self.get_job_skills()}"
    
    def _create_email_inputs(self, email_content, context):
        """Create input dictionary for prompty execution"""
        return {
            'context': context,
            'job_role_context': self.get_job_role_context(),
            'username': self.get_username(),
            'subject': email_content.get('subject', ''),
            'sender': email_content.get('sender', ''),
            'date': email_content.get('date', ''),
            'body': email_content.get('body', '')[:3000]  # Increased for better context
        }
    
    def classify_email(self, email_content, learning_data):
        """AI-powered email classification using prompty"""
        context = f"""{self.get_standard_context()}
Learning History: {len(learning_data)} previous decisions"""
        
        inputs = self._create_email_inputs(email_content, context)
        result = self.execute_prompty(self.email_classifier_system_file, inputs)
        return result.strip().lower() if result else "general_information"
    
    def generate_email_summary(self, email_content):
        """Generate a concise AI summary of an email"""
        try:
            context = self.get_standard_context()
            inputs = self._create_email_inputs(email_content, context)
            
            # Use the dedicated one-line summary prompt
            result = self.execute_prompty('email_one_line_summary.prompty', inputs)
            
            if result and result.strip():
                # Clean up the result - should already be one line but ensure it
                summary = result.strip().split('\n')[0]
                # Remove any markdown formatting that might sneak in
                summary = re.sub(r'^#+\s*', '', summary)  # Remove headers
                summary = re.sub(r'\*\*(.*?)\*\*', r'\1', summary)  # Remove bold
                summary = re.sub(r'\*(.*?)\*', r'\1', summary)  # Remove italic
                summary = re.sub(r'^-\s*', '', summary)  # Remove bullet points
                
                # Limit summary length for display
                if len(summary) > 120:
                    summary = summary[:117] + "..."
                    
                return summary
            else:
                return f"No summary available - {email_content.get('subject', 'Unknown')[:50]}"
                
        except Exception as e:
            print(f"⚠️  Failed to generate AI summary: {e}")
            return f"Summary error - {email_content.get('subject', 'Unknown')[:50]}"
    
    def extract_action_item_details(self, email_content, context=""):
        """Extract detailed action item information using prompty"""
        inputs = self._create_email_inputs(email_content, context)
        result = self.execute_prompty('summerize_action_item.prompty', inputs)
        
        if not result or not result.strip():
            return {
                'due_date': 'No specific deadline',
                'action_required': 'Review email content',
                'explanation': 'AI could not analyze this email',
                'relevance': 'General professional interest',
                'links': []
            }
        
        # Strip markdown code blocks if present
        result = result.strip()
        if result.startswith('```json'):
            result = result[7:]  # Remove ```json
        if result.startswith('```'):
            result = result[3:]  # Remove ``` 
        if result.endswith('```'):
            result = result[:-3]  # Remove trailing ```
        
        result = result.strip()
        
        try:
            return json.loads(result)
        except json.JSONDecodeError as e:
            print(f"⚠️  Could not parse action item details: {e}")
            return {
                'due_date': 'No specific deadline',
                'action_required': 'Review email content',
                'explanation': 'AI parsing failed',
                'relevance': 'General professional interest',
                'links': []
            }
    
    def assess_event_relevance(self, subject, body, context):
        """Assess why an event is relevant to the user using AI"""
        # Create proper email content structure
        email_content = {
            'subject': subject,
            'sender': 'Unknown',
            'body': body[:500],
            'date': ''  # Not critical for relevance assessment
        }
        
        try:
            # Use the standard input creation method that includes username
            inputs = self._create_email_inputs(email_content, context)
            result = self.execute_prompty('event_relevance_assessment.prompty', inputs)
            return result.strip() if result else "Professional development or networking opportunity"
        except Exception as e:
            print(f"⚠️  AI relevance assessment failed: {e}")
            return "Professional development or networking opportunity"
    
    def save_learning_feedback(self, feedback_entries):
        """Save learning feedback to CSV"""
        # Ensure all datetime objects are converted to strings
        processed_entries = []
        for entry in feedback_entries:
            processed_entry = entry.copy()
            for key, value in processed_entry.items():
                if hasattr(value, 'strftime'):
                    processed_entry[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif not isinstance(value, (str, int, float, bool)) and value is not None:
                    processed_entry[key] = str(value)
            processed_entries.append(processed_entry)
            
        new_df = pd.DataFrame(processed_entries)
        
        try:
            if os.path.exists(self.learning_file):
                existing_df = pd.read_csv(self.learning_file)
                # Ensure consistent data types
                for col in new_df.columns:
                    if col in existing_df.columns:
                        existing_df[col] = existing_df[col].astype(str)
                    new_df[col] = new_df[col].astype(str)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                combined_df = new_df
            
            combined_df.to_csv(self.learning_file, index=False)
        except Exception as e:
            print(f"⚠️  Error saving learning feedback: {e}")
            print("   Continuing without saving to file...")
    
    def generate_fyi_summary(self, email_content, context):
        """Generate a bullet point summary for FYI notices"""
        try:
            inputs = self._create_email_inputs(email_content, context)
            result = self.execute_prompty('fyi_summary.prompty', inputs)
            
            if result and result.strip():
                summary = result.strip().split('\n')[0]  # Take first line only
                # Ensure it starts with bullet point
                if not summary.startswith('•'):
                    summary = f"• {summary}"
                return summary
            else:
                return f"• {email_content.get('subject', 'Unknown')[:80]}"
                
        except Exception as e:
            print(f"⚠️  Failed to generate FYI summary: {e}")
            return f"• {email_content.get('subject', 'Unknown')[:80]}"
    
    def generate_newsletter_summary(self, email_content, context):
        """Generate a paragraph summary for newsletters"""
        try:
            inputs = self._create_email_inputs(email_content, context)
            result = self.execute_prompty('newsletter_summary.prompty', inputs)
            
            if result and result.strip():
                # Clean up the result - should be paragraph format
                summary = result.strip()
                # Remove any markdown formatting
                summary = re.sub(r'^#+\s*', '', summary)  # Remove headers
                summary = re.sub(r'\*\*(.*?)\*\*', r'\1', summary)  # Remove bold
                summary = re.sub(r'\*(.*?)\*', r'\1', summary)  # Remove italic
                
                # Limit length for display
                if len(summary) > 300:
                    summary = summary[:297] + "..."
                    
                return summary
            else:
                return f"Newsletter from {email_content.get('sender', 'Unknown')}: {email_content.get('subject', 'No summary available')}"
                
        except Exception as e:
            print(f"⚠️  Failed to generate newsletter summary: {e}")
            return f"Newsletter from {email_content.get('sender', 'Unknown')}: {email_content.get('subject', 'No summary available')}"

    def record_batch_processing(self, success_count, error_count, categories_used):
        """Record batch processing results for learning AND finalize accuracy tracking"""
        batch_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Use string format
            'action': 'batch_categorization',
            'emails_processed': success_count + error_count,
            'successful': success_count,
            'errors': error_count,
            'categories_used': categories_used
        }
        
        # Save to existing learning file
        try:
            batch_df = pd.DataFrame([batch_entry])
            
            if os.path.exists(self.learning_file):
                existing_df = pd.read_csv(self.learning_file)
                # Ensure consistent string types for timestamp columns
                if 'timestamp' in existing_df.columns:
                    existing_df['timestamp'] = existing_df['timestamp'].astype(str)
                batch_df['timestamp'] = batch_df['timestamp'].astype(str)
                combined_df = pd.concat([existing_df, batch_df], ignore_index=True)
            else:
                combined_df = batch_df
                
            combined_df.to_csv(self.learning_file, index=False)
            
        except Exception as e:
            print(f"⚠️  Error saving batch processing record: {e}")
            print("   Continuing without saving to file...")
            print(f"⚠️  Could not record batch processing: {e}")
        
        # Finalize accuracy tracking for this session
        self.finalize_accuracy_session(success_count, error_count, categories_used)
    
    def start_accuracy_session(self, total_emails):
        """Initialize accuracy tracking for a new session"""
        self.session_start_time = datetime.now()
        self.session_total_emails = total_emails
        self.session_modifications = []
    
    def record_suggestion_modification(self, email_data, old_category, new_category, user_explanation):
        """Record the suggestion modification to CSV for learning AND track for accuracy"""
        # Ensure datetime is properly formatted as string to avoid pandas timezone issues
        email_date = email_data.get('date', email_data.get('received_time', 'Unknown'))
        if hasattr(email_date, 'strftime'):
            email_date = email_date.strftime('%Y-%m-%d %H:%M:%S')
        elif not isinstance(email_date, str):
            email_date = str(email_date)
            
        modification_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Use string format
            'subject': email_data.get('subject', 'Unknown'),
            'sender': email_data.get('sender', 'Unknown'),
            'email_date': email_date,  # Now guaranteed to be string
            'old_suggestion': old_category,
            'new_suggestion': new_category,
            'user_explanation': user_explanation,
            'body_preview': email_data.get('body', '')[:200]
        }
        
        try:
            # Save to CSV with better error handling
            new_df = pd.DataFrame([modification_entry])
            
            if os.path.exists(self.modification_file):
                try:
                    existing_df = pd.read_csv(self.modification_file)
                    # Ensure consistent data types before concatenation
                    for col in ['timestamp', 'email_date']:
                        if col in existing_df.columns:
                            existing_df[col] = existing_df[col].astype(str)
                        new_df[col] = new_df[col].astype(str)
                    
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                except Exception as read_error:
                    print(f"⚠️  Error reading existing file, creating new: {read_error}")
                    combined_df = new_df
            else:
                combined_df = new_df
                
            combined_df.to_csv(self.modification_file, index=False)
            print(f"💾 Modification recorded to {self.modification_file}")
            
        except Exception as e:
            print(f"⚠️  Error saving modification record: {e}")
            print("   Continuing without saving to file...")
        
        # Track for session accuracy (this should always work)
        self.session_modifications.append({
            'old_category': old_category,
            'new_category': new_category,
            'timestamp': datetime.now()
        })
    
    def finalize_accuracy_session(self, success_count=None, error_count=None, categories_used=None):
        """Calculate and record accuracy metrics for the completed session"""
        if self.session_total_emails == 0:
            print("⚠️  No emails processed in this session")
            return
            
        # Calculate session metrics
        session_duration = (datetime.now() - self.session_start_time).total_seconds() / 60
        modifications_count = len(self.session_modifications)
        accuracy_rate = self.accuracy_tracker.calculate_accuracy_for_session(
            self.session_total_emails, self.session_modifications
        )
        
        # Analyze modifications by category
        category_modifications = {}
        for mod in self.session_modifications:
            old_cat = mod['old_category']
            category_modifications[old_cat] = category_modifications.get(old_cat, 0) + 1
        
        # Prepare session data
        session_data = {
            'run_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'total_emails': self.session_total_emails,
            'modifications_count': modifications_count,
            'accuracy_rate': accuracy_rate,
            'categories_used': categories_used or 0,
            'errors': error_count or 0,
            'duration_minutes': round(session_duration, 2),
            'category_modifications': category_modifications
        }
        
        # Record accuracy data
        self.accuracy_tracker.record_session_accuracy(session_data)
        self.accuracy_tracker.save_accuracy_summary(session_data)
        
        # Display quick summary
        print(f"Session summary - Processed: {self.session_total_emails}, Corrections: {modifications_count}, Accuracy: {accuracy_rate:.1f}%")
        
        if category_modifications:
            for category, count in sorted(category_modifications.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"   Most corrected: {category.replace('_', ' ').title()}: {count}")
        
        print(f"\n💡 Use 'python show_accuracy_report.py' to see detailed trends")
    
    def show_accuracy_report(self, days_back=30):
        """Display comprehensive accuracy report"""
        self.accuracy_tracker.display_accuracy_report(days_back)
    
    @staticmethod
    def get_available_categories():
        """Get list of available email categories"""
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
