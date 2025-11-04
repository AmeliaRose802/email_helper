#!/usr/bin/env python3
"""Outlook Manager for Email Helper - Microsoft Outlook COM Integration.

This module provides comprehensive Microsoft Outlook integration using the
COM interface, handling email retrieval, folder management, categorization,
and email operations throughout the email helper application.

The OutlookManager class manages:
- Outlook application connection and initialization
- Email folder creation and organization
- Email retrieval with filtering and sorting
- Email categorization and color coding
- Email movement between folders
- Folder structure management and cleanup

Key Features:
- Robust COM interface handling with error recovery
- Automatic folder creation and organization
- Email categorization with color coding system
- Batch email operations for efficiency
- Cross-folder email movement and organization
- Integration with task completion workflows

Category Mappings:
- INBOX_CATEGORIES: Categories that remain in the inbox
- NON_INBOX_CATEGORIES: Categories moved to organized folders
- CATEGORY_COLORS: Visual color coding for different categories

This module follows the project's Outlook integration patterns and provides
comprehensive error handling for robust operation with the Outlook COM interface.
"""

# Conditional import for Windows-only dependency
try:
    import win32com.client
    import pythoncom
    WIN32COM_AVAILABLE = True
except ImportError:
    WIN32COM_AVAILABLE = False
    # Define dummy for type hints when not available
    win32com = None
    pythoncom = None

from datetime import datetime, timedelta


# Email category folder mappings
INBOX_CATEGORIES = {
    'required_personal_action': 'Required Actions (Me)',
    'optional_action': 'Optional Actions',
    'job_listing': 'Job Listings',
    'work_relevant': 'Work Relevant'
}

NON_INBOX_CATEGORIES = {
    'team_action': 'Team Actions',
    'optional_event': 'Optional Events',
    'fyi': 'FYI',
    'newsletter': 'Newsletters',
    'general_information': 'Summarized',
    'spam_to_delete': 'ai_deleted'
}

CATEGORY_COLORS = {
    'required_personal_action': 'Red Category',
    'team_action': 'Orange Category',
    'optional_action': 'Yellow Category',
    'job_listing': 'Green Category',
    'optional_event': 'Blue Category',
    'fyi': 'Blue Category',
    'newsletter': 'Gray Category',
    'spam_to_delete': 'Purple Category',
    'general_information': 'Gray Category'
}


