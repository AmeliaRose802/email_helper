"""Outlook Email Adapter for Backend Integration.

This adapter wraps OutlookManager to provide a standardized EmailProvider
interface for the backend API, enabling seamless integration without
duplicating functionality.

The adapter handles:
- Email retrieval with pagination
- Email folder operations
- Email movement and categorization
- Email body content access
- COM object to dictionary conversion
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
from pathlib import Path

# Ensure src directory is in path
src_dir = str(Path(__file__).parent.parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Now import from src directory
from outlook_manager import OutlookManager
from core.interfaces import EmailProvider


class OutlookEmailAdapter(EmailProvider):
    """Adapter wrapping OutlookManager to implement EmailProvider interface.
    
    This adapter delegates email operations to the existing OutlookManager
    implementation, providing a standardized interface for the backend API.
    
    Attributes:
        outlook_manager (OutlookManager): Wrapped Outlook COM interface
        connected (bool): Connection status to Outlook application
        outlook: Direct reference to Outlook COM object (for advanced operations)
    """
    
    def __init__(self, outlook_manager: Optional[OutlookManager] = None):
        """Initialize the adapter.
        
        Args:
            outlook_manager: Optional OutlookManager instance. If not provided,
                           a new instance will be created.
        """
        self.outlook_manager = outlook_manager or OutlookManager()
        self.connected = False
        self.outlook = None  # Will be set after connection
    
    def connect(self) -> bool:
        """Establish connection to Outlook.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.outlook_manager.connect_to_outlook()
            self.connected = True
            self.outlook = self.outlook_manager.outlook
            return True
        except Exception as e:
            print(f"Failed to connect to Outlook: {e}")
            self.connected = False
            return False
    
    def get_emails(
        self, 
        folder_name: str = "Inbox", 
        count: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve emails from the specified folder.
        
        Args:
            folder_name: Name of the Outlook folder to retrieve from
            count: Maximum number of emails to retrieve
            offset: Number of emails to skip (for pagination)
        
        Returns:
            List of email dictionaries with standardized fields
        
        Raises:
            RuntimeError: If not connected to Outlook
        """
        if not self.connected:
            raise RuntimeError("Not connected to Outlook. Call connect() first.")
        
        try:
            # Get emails from OutlookManager
            # For large counts, fetch ALL emails without date restrictions
            # For smaller counts, use reasonable time windows
            days_back = None if count >= 50000 else (365 if count >= 1000 else 30)
            emails = self.outlook_manager.get_recent_emails(
                days_back=days_back,
                max_emails=count + offset
            )
            
            # Convert to standardized format with pagination
            result = []
            for i, email in enumerate(emails):
                # Skip emails before offset
                if i < offset:
                    continue
                
                # Stop when we reach count
                if len(result) >= count:
                    break
                
                try:
                    email_dict = self._email_to_dict(email)
                    result.append(email_dict)
                except Exception as e:
                    print(f"Error converting email: {e}")
                    continue
            
            return result
            
        except Exception as e:
            print(f"Error retrieving emails: {e}")
            return []
    
    def move_email(self, email_id: str, destination_folder: str) -> bool:
        """Move an email to the specified folder.
        
        Args:
            email_id: EntryID of the email to move
            destination_folder: Name of the destination folder
        
        Returns:
            True if move successful, False otherwise
        
        Raises:
            RuntimeError: If not connected to Outlook
        """
        if not self.connected:
            raise RuntimeError("Not connected to Outlook. Call connect() first.")
        
        try:
            # Get the email item by ID
            email = self.outlook_manager.namespace.GetItemFromID(email_id)
            
            # Use OutlookManager's move logic
            return self.outlook_manager.move_email_to_category(email, destination_folder)
            
        except Exception as e:
            print(f"Error moving email: {e}")
            return False
    
    def get_email_body(self, email_id: str) -> str:
        """Get the full body text of an email.
        
        Args:
            email_id: EntryID of the email
        
        Returns:
            Email body text (plain text or HTML)
        
        Raises:
            RuntimeError: If not connected to Outlook
        """
        if not self.connected:
            raise RuntimeError("Not connected to Outlook. Call connect() first.")
        
        try:
            # Get the email item by ID
            email = self.outlook_manager.namespace.GetItemFromID(email_id)
            
            # Try HTML first to preserve img alt text, fallback to plain text
            body = getattr(email, 'HTMLBody', '')
            if not body:
                body = getattr(email, 'Body', '')
            
            return body
            
        except Exception as e:
            print(f"Error retrieving email body: {e}")
            return ""
    
    def get_folders(self) -> List[Dict[str, str]]:
        """List available email folders.
        
        Returns:
            List of folder dictionaries with id, name, and type
        
        Raises:
            RuntimeError: If not connected to Outlook
        """
        if not self.connected:
            raise RuntimeError("Not connected to Outlook. Call connect() first.")
        
        try:
            folders = []
            
            # Get default folders
            inbox = self.outlook_manager.inbox
            if inbox:
                folders.append({
                    'id': inbox.EntryID,
                    'name': inbox.Name,
                    'type': 'inbox'
                })
            
            # Get custom folders from OutlookManager
            for category, folder in self.outlook_manager.folders.items():
                if folder:
                    folders.append({
                        'id': folder.EntryID,
                        'name': folder.Name,
                        'type': category
                    })
            
            return folders
            
        except Exception as e:
            print(f"Error listing folders: {e}")
            return []
    
    def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read.
        
        Args:
            email_id: EntryID of the email
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            RuntimeError: If not connected to Outlook
        """
        if not self.connected:
            raise RuntimeError("Not connected to Outlook. Call connect() first.")
        
        try:
            email = self.outlook_manager.namespace.GetItemFromID(email_id)
            email.UnRead = False
            email.Save()
            return True
        except Exception as e:
            print(f"Error marking email as read: {e}")
            return False
    
    def categorize_email(self, email_id: str, category: str) -> bool:
        """Apply a category to an email.
        
        Args:
            email_id: EntryID of the email
            category: Category to apply
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            RuntimeError: If not connected to Outlook
        """
        if not self.connected:
            raise RuntimeError("Not connected to Outlook. Call connect() first.")
        
        try:
            email = self.outlook_manager.namespace.GetItemFromID(email_id)
            return self.outlook_manager._add_category_to_email(email, category)
        except Exception as e:
            print(f"Error categorizing email: {e}")
            return False
    
    def get_email_by_id(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get a single email by its EntryID.
        
        Args:
            email_id: EntryID of the email to retrieve
        
        Returns:
            Email dictionary if found, None otherwise
        """
        if not self.connected:
            raise RuntimeError("Not connected to Outlook. Call connect() first.")
        
        try:
            email = self.outlook_manager.namespace.GetItemFromID(email_id)
            if email:
                return self._email_to_dict(email)
            return None
        except Exception as e:
            print(f"Error retrieving email by ID {email_id}: {e}")
            return None
    
    def _email_to_dict(self, email) -> Dict[str, Any]:
        """Convert Outlook email COM object to dictionary.
        
        Args:
            email: Outlook email COM object
        
        Returns:
            Dictionary with standardized email fields
        """
        try:
            # Extract sender - try multiple properties for best results
            sender = ''
            try:
                # Try SenderEmailAddress first (most reliable for SMTP addresses)
                sender = getattr(email, 'SenderEmailAddress', '')
                
                # If it's an Exchange address (starts with /O=), try SenderName or Sender.Address
                if not sender or sender.startswith('/O='):
                    # Try the Sender property for Address
                    if hasattr(email, 'Sender') and email.Sender:
                        sender = getattr(email.Sender, 'Address', '') or getattr(email.Sender, 'Name', '')
                    
                    # If still no luck, try SenderName
                    if not sender:
                        sender = getattr(email, 'SenderName', '')
            except:
                sender = getattr(email, 'SenderName', 'Unknown Sender')
            
            # Extract basic fields
            email_dict = {
                'id': email.EntryID,
                'subject': getattr(email, 'Subject', '(No Subject)'),
                'sender': sender or 'Unknown Sender',
                'recipient': '',
                'body': getattr(email, 'Body', '')[:500],  # Truncate for list view
                'received_time': self._format_datetime(email.ReceivedTime),
                'date': self._format_datetime(email.ReceivedTime),
                'is_read': not email.UnRead,
                'has_attachments': email.Attachments.Count > 0 if hasattr(email, 'Attachments') else False,
                'categories': email.Categories if hasattr(email, 'Categories') else '',
                'conversation_id': getattr(email, 'ConversationID', ''),
            }
            
            # Extract recipient emails - try multiple methods
            try:
                # Method 1: Try To field (most reliable)
                if hasattr(email, 'To') and email.To:
                    # Take first recipient if multiple (separated by semicolon)
                    to_field = email.To
                    if ';' in to_field:
                        email_dict['recipient'] = to_field.split(';')[0].strip()
                    else:
                        email_dict['recipient'] = to_field.strip()
                # Method 2: Try Recipients collection as fallback
                elif hasattr(email, 'Recipients') and email.Recipients.Count > 0:
                    try:
                        recipient = email.Recipients.Item(1)
                        email_dict['recipient'] = recipient.Address
                    except:
                        # If Address fails, try Name
                        try:
                            recipient = email.Recipients.Item(1)
                            email_dict['recipient'] = recipient.Name
                        except:
                            pass
            except Exception as e:
                # If all extraction methods fail, leave empty
                pass
            
            return email_dict
            
        except Exception as e:
            print(f"Error converting email to dict: {e}")
            return {
                'id': getattr(email, 'EntryID', ''),
                'subject': 'Error loading email',
                'sender': '',
                'recipient': '',
                'body': '',
                'received_time': '',
                'date': '',
                'is_read': False,
                'has_attachments': False,
                'categories': '',
                'conversation_id': '',
            }
    
    def _format_datetime(self, dt) -> str:
        """Format COM datetime to ISO string.
        
        Args:
            dt: COM datetime object
        
        Returns:
            ISO format datetime string
        """
        try:
            if dt:
                # Convert to Python datetime if needed
                if hasattr(dt, 'strftime'):
                    return dt.strftime('%Y-%m-%dT%H:%M:%S')
                else:
                    # Try to parse as COM date
                    from pywintypes import TimeType
                    if isinstance(dt, TimeType):
                        return dt.Format('%Y-%m-%dT%H:%M:%S')
            return ''
        except:
            return ''
