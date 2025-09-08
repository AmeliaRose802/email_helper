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


class AIProcessor:
    def __init__(self):
        # Set up paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.prompts_dir = os.path.join(project_root, 'prompts')
        self.user_data_dir = os.path.join(project_root, 'user_specific_data')
        
        # File references (now in user_specific_data)
        self.job_summary_file = os.path.join(self.user_data_dir, 'job_summery.md')
        self.job_skills_file = os.path.join(self.user_data_dir, 'job_skill_summery.md')
        self.job_role_context_file = os.path.join(self.user_data_dir, 'job_role_context.md')
        self.classification_rules_file = os.path.join(self.user_data_dir, 'classification_rules.md')
        self.email_classifier_system_file = 'email_classifier_system.prompty'
        
        # Learning files
        self.learning_file = 'ai_learning_feedback.csv'
        self.modification_file = 'suggestion_modifications.csv'
    
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
        if os.path.exists(self.learning_file):
            return pd.read_csv(self.learning_file)
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
                            
                        print("✅ Using Azure DefaultCredential authentication")
                        
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
    
    def get_classification_rules(self):
        """Get classification rules from file"""
        try:
            if os.path.exists(self.classification_rules_file):
                with open(self.classification_rules_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            else:
                print(f"⚠️  Classification rules file not found: {self.classification_rules_file}")
                print("   Please create user_specific_data/classification_rules.md with your classification rules")
                return "Classification rules unavailable - please create user_specific_data/classification_rules.md"
        except Exception as e:
            print(f"⚠️  Could not load classification rules: {e}")
            return "Classification rules unavailable"
    
    def _create_email_inputs(self, email_content, context):
        """Create input dictionary for prompty execution"""
        return {
            'context': context,
            'job_role_context': self.get_job_role_context(),
            'classification_rules': self.get_classification_rules(),
            'username': self.get_username(),
            'subject': email_content.get('subject', ''),
            'sender': email_content.get('sender', ''),
            'date': email_content.get('date', ''),
            'body': email_content.get('body', '')[:2000]
        }
    
    def classify_email(self, email_content, learning_data):
        """AI-powered email classification using prompty"""
        context = f"""Job Context: {self.get_job_context()}
Skills Profile: {self.get_job_skills()}
Learning History: {len(learning_data)} previous decisions"""
        
        inputs = self._create_email_inputs(email_content, context)
        result = self.execute_prompty(self.email_classifier_system_file, inputs)
        return result.strip().lower() if result else "general_information"
    
    def generate_email_summary(self, email_content):
        """Generate a concise AI summary of an email"""
        try:
            context = f"Job Context: {self.get_job_context()}\nSkills Profile: {self.get_job_skills()}"
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
        email_inputs = {
            'context': context,
            'subject': subject,
            'sender': 'Unknown',
            'body': body[:500]
        }
        
        try:
            result = self.execute_prompty('event_relevance_assessment.prompty', email_inputs)
            return result.strip() if result else "Professional development or networking opportunity"
        except Exception as e:
            print(f"⚠️  AI relevance assessment failed: {e}")
            return "Professional development or networking opportunity"
    
    def save_learning_feedback(self, feedback_entries):
        """Save learning feedback to CSV"""
        new_df = pd.DataFrame(feedback_entries)
        
        if os.path.exists(self.learning_file):
            existing_df = pd.read_csv(self.learning_file)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df
        
        combined_df.to_csv(self.learning_file, index=False)
    
    def record_suggestion_modification(self, email_data, old_category, new_category, user_explanation):
        """Record the suggestion modification to CSV for learning"""
        modification_entry = {
            'timestamp': datetime.now().isoformat(),
            'subject': email_data['subject'],
            'sender': email_data['sender'],
            'email_date': email_data['date'],
            'old_suggestion': old_category,
            'new_suggestion': new_category,
            'user_explanation': user_explanation,
            'body_preview': email_data.get('body', '')[:200]
        }
        
        # Save to CSV
        new_df = pd.DataFrame([modification_entry])
        
        if os.path.exists(self.modification_file):
            existing_df = pd.read_csv(self.modification_file)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df
            
        combined_df.to_csv(self.modification_file, index=False)
        print(f"💾 Modification recorded to {self.modification_file}")
    
    def record_batch_processing(self, success_count, error_count, categories_used):
        """Record batch processing results for learning"""
        batch_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'batch_categorization',
            'emails_processed': success_count + error_count,
            'successful': success_count,
            'errors': error_count,
            'categories_used': categories_used
        }
        
        # Save to existing learning file
        try:
            if os.path.exists(self.learning_file):
                existing_df = pd.read_csv(self.learning_file)
            else:
                existing_df = pd.DataFrame()
                
            batch_df = pd.DataFrame([batch_entry])
            combined_df = pd.concat([existing_df, batch_df], ignore_index=True)
            combined_df.to_csv(self.learning_file, index=False)
            
        except Exception as e:
            print(f"⚠️  Could not record batch processing: {e}")
    
    @staticmethod
    def get_available_categories():
        """Get list of available email categories"""
        return [
            'required_personal_action',
            'team_action', 
            'optional_action',
            'job_listing',
            'optional_event',
            'spam_to_delete',
            'general_information'
        ]
