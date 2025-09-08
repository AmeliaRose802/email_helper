#!/usr/bin/env python3
"""
User Interface - Handles user interaction, editing, and menu systems
"""

from datetime import datetime


class UserInterface:
    def __init__(self, ai_processor, outlook_manager, summary_generator):
        self.ai_processor = ai_processor
        self.outlook_manager = outlook_manager
        self.summary_generator = summary_generator
        self.email_suggestions = []
        self.action_items_data = {}
    
    def get_max_emails_from_user(self, default=50, max_limit=200):
        """Get the number of emails to process from user input"""
        while True:
            try:
                max_emails_input = input(f"\nHow many emails would you like to process? (default: {default}, max: {max_limit}): ").strip()
                
                if not max_emails_input:
                    return default  # Default
                
                max_emails = int(max_emails_input)
                
                if max_emails <= 0:
                    print("❌ Please enter a positive number.")
                    continue
                elif max_emails > max_limit:
                    print(f"⚠️  Processing more than {max_limit} emails may take a very long time. Limiting to {max_limit}.")
                    return max_limit
                else:
                    return max_emails
                    
            except ValueError:
                print("❌ Please enter a valid number.")
                continue
    
    def offer_editing_options(self):
        """Offer user the option to edit AI suggestions"""
        print("\n" + "=" * 60)
        print("✏️  EDIT SUGGESTIONS")
        print("=" * 60)
        
        while True:
            print("\nWould you like to edit any AI suggestions?")
            print("1. ✏️  Edit a suggestion by number")
            print("2. 📋 View all suggestions") 
            print("3. ✅ Apply categorization to Outlook")
            print("4. � Show accuracy report")
            print("5. �🚪 Continue (accept all suggestions)")
            print("6. 🛑 Quit")
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '1':
                self._handle_edit_suggestion()
            elif choice == '2':
                self.summary_generator.display_suggestions_for_editing(self.email_suggestions)
            elif choice == '3':
                self._apply_categorization_to_outlook()
            elif choice == '4':
                self._show_accuracy_report()
            elif choice == '5':
                print("✅ Continuing with current suggestions...")
                break
            elif choice == '6':
                print("🛑 Exiting program...")
                exit(0)
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")
    
    def _apply_categorization_to_outlook(self):
        """Apply the current categorization to emails in Outlook"""
        if not self.email_suggestions:
            print("❌ No email suggestions available.")
            return
            
        def confirmation_callback(email_count):
            print(f"This will organize {email_count} emails based on AI suggestions.")
            print("Actions will include:")
            print("  • Moving emails to category folders under Inbox")
            print("  • Adding color categories as backup")
            print("  • Moving spam/irrelevant emails to 'ai_deleted' folder")
            
            confirm = input("\nDo you want to proceed? (y/N): ").strip().lower()
            return confirm == 'y'
            
        success_count, error_count = self.outlook_manager.apply_categorization_batch(
            self.email_suggestions, 
            confirmation_callback
        )
        
        # Record the batch processing
        categories_used = len(set(s['ai_suggestion'] for s in self.email_suggestions))
        self.ai_processor.record_batch_processing(success_count, error_count, categories_used)
    
    def _show_accuracy_report(self):
        """Display accuracy report to the user"""
        print("\n" + "=" * 60)
        print("📊 ACCURACY REPORT")
        print("=" * 60)
        
        try:
            # Show recent accuracy trends
            self.ai_processor.show_accuracy_report(days_back=14)  # Last 2 weeks
            
            input("\n📖 Press Enter to continue...")
            
        except Exception as e:
            print(f"❌ Could not generate accuracy report: {e}")
            print("This might be the first run or there's insufficient data.")
            input("\nPress Enter to continue...")
    
    def _handle_edit_suggestion(self):
        """Handle the process of editing a single suggestion"""
        if not self.summary_generator.display_suggestions_for_editing(self.email_suggestions):
            return
            
        try:
            email_num = int(input(f"\nEnter email number to edit (1-{len(self.email_suggestions)}): ").strip())
        except ValueError:
            print("❌ Please enter a valid number.")
            return
            
        if email_num < 1 or email_num > len(self.email_suggestions):
            print(f"❌ Please enter a number between 1 and {len(self.email_suggestions)}.")
            return
            
        # Show current email details
        suggestion_data = self.email_suggestions[email_num - 1]
        email = suggestion_data['email_object']
        current_category = suggestion_data['ai_suggestion']
        
        print(f"\n📧 EDITING EMAIL #{email_num}")
        print("-" * 40)
        print(f"Subject: {email.Subject}")
        print(f"From: {email.SenderName}")
        print(f"Current category: {current_category.replace('_', ' ').title()}")
        
        body_preview = self.outlook_manager.get_email_body(email)[:300]
        if body_preview:
            print(f"Preview: {body_preview}...")
            
        # Show available categories
        categories = self.ai_processor.get_available_categories()
        print(f"\nAvailable categories:")
        for i, cat in enumerate(categories, 1):
            marker = "👈 CURRENT" if cat == current_category else ""
            print(f"{i}. {cat.replace('_', ' ').title()} {marker}")
            
        try:
            cat_choice = int(input(f"\nChoose new category (1-{len(categories)}): ").strip())
        except ValueError:
            print("❌ Please enter a valid number.")
            return
            
        if cat_choice < 1 or cat_choice > len(categories):
            print(f"❌ Please enter a number between 1 and {len(categories)}.")
            return
            
        new_category = categories[cat_choice - 1]
        
        if new_category == current_category:
            print("ℹ️  Same category selected. No change needed.")
            return
            
        # Get user explanation
        explanation = input("\nWhy are you changing this categorization? (for learning): ").strip()
        if not explanation:
            explanation = "User correction - no explanation provided"
            
        # Apply the edit
        if self.edit_suggestion(email_num, new_category, explanation):
            print(f"\n🔄 Regenerating summary with your changes...")
            self.regenerate_summary_after_edits()
    
    def edit_suggestion(self, email_index, new_category, user_explanation):
        """Edit a specific email suggestion and update all related data"""
        if not self.email_suggestions:
            print("❌ No email suggestions available.")
            return False
            
        if email_index < 1 or email_index > len(self.email_suggestions):
            print("❌ Invalid email number.")
            return False
            
        # Get the email suggestion
        suggestion_data = self.email_suggestions[email_index - 1]
        email = suggestion_data['email_object']
        old_category = suggestion_data['ai_suggestion']
        
        if new_category not in self.ai_processor.get_available_categories():
            print(f"❌ Invalid category. Available: {', '.join(self.ai_processor.get_available_categories())}")
            return False
            
        print(f"✏️  Updating email #{email_index}: '{email.Subject}'")
        print(f"    From: {old_category.replace('_', ' ').title()}")
        print(f"    To: {new_category.replace('_', ' ').title()}")
        
        # Update the suggestion
        suggestion_data['ai_suggestion'] = new_category
        
        # Remove from old category in action_items_data
        self._remove_from_action_data(email, old_category)
        
        # Add to new category in action_items_data
        self._add_to_action_data(email, new_category)
        
        # Move the email in Outlook immediately
        print("📧 Moving email to new category...")
        self.outlook_manager.move_email_to_category(email, new_category)
        
        # Record the modification
        email_data = {
            'subject': email.Subject,
            'sender': email.SenderName,
            'date': email.ReceivedTime.strftime('%Y-%m-%d %H:%M'),
            'body': self.outlook_manager.get_email_body(email)
        }
        self.ai_processor.record_suggestion_modification(email_data, old_category, new_category, user_explanation)
        
        print("✅ Suggestion updated successfully!")
        return True
    
    def _remove_from_action_data(self, email, category):
        """Remove email from action_items_data category"""
        if category in self.action_items_data:
            # Remove entries that match this email
            self.action_items_data[category] = [
                item for item in self.action_items_data[category]
                if item['email_object'].Subject != email.Subject or 
                   item['email_object'].SenderName != email.SenderName
            ]
    
    def _add_to_action_data(self, email, new_category):
        """Add email to action_items_data in new category"""
        if new_category not in self.action_items_data:
            self.action_items_data[new_category] = []
            
        # Process the email for the new category
        if new_category in ['required_personal_action', 'team_action', 'optional_action']:
            email_content = {
                'subject': email.Subject,
                'sender': email.SenderName,
                'date': email.ReceivedTime.strftime('%Y-%m-%d %H:%M'),
                'body': self.outlook_manager.get_email_body(email)
            }
            
            context = f"Job Context: {self.ai_processor.get_job_context()}\nSkills Profile: {self.ai_processor.get_job_skills()}"
            action_details = self.ai_processor.extract_action_item_details(email_content, context)
            
            self.action_items_data[new_category].append({
                'email_object': email,
                'action_details': action_details
            })
            
        elif new_category == 'job_listing':
            from .email_analyzer import EmailAnalyzer
            analyzer = EmailAnalyzer(self.ai_processor)
            
            job_data = {
                'email_object': email,
                'qualification_match': analyzer.assess_job_qualification(email.Subject, self.outlook_manager.get_email_body(email)),
                'due_date': analyzer.extract_due_date_intelligent(f"{email.Subject} {self.outlook_manager.get_email_body(email)}"),
                'links': analyzer.extract_links_intelligent(self.outlook_manager.get_email_body(email))
            }
            self.action_items_data[new_category].append(job_data)
            
        elif new_category == 'optional_event':
            from .email_analyzer import EmailAnalyzer
            analyzer = EmailAnalyzer(self.ai_processor)
            
            event_data = {
                'email_object': email,
                'date': analyzer.extract_due_date_intelligent(f"{email.Subject} {self.outlook_manager.get_email_body(email)}"),
                'relevance': self.ai_processor.assess_event_relevance(email.Subject, self.outlook_manager.get_email_body(email), self.ai_processor.get_job_context()),
                'links': analyzer.extract_links_intelligent(self.outlook_manager.get_email_body(email))
            }
            self.action_items_data[new_category].append(event_data)
    
    def regenerate_summary_after_edits(self):
        """Regenerate summary sections after suggestions have been edited"""
        if not self.action_items_data:
            print("❌ No action items data available.")
            return
            
        # Generate focused summary using updated data
        summary_sections = self.summary_generator.build_summary_sections(self.action_items_data)
        
        print("\n" + "=" * 60)
        print("📊 UPDATED SUMMARY")
        print("=" * 60)
        self.summary_generator.display_focused_summary(summary_sections)
        
        # Save updated summary
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.summary_generator.save_focused_summary(summary_sections, timestamp)
    
    def set_email_suggestions(self, email_suggestions):
        """Set the email suggestions for editing"""
        self.email_suggestions = email_suggestions
    
    def set_action_items_data(self, action_items_data):
        """Set the action items data for editing"""
        self.action_items_data = action_items_data