class OutlookManager:
    def __init__(self):
        if not WIN32COM_AVAILABLE:
            raise ImportError(
                "OutlookManager requires pywin32 package. "
                "This is only available on Windows. "
                "Install it with: pip install pywin32"
            )
        self.outlook = None
        self.namespace = None
        self.inbox = None
        self.folders = {}

    def connect_to_outlook(self):
        """Connect to Outlook application"""
        try:
            # Initialize COM on this thread (required for multi-threaded environments)
            # Use try/except because it might already be initialized
            try:
                pythoncom.CoInitialize()
            except:
                pass  # Already initialized on this thread

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
            print(f"[ERROR] Failed to connect to Outlook: {str(e)}", flush=True)
            raise

    def _setup_outlook_folders(self):
        """Set up Outlook folders for organizing emails with proper hierarchy"""
        try:
            print("\n=== Setting up Outlook folders ===")
            # Get the Inbox folder and main mail root
            inbox_folder = self.inbox
            mail_root = inbox_folder.Parent  # This gets the main Mail folder (parent of Inbox)
            print(f"Inbox: {inbox_folder.Name}")
            print(f"Mail root: {mail_root.Name}")

            print(f"\nCreating {len(INBOX_CATEGORIES)} inbox category folders:")
            # Create inbox folders (actionable items)
            for category, folder_name in INBOX_CATEGORIES.items():
                folder = self._create_folder_if_not_exists(inbox_folder, folder_name)
                self.folders[category] = folder
                if folder:
                    print(f"  [OK] {category} -> {folder.Name} (under Inbox)")
                else:
                    print(f"  [FAIL] {category} -> {folder_name} (failed)")

            print(f"\nCreating {len(NON_INBOX_CATEGORIES)} mail root category folders:")
            # Create non-inbox folders (reference/FYI items) at mail root level
            for category, folder_name in NON_INBOX_CATEGORIES.items():
                folder = self._create_folder_if_not_exists(mail_root, folder_name)
                self.folders[category] = folder
                if folder:
                    print(f"  [OK] {category} -> {folder.Name} (under Mail root)")
                else:
                    print(f"  [FAIL] {category} -> {folder_name} (failed)")

            # Create Done folder at mail root level for completed tasks
            print("\nCreating Done folder:")
            done_folder = self._create_folder_if_not_exists(mail_root, "Done")
            self.folders['done'] = done_folder
            if done_folder:
                print(f"  [OK] done -> {done_folder.Name} (under Mail root)")
            else:
                print("  [FAIL] done -> Done (failed)")

            print(f"\n[OK] Folder setup complete. Total folders in dictionary: {len(self.folders)}")
            print("=== End folder setup ===\n")

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
            print(f"[WARNING] Could not create/access folder '{folder_name}': {e}")
            return None

    def move_email_to_category(self, email, category):
        """Move email to appropriate category folder with location logging"""
        return self._move_to_folder_or_categorize(email, category)

    def _move_to_folder_or_categorize(self, email, category):
        """Handle normal folder moves or categorization fallback"""
        # Normalize category to lowercase for folder lookup
        normalized_category = category.lower()
        if normalized_category not in self.folders or not self.folders[normalized_category]:
            # Fallback: just add category to email if folder not available
            self._add_category_to_email(email, normalized_category)
            return True

        try:
            target_folder = self.folders[normalized_category]
            email.Move(target_folder)

            # Log where the email was moved for user awareness
            folder_location = "Inbox" if self._is_inbox_subfolder(target_folder) else "Mail Root"
            print(f"📁 Moved '{email.Subject[:50]}...' to {target_folder.Name} ({folder_location})")
            return True

        except Exception as e:
            print(f"⚠️  Could not move email: {e}")
            # Fallback: add category instead
            self._add_category_to_email(email, normalized_category)
            return False

    def _is_inbox_subfolder(self, folder):
        """Check if a folder is a subfolder of Inbox"""
        try:
            return folder.Parent.Name == self.inbox.Name
        except:
            return False

    def _add_category_to_email(self, email, category):
        """Add color category to email as fallback"""
        try:
            color_category = CATEGORY_COLORS.get(category, 'Gray Category')
            email.Categories = color_category
            email.Save()
            print(f"🏷️  Tagged '{email.Subject[:50]}...' with {color_category}")

        except Exception as e:
            print(f"⚠️  Could not add category to email: {e}")

    def get_recent_emails(self, days_back=7, max_emails=10000):
        """Get recent emails from inbox"""
        if not self.inbox:
            raise Exception("Not connected to Outlook. Call connect_to_outlook() first.")

        cutoff_date = datetime.now() - timedelta(days=days_back)

        recent_emails = []
        for item in self.inbox.Items:
            try:
                # Only process MailItem objects (Class = 43)
                if hasattr(item, 'Class') and item.Class == 43:
                    if hasattr(item, 'ReceivedTime'):
                        if item.ReceivedTime.replace(tzinfo=None) >= cutoff_date:
                            recent_emails.append(item)
                            if len(recent_emails) >= max_emails * 2:
                                break
            except Exception:
                # Skip items that cause errors
                continue

        return recent_emails[:max_emails * 2]  # Get more emails to account for thread consolidation

    def get_emails_with_full_conversations(self, days_back=7, max_emails=10000):
        """Get recent emails and include their full conversation threads"""
        if not self.inbox:
            raise Exception("Not connected to Outlook. Call connect_to_outlook() first.")

        # Set up date filter
        if days_back is not None:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            extended_cutoff = datetime.now() - timedelta(days=30)
        else:
            cutoff_date = None
            extended_cutoff = None

        try:
            inbox_items = self.inbox.Items
        except Exception as items_error:
            raise Exception(f"Could not access Outlook inbox items: {str(items_error)}")

        recent_emails = []
        all_relevant_emails = []

        # Collect emails with simplified filtering
        for email in inbox_items:
            if not self._is_valid_email_item(email):
                continue

            try:
                email_date = email.ReceivedTime.replace(tzinfo=None)

                # Add to recent if within date range
                if cutoff_date is None or email_date >= cutoff_date:
                    recent_emails.append(email)

                # Add to extended search for thread matching
                if extended_cutoff is None or email_date >= extended_cutoff:
                    all_relevant_emails.append(email)

                # Limit processing to prevent slowdown
                if len(recent_emails) >= max_emails * 2:
                    break

            except Exception:
                continue

        # Limit all_relevant_emails
        all_relevant_emails = all_relevant_emails[:max_emails * 5]

        if not recent_emails:
            return []

        # Group by conversation
        return self._group_emails_by_conversation(recent_emails, all_relevant_emails, max_emails)

    def _is_valid_email_item(self, email):
        """Check if email item is valid for processing"""
        return hasattr(email, 'Class') and email.Class == 43  # olMail = 43

    def _group_emails_by_conversation(self, recent_emails, all_relevant_emails, max_emails):
        """Group emails by conversation with simplified logic"""
        conversation_groups = {}
        processed_conversations = set()

        for email in recent_emails:
            if not self._is_valid_email_item(email):
                continue

            conversation_id = getattr(email, 'ConversationID', f"single_{email.EntryID}")

            if conversation_id in processed_conversations:
                continue

            # Find conversation emails
            if conversation_id.startswith("single_"):
                full_conversation = [email]
            else:
                full_conversation = self._find_conversation_emails(conversation_id, all_relevant_emails)
                if not full_conversation:
                    full_conversation = [email]
                    conversation_id = f"single_{email.EntryID}"

            if full_conversation:
                full_conversation.sort(key=lambda x: x.ReceivedTime)

                conversation_groups[conversation_id] = {
                    'emails': full_conversation,
                    'topic': getattr(email, 'ConversationTopic', None) or email.Subject,
                    'latest_date': max(e.ReceivedTime for e in full_conversation),
                    'recent_trigger': email
                }
                processed_conversations.add(conversation_id)

        # Sort and limit results
        sorted_conversations = sorted(
            conversation_groups.items(),
            key=lambda x: x[1]['latest_date'],
            reverse=True
        )

        return sorted_conversations[:max_emails]

    def _find_conversation_emails(self, conversation_id, all_emails):
        """Find all emails matching a conversation ID"""
        conversation = []
        for email in all_emails:
            if (self._is_valid_email_item(email) and
                hasattr(email, 'ConversationID') and
                email.ConversationID == conversation_id):
                conversation.append(email)
        return conversation

    def get_email_body(self, email):
        """Get email body safely with larger context window"""
        return email.Body[:5000] if email.Body else ""

    def apply_categorization_batch(self, email_suggestions, confirmation_callback=None):
        """Apply categorization to a batch of emails with improved folder organization"""
        if not email_suggestions:
            print("❌ No email suggestions to process.")
            return 0, 0

        # Show folder organization info
        print("\n📂 FOLDER ORGANIZATION:")
        print("   🎯 INBOX (Actionable): Required Actions, Optional Actions, Job Listings, Work Relevant")
        print("   📚 OUTSIDE INBOX (Reference): Team Actions, Optional Events, FYI, Newsletters")
        print()

        # Ask for confirmation if callback provided
        if confirmation_callback and not confirmation_callback(len(email_suggestions)):
            print("❌ Categorization cancelled.")
            return 0, 0

        # Track results
        success_count = 0
        error_count = 0
        inbox_count = 0
        non_inbox_count = 0

        for i, suggestion_data in enumerate(email_suggestions, 1):
            email = suggestion_data['email_object']
            category = suggestion_data['ai_suggestion']
            thread_data = suggestion_data.get('thread_data', {})

            # Count folder destinations (case-insensitive)
            if category.lower() in NON_INBOX_CATEGORIES:
                non_inbox_count += 1
            else:
                inbox_count += 1

            # Show processing details
            subject = email.Subject[:50] if hasattr(email, 'Subject') else 'Unknown'
            print(f"   📧 {subject}... → {category.replace('_', ' ').title()}")

            # Get all emails in thread
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
                try:
                    if self.move_email_to_category(email, category):
                        success_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    print(f"❌ Error processing email: {e}")
                    error_count += 1

        print("\n✅ CATEGORIZATION COMPLETE:")
        print(f"   📊 Total processed: {success_count} emails")
        print(f"   🎯 Remaining in Inbox: {inbox_count} emails (actionable items)")
        print(f"   📚 Moved outside Inbox: {non_inbox_count} emails (reference/FYI items)")
        if error_count > 0:
            print(f"   ❌ Errors encountered: {error_count} emails")

        return success_count, error_count

    def move_emails_to_done_folder(self, entry_ids):
        """Move emails with specified EntryIDs to the Done folder"""
        if not self.namespace:
            raise Exception("Not connected to Outlook. Call connect_to_outlook() first.")

        if not entry_ids:
            return 0, 0

        done_folder = self.folders.get('done')
        if not done_folder:
            print("⚠️ Done folder not available. Cannot move emails.")
            return 0, len(entry_ids)

        success_count = 0
        error_count = 0

        for entry_id in entry_ids:
            try:
                # Get the email using its EntryID
                email_item = self.namespace.GetItemFromID(entry_id)

                if email_item:
                    # Move to Done folder
                    email_item.Move(done_folder)
                    subject = email_item.Subject[:50] if hasattr(email_item, 'Subject') else 'Unknown'
                    print(f"✅ Moved '{subject}...' to Done folder")
                    success_count += 1
                else:
                    print(f"⚠️ Email with EntryID {entry_id} not found")
                    error_count += 1

            except Exception as e:
                print(f"❌ Error moving email {entry_id} to Done folder: {e}")
                error_count += 1

        if success_count > 0:
            print(f"📁 Moved {success_count} emails to Done folder")
        if error_count > 0:
            print(f"⚠️ Failed to move {error_count} emails")

        return success_count, error_count
