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
        try:
            self.outlook = win32com.client.Dispatch("Outlook.Application")
            self.namespace = self.outlook.GetNamespace("MAPI")
            
            # Test accessing the default folder before storing it
            inbox = self.namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
            
            # Try to access the Items property to verify it works
            try:
                _ = inbox.Items.Count  # This will trigger the error if there is one
            except Exception as items_error:
                raise Exception(f"Cannot access inbox items: {str(items_error)}")
            
            self.inbox = inbox
            
            # Set up folder structure for email organization
            self._setup_outlook_folders()
            
        except Exception as e:
            print(f"❌ Failed to connect to Outlook: {str(e)}")
            raise
    
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
                'work_relevant': 'Work Relevant',
                'fyi': 'FYI',
                'newsletter': 'Newsletters',
                'spam_to_delete': 'ai_deleted',  # Use existing ai_deleted folder
                'general_information': 'Summarized'  # Use existing Summarized folder
            }
            
            # Create folders if they don't exist (all under Inbox)
            for category, folder_name in folder_names.items():
                folder = self._create_folder_if_not_exists(inbox_folder, folder_name)
                self.folders[category] = folder
                
        except Exception as e:
            print(f"⚠️  Warning: Could not set up Outlook folders: {e}")
            print("   Emails will be categorized but not moved to folders")
            
    def _create_folder_if_not_exists(self, parent_folder, folder_name):
        """Create folder under parent if it doesn't exist"""
        try:
            # Try to find existing folder
            for folder in parent_folder.Folders:
                if folder.Name == folder_name:
                    return folder
            
            # Create if not found
            new_folder = parent_folder.Folders.Add(folder_name)
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
    
    def get_conversation_emails(self, conversation_id):
        """Get all emails in a conversation using ConversationID"""
        if not self.inbox:
            raise Exception("Not connected to Outlook")
            
        try:
            # Search all emails in inbox with the same ConversationID
            conversation_emails = []
            
            # Iterate through all emails to find matching ConversationID
            # (Restrict method syntax is problematic with ConversationID)
            for item in self.inbox.Items:
                try:
                    # Only include MailItem objects (not meeting requests, etc.)
                    if item.Class == 43:  # olMail = 43
                        if hasattr(item, 'ConversationID') and item.ConversationID == conversation_id:
                            conversation_emails.append(item)
                except:
                    # Skip items that can't be accessed
                    continue
            
            # Sort by received time (oldest first)
            conversation_emails.sort(key=lambda x: x.ReceivedTime)
            return conversation_emails
            
        except Exception as e:
            print(f"⚠️  Warning: Could not retrieve conversation emails for {conversation_id}: {e}")
            return []
    
    def get_emails_with_full_conversations(self, days_back=7, max_emails=100):
        """Get recent emails and include their full conversation threads"""
        if not self.inbox:
            raise Exception("Not connected to Outlook. Call connect_to_outlook() first.")
            
        from datetime import timedelta
        
        # If days_back is None, don't apply any date filter
        if days_back is not None:
            cutoff_date = datetime.now() - timedelta(days=days_back)
        else:
            cutoff_date = None
        
        try:
            # Get recent emails as starting point - use simpler approach
            
            recent_emails = []
            all_relevant_emails = []
            
            # Access inbox items safely with proper error handling
            try:
                inbox_items = self.inbox.Items
            except Exception as items_error:
                raise Exception(f"Could not access Outlook inbox items: {str(items_error)}")
            
            # Simple iteration approach that was working before
            for email in inbox_items:
                try:
                    # Skip if not a mail item
                    if not hasattr(email, 'Class') or email.Class != 43:  # olMail = 43
                        continue
                    
                    # Check recent emails
                    if hasattr(email, 'ReceivedTime'):
                        email_date = email.ReceivedTime.replace(tzinfo=None)
                        
                        # Apply date filter only if cutoff_date is set
                        if cutoff_date is None or email_date >= cutoff_date:
                            recent_emails.append(email)
                        
                        # Also collect for extended search (30 days or all if no cutoff)
                        if cutoff_date is None:
                            all_relevant_emails.append(email)
                        else:
                            extended_cutoff = datetime.now() - timedelta(days=30)
                            if email_date >= extended_cutoff:
                                all_relevant_emails.append(email)
                    
                    # Limit to prevent excessive processing
                    if len(recent_emails) >= max_emails * 2:
                        break
                        
                except Exception as item_error:
                    # Skip problematic items and continue
                    continue
            
            # Limit all_relevant_emails as well
            all_relevant_emails = all_relevant_emails[:max_emails * 5]
            
            if not recent_emails:
                print("⚠️  No recent emails found in the specified time range")
                return []
        
        except Exception as access_error:
            raise Exception(f"Failed to access Outlook emails: {str(access_error)}")
        
        # Group by conversation using all available emails
        conversation_groups = {}
        processed_conversations = set()
        
        for email in recent_emails:
            try:
                # Ensure email is a mail item
                if not hasattr(email, 'Class') or email.Class != 43:  # olMail = 43
                    continue
                    
                conversation_id = email.ConversationID if hasattr(email, 'ConversationID') else f"single_{email.EntryID}"
                
                # Skip if we've already processed this conversation
                if conversation_id in processed_conversations:
                    continue
                
                # Find all emails with same ConversationID in our broader set
                full_conversation = []
                if conversation_id.startswith("single_"):
                    # This is a fallback single email
                    full_conversation = [email]
                else:
                    # Look for conversation matches
                    for e in all_relevant_emails:
                        try:
                            if (hasattr(e, 'ConversationID') and 
                                hasattr(e, 'Class') and 
                                e.Class == 43 and  # Only mail items
                                e.ConversationID == conversation_id):
                                full_conversation.append(e)
                        except:
                            # Skip emails that can't be accessed
                            continue
                    
                    # If no conversation emails found, treat as single email
                    if not full_conversation:
                        full_conversation = [email]
                        conversation_id = f"single_{email.EntryID}"
                
                if full_conversation:
                    # Sort by date
                    full_conversation.sort(key=lambda x: x.ReceivedTime)
                    
                    conversation_groups[conversation_id] = {
                        'emails': full_conversation,
                        'topic': getattr(email, 'ConversationTopic', None) or email.Subject,
                        'latest_date': max(e.ReceivedTime for e in full_conversation),
                        'recent_trigger': email  # The recent email that triggered including this conversation
                    }
                    processed_conversations.add(conversation_id)
                    
            except Exception as e:
                # Fallback: treat as single email if conversation API fails
                print(f"⚠️  Warning: Could not process conversation for '{email.Subject[:50]}': {e}")
                fallback_id = f"single_{email.EntryID}"
                conversation_groups[fallback_id] = {
                    'emails': [email],
                    'topic': email.Subject,
                    'latest_date': email.ReceivedTime,
                    'recent_trigger': email
                }
        
        # Sort conversations by latest activity
        sorted_conversations = sorted(
            conversation_groups.items(),
            key=lambda x: x[1]['latest_date'],
            reverse=True
        )
        
        return sorted_conversations[:max_emails]
    
    def get_email_body(self, email):
        """Get email body safely"""
        return email.Body[:1000] if email.Body else ""
    
    def apply_categorization_batch(self, email_suggestions, confirmation_callback=None):
        """Apply categorization to a batch of emails"""
        if not email_suggestions:
            print("❌ No email suggestions to process.")
            return 0, 0
            
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
            
            # Get all emails in thread (use new structure)
            all_emails = thread_data.get('all_emails', [email])
            thread_count = thread_data.get('thread_count', 1)
            
            if thread_count > 1:
                # Move all emails in the thread
                thread_success = 0
                for thread_email in all_emails:
                    try:
                        if self.move_email_to_category(thread_email, category):
                            thread_success += 1
                        else:
                            error_count += 1
                    except Exception as e:
                        print(f"❌ Error processing thread email: {e}")
                        error_count += 1
                
                if thread_success == len(all_emails):
                    success_count += 1
                else:
                    pass  # Partially moved thread
            else:
                print(f"   Category: {category.replace('_', ' ').title()}")
                
                try:
                    if self.move_email_to_category(email, category):
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    print(f"❌ Error processing email: {e}")
                    error_count += 1
        
        print(f"\n✅ CATEGORIZATION COMPLETE - Successfully processed: {success_count} emails")
        if error_count > 0:
            print(f"   Errors encountered: {error_count} emails")
        
        return success_count, error_count
