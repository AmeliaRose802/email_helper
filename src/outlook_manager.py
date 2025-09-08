#!/usr/bin/env python3
"""
Outlook Manager - Handles Outlook connection and folder management
"""

import win32com.client
import os
from datetime import datetime


class OutlookManager:
    def __init__(self):
        self.outlook = None
        self.namespace = None
        self.inbox = None
        self.folders = {}
        
    def connect_to_outlook(self):
        """Connect to Outlook application"""
        print("🔗 Connecting to Outlook...")
        self.outlook = win32com.client.Dispatch("Outlook.Application")
        self.namespace = self.outlook.GetNamespace("MAPI")
        self.inbox = self.namespace.GetDefaultFolder(6)
        
        # Set up folder structure for email organization
        self._setup_outlook_folders()
        print("✅ Connected to Outlook successfully")
    
    def _setup_outlook_folders(self):
        """Set up Outlook folders for organizing emails"""
        try:
            # Get the Inbox folder as the root for our organization
            inbox_folder = self.inbox
            
            # Folder mapping for categories - all under Inbox
            folder_names = {
                'required_personal_action': 'Required Actions (Me)',
                'team_action': 'Team Actions', 
                'optional_action': 'Optional Actions',
                'job_listing': 'Job Listings',  # Use existing Job Listings folder
                'optional_event': 'Optional Events',
                'spam_to_delete': 'ai_deleted',  # Use existing ai_deleted folder
                'general_information': 'Summarized'  # Use existing Summarized folder
            }
            
            # Create folders if they don't exist (all under Inbox)
            for category, folder_name in folder_names.items():
                folder = self._create_folder_if_not_exists(inbox_folder, folder_name)
                self.folders[category] = folder
                
            print("✅ Outlook folder structure ready under Inbox")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not set up Outlook folders: {e}")
            print("   Emails will be categorized but not moved to folders")
            
    def _create_folder_if_not_exists(self, parent_folder, folder_name):
        """Create folder under parent if it doesn't exist"""
        try:
            # Try to find existing folder
            for folder in parent_folder.Folders:
                if folder.Name == folder_name:
                    print(f"📁 Found existing folder: {folder_name}")
                    return folder
            
            # Create if not found
            new_folder = parent_folder.Folders.Add(folder_name)
            print(f"📁 Created new folder: {folder_name}")
            return new_folder
                    
        except Exception as e:
            print(f"⚠️  Could not create/access folder '{folder_name}': {e}")
            return None
    
    def move_email_to_category(self, email, category):
        """Move email to appropriate category folder"""
        if category not in self.folders or not self.folders[category]:
            # Fallback: just add category to email if folder not available
            self._add_category_to_email(email, category)
            return True
            
        try:
            target_folder = self.folders[category]
            email.Move(target_folder)
            print(f"📧 Moved '{email.Subject[:50]}...' to {category.replace('_', ' ').title()}")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not move email: {e}")
            # Fallback: add category instead
            self._add_category_to_email(email, category)
            return False
            
    def _add_category_to_email(self, email, category):
        """Add color category to email as fallback"""
        try:
            # Outlook category colors mapping
            category_colors = {
                'required_personal_action': 'Red Category',
                'team_action': 'Orange Category', 
                'optional_action': 'Yellow Category',
                'job_listing': 'Green Category',
                'optional_event': 'Blue Category',
                'spam_to_delete': 'Purple Category',
                'general_information': 'Gray Category'
            }
            
            color_category = category_colors.get(category, 'Gray Category')
            email.Categories = color_category
            email.Save()
            print(f"🏷️  Tagged '{email.Subject[:50]}...' with {color_category}")
            
        except Exception as e:
            print(f"⚠️  Could not add category to email: {e}")
    
    def get_recent_emails(self, days_back=7, max_emails=100):
        """Get recent emails from inbox"""
        if not self.inbox:
            raise Exception("Not connected to Outlook. Call connect_to_outlook() first.")
            
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        recent_emails = [
            email for email in self.inbox.Items
            if email.ReceivedTime.replace(tzinfo=None) >= cutoff_date
        ][:max_emails * 2]  # Get more emails to account for thread consolidation
        
        return recent_emails
    
    def get_email_body(self, email):
        """Get email body safely"""
        return email.Body[:1000] if email.Body else ""
    
    def apply_categorization_batch(self, email_suggestions, confirmation_callback=None):
        """Apply categorization to a batch of emails"""
        if not email_suggestions:
            print("❌ No email suggestions to process.")
            return 0, 0
            
        print(f"\n📧 APPLYING CATEGORIZATION TO {len(email_suggestions)} EMAILS")
        print("=" * 60)
        
        # Ask for confirmation if callback provided
        if confirmation_callback and not confirmation_callback(len(email_suggestions)):
            print("❌ Categorization cancelled.")
            return 0, 0
            
        # Track results
        success_count = 0
        error_count = 0
        
        for i, suggestion_data in enumerate(email_suggestions, 1):
            email = suggestion_data['email_object']
            category = suggestion_data['ai_suggestion']
            thread_data = suggestion_data.get('thread_data', {})
            thread_emails = thread_data.get('thread_emails', [email])
            
            if len(thread_emails) > 1:
                print(f"\n📧 Processing THREAD {i}/{len(email_suggestions)}: {email.Subject[:50]}...")
                print(f"   Category: {category.replace('_', ' ').title()}")
                print(f"   Thread size: {len(thread_emails)} emails")
                
                # Move all emails in the thread
                thread_success = 0
                for thread_email in thread_emails:
                    try:
                        if self.move_email_to_category(thread_email, category):
                            thread_success += 1
                        else:
                            error_count += 1
                    except Exception as e:
                        print(f"❌ Error processing thread email: {e}")
                        error_count += 1
                
                if thread_success == len(thread_emails):
                    success_count += 1
                    print(f"✅ Moved entire thread ({len(thread_emails)} emails)")
                else:
                    print(f"⚠️  Partially moved thread ({thread_success}/{len(thread_emails)} emails)")
            else:
                print(f"\n📧 Processing {i}/{len(email_suggestions)}: {email.Subject[:50]}...")
                print(f"   Category: {category.replace('_', ' ').title()}")
                
                try:
                    if self.move_email_to_category(email, category):
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    print(f"❌ Error processing email: {e}")
                    error_count += 1
        
        print(f"\n✅ CATEGORIZATION COMPLETE")
        print(f"   Successfully processed: {success_count} emails")
        if error_count > 0:
            print(f"   Errors encountered: {error_count} emails")
        print(f"   Check your Inbox subfolders for organized emails!")
        
        return success_count, error_count
