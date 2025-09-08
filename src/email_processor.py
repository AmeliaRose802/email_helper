#!/usr/bin/env python3
"""
Email Processing Engine - Main processing logic and orchestration
"""

from datetime import datetime
from collections import defaultdict


class EmailProcessor:
    def __init__(self, outlook_manager, ai_processor, email_analyzer, summary_generator):
        self.outlook_manager = outlook_manager
        self.ai_processor = ai_processor
        self.email_analyzer = email_analyzer
        self.summary_generator = summary_generator
        
        # Data storage
        self.action_items_data = {
            'required_personal_action': [],
            'team_action': [],
            'optional_action': [],
            'job_listing': [],
            'optional_event': []
        }
        self.email_suggestions = []
    
    def process_emails(self, max_emails=50):
        """Main email processing pipeline"""
        print("🔍 AI SUGGESTIONS PREVIEW")
        print("=" * 60)
        
        # Load learning data
        learning_data = self.ai_processor.load_learning_data()
        
        # Get recent emails
        recent_emails = self.outlook_manager.get_recent_emails(days_back=7, max_emails=max_emails)
        
        # Group emails by conversation thread
        print("🔗 Grouping emails by conversation threads...")
        thread_groups = self.email_analyzer.group_emails_by_thread(recent_emails)
        
        # Select representative email from each thread
        representative_emails = self.email_analyzer.select_thread_representatives(thread_groups, max_emails)
        
        print(f"📊 Analyzing {len(representative_emails)} unique conversations (consolidated from {len(recent_emails)} individual emails)...")
        
        # Reset data storage
        self._reset_data_storage()
        
        # Process each representative email
        categories = defaultdict(list)
        
        for i, email_data in enumerate(representative_emails, 1):
            email = email_data['representative']
            thread_count = email_data['thread_count']
            thread_info = f" (Thread: {thread_count} emails)" if thread_count > 1 else ""
            
            print(f"\n📧 CONVERSATION {i}/{len(representative_emails)}{thread_info}")
            print("=" * 50)
            print(f"Subject: {email.Subject}")
            print(f"From: {email.SenderName}")
            print(f"Date: {email.ReceivedTime.strftime('%Y-%m-%d %H:%M')}")
            
            if thread_count > 1:
                print(f"🔗 Thread Summary: {thread_count} emails in conversation")
                print(f"   Participants: {', '.join(email_data['participants'][:3])}{'...' if len(email_data['participants']) > 3 else ''}")
                print(f"   Latest: {email_data['latest_date'].strftime('%Y-%m-%d %H:%M')}")
            
            # Generate AI summary
            email_content = self._create_email_content_dict(email)
            ai_summary = self.ai_processor.generate_email_summary(email_content)
            if ai_summary:
                print(f"📋 AI Summary: {ai_summary}")
            
            # Classify the email
            suggestion = self.ai_processor.classify_email(email_content, learning_data)
            print(f"🤖 AI Classification: {suggestion.replace('_', ' ').title()}")
            
            # Store email suggestion
            email_suggestion = {
                'email_object': email,
                'ai_suggestion': suggestion,
                'thread_data': email_data
            }
            
            # Process based on category
            self._process_email_by_category(email, email_data, suggestion)
            
            categories[suggestion].append(email)
            self.email_suggestions.append(email_suggestion)
            print("✅ Processing complete")
        
        # Show categorization summary
        self.summary_generator.show_categorization_preview(categories)
        
        return self.email_suggestions
    
    def _reset_data_storage(self):
        """Reset data storage for new processing run"""
        self.action_items_data = {
            'required_personal_action': [],
            'team_action': [],
            'optional_action': [],
            'job_listing': [],
            'optional_event': []
        }
        self.email_suggestions = []
    
    def _create_email_content_dict(self, email):
        """Create standardized email content dictionary"""
        return {
            'subject': email.Subject,
            'sender': email.SenderName,
            'date': email.ReceivedTime.strftime('%Y-%m-%d %H:%M'),
            'body': self.outlook_manager.get_email_body(email)
        }
    
    def _process_email_by_category(self, email, email_data, suggestion):
        """Process email based on its AI-suggested category"""
        # Process action items with detailed output
        if suggestion in ['required_personal_action', 'team_action', 'optional_action']:
            print("🔍 Extracting action item details...")
            
            # For thread processing, analyze the most relevant email in the thread
            analysis_email = self.email_analyzer.get_most_actionable_email(
                email_data.get('thread_emails', [email])
            )
            
            email_content = self._create_email_content_dict(analysis_email)
            
            # Add thread context if available
            thread_count = email_data.get('thread_count', 1)
            if thread_count > 1:
                thread_context = f"\nThread context: {thread_count} emails in conversation with {', '.join(email_data['participants'])}"
                email_content['body'] += thread_context
            
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            action_details = self.ai_processor.extract_action_item_details(email_content, context)
            
            print(f"   • Due Date: {action_details.get('due_date', 'No specific deadline')}")
            print(f"   • Action: {action_details.get('action_required', 'Review email')}")
            if action_details.get('links'):
                print(f"   • Links: {len(action_details['links'])} found")
            
            self.action_items_data[suggestion].append({
                'email_object': email,
                'action_details': action_details,
                'thread_data': email_data
            })
        
        # Process job listings with detailed output
        elif suggestion == 'job_listing':
            print("🔍 Analyzing job qualification match...")
            qualification_match = self.email_analyzer.assess_job_qualification(email.Subject, self.outlook_manager.get_email_body(email))
            due_date = self.email_analyzer.extract_due_date_intelligent(f"{email.Subject} {self.outlook_manager.get_email_body(email)}")
            links = self.email_analyzer.extract_links_intelligent(self.outlook_manager.get_email_body(email))
            
            print(f"   • Match Assessment: {qualification_match}")
            print(f"   • Application Due: {due_date}")
            if links:
                print(f"   • Application Links: {len(links)} found")
            
            job_data = {
                'email_object': email,
                'qualification_match': qualification_match,
                'due_date': due_date,
                'links': links,
                'thread_data': email_data
            }
            self.action_items_data['job_listing'].append(job_data)
        
        # Process optional events with detailed output
        elif suggestion == 'optional_event':
            print("🔍 Analyzing event details and relevance...")
            event_date = self.email_analyzer.extract_due_date_intelligent(f"{email.Subject} {self.outlook_manager.get_email_body(email)}")
            relevance = self.ai_processor.assess_event_relevance(email.Subject, self.outlook_manager.get_email_body(email), self.ai_processor.get_job_context())
            links = self.email_analyzer.extract_links_intelligent(self.outlook_manager.get_email_body(email))
            
            print(f"   • Event Date: {event_date}")
            print(f"   • Relevance: {relevance[:100]}..." if len(relevance) > 100 else f"   • Relevance: {relevance}")
            if links:
                print(f"   • Registration Links: {len(links)} found")
            
            event_data = {
                'email_object': email,
                'date': event_date,
                'relevance': relevance,
                'links': links,
                'thread_data': email_data
            }
            self.action_items_data['optional_event'].append(event_data)
        
        # For other categories, just show basic info
        else:
            if suggestion == 'spam_to_delete':
                print("🗑️  Marked for deletion")
                thread_count = email_data.get('thread_count', 1)
                if thread_count > 1:
                    print(f"   Note: Will handle entire thread ({thread_count} emails)")
            elif suggestion == 'general_information':
                print("ℹ️  Informational content")
                thread_count = email_data.get('thread_count', 1)
                if thread_count > 1:
                    print(f"   Note: Thread summary ({thread_count} emails)")
            else:
                print("📄 Basic categorization")
    
    def generate_summary(self):
        """Generate and display the focused summary"""
        summary_sections = self.summary_generator.build_summary_sections(self.action_items_data)
        
        print("\n" + "=" * 60)
        print("📊 INITIAL SUMMARY")
        print("=" * 60)
        self.summary_generator.display_focused_summary(summary_sections)
        
        # Save summary
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.summary_generator.save_focused_summary(summary_sections, timestamp)
        
        return summary_sections
    
    def get_email_suggestions(self):
        """Get the processed email suggestions"""
        return self.email_suggestions
    
    def get_action_items_data(self):
        """Get the action items data"""
        return self.action_items_data
