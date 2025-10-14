"""Outlook Email Adapter for Backend Integration.

This module provides an adapter that wraps the existing OutlookManager class
to implement the EmailProvider interface, enabling seamless integration with
the FastAPI backend without duplicating existing COM functionality.

The adapter maintains full backward compatibility while providing a clean
interface for dependency injection and testing.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add src to Python path if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.interfaces import EmailProvider
from outlook_manager import OutlookManager


class OutlookEmailAdapter(EmailProvider):
    """Adapter wrapping OutlookManager to implement EmailProvider interface.
    
    This adapter delegates all email operations to the existing OutlookManager
    implementation, providing a standardized interface for the backend API
    without duplicating functionality.
    
    The adapter handles:
    - Email retrieval with filtering and pagination
    - Email folder operations and organization
    - Email movement and categorization
    - Email body content access
    - Folder structure management
    
    Attributes:
        outlook_manager (OutlookManager): Wrapped Outlook COM interface
        connected (bool): Connection status to Outlook application
    
    Example:
        >>> adapter = OutlookEmailAdapter()
        >>> adapter.connect()
        >>> emails = adapter.get_emails("Inbox", count=10)
        >>> adapter.move_email(emails[0]['id'], "Archive")
    """
    
    def __init__(self, outlook_manager: Optional[OutlookManager] = None):
        """Initialize the adapter with optional OutlookManager instance.
        
        Args:
            outlook_manager: Optional existing OutlookManager instance.
                           If None, creates a new instance.
        """
        self.outlook_manager = outlook_manager or OutlookManager()
        self.connected = False
    
    def connect(self) -> bool:
        """Establish connection to Outlook application.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.outlook_manager.connect_to_outlook()
            self.connected = True
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
        
        This method wraps OutlookManager's email retrieval functionality,
        converting COM objects to dictionaries suitable for API responses.
        
        Args:
            folder_name: Name of the Outlook folder to retrieve from
            count: Maximum number of emails to retrieve
            offset: Number of emails to skip (for pagination)
        
        Returns:
            List of email dictionaries with standardized fields:
            - id: Unique email identifier (EntryID)
            - subject: Email subject line
            - sender: Sender email address
            - recipient: Primary recipient address
            - body: Email body text (plain or HTML)
            - received_time: ISO format timestamp
            - is_read: Read status boolean
            - categories: List of assigned categories
            - conversation_id: Thread identifier
        
        Raises:
            RuntimeError: If not connected to Outlook
        """
        if not self.connected:
            raise RuntimeError("Not connected to Outlook. Call connect() first.")
        
        try:
            # Get emails from OutlookManager
            emails = self.outlook_manager.get_emails_from_inbox(
                days_back=30,  # Default to 30 days
                count=count
            )
            
            # Convert to standardized format
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
            bool: True if move successful, False otherwise
        """
        if not self.connected:
            raise RuntimeError("Not connected to Outlook. Call connect() first.")
        
        try:
            # Get the email item by EntryID
            email = self.outlook_manager.namespace.GetItemFromID(email_id)
            
            # Get or create the destination folder
            target_folder = self.outlook_manager._get_or_create_folder(destination_folder)
            
            # Move the email
            email.Move(target_folder)
            return True
            
        except Exception as e:
            print(f"Error moving email: {e}")
            return False
    
    def get_email_body(self, email_id: str) -> str:
        """Get the full body text of an email.
        
        Args:
            email_id: EntryID of the email
        
        Returns:
            str: Email body text (plain text or HTML)
        """
        if not self.connected:
            raise RuntimeError("Not connected to Outlook. Call connect() first.")
        
        try:
            email = self.outlook_manager.namespace.GetItemFromID(email_id)
            
            # Try to get plain text body first, fall back to HTML
            body = getattr(email, 'Body', None)
            if not body:
                body = getattr(email, 'HTMLBody', '')
            
            return body or ""
            
        except Exception as e:
            print(f"Error retrieving email body: {e}")
            return ""
    
    def get_folders(self) -> List[Dict[str, str]]:
        """List available email folders.
        
        Returns:
            List of folder dictionaries with id and name
        """
        if not self.connected:
            raise RuntimeError("Not connected to Outlook. Call connect() first.")
        
        try:
            folders = []
            inbox_parent = self.outlook_manager.inbox.Parent
            
            for folder in inbox_parent.Folders:
                try:
                    folders.append({
                        'id': folder.EntryID,
                        'name': folder.Name,
                        'type': 'mail'
                    })
                except Exception:
                    continue
            
            return folders
            
        except Exception as e:
            print(f"Error listing folders: {e}")
            return []
    
    def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read.
        
        Args:
            email_id: EntryID of the email
        
        Returns:
            bool: True if successful, False otherwise
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
    
    def categorize_email(self, email_id: str, category: str, color: str = None) -> bool:
        """Apply a category to an email.
        
        Args:
            email_id: EntryID of the email
            category: Category name to apply
            color: Optional Outlook color category
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            raise RuntimeError("Not connected to Outlook. Call connect() first.")
        
        try:
            email = self.outlook_manager.namespace.GetItemFromID(email_id)
            
            # Use OutlookManager's categorization logic
            self.outlook_manager.categorize_email(email, category)
            return True
            
        except Exception as e:
            print(f"Error categorizing email: {e}")
            return False
    
    def _email_to_dict(self, email) -> Dict[str, Any]:
        """Convert Outlook email COM object to dictionary.
        
        Args:
            email: Outlook email COM object
        
        Returns:
            Dictionary with standardized email fields
        """
        try:
            # Extract basic fields
            email_dict = {
                'id': email.EntryID,
                'subject': getattr(email, 'Subject', 'No Subject'),
                'sender': getattr(email, 'SenderEmailAddress', 'Unknown'),
                'recipient': '',
                'body': getattr(email, 'Body', '')[:500],  # Truncate for list view
                'received_time': self._format_datetime(email.ReceivedTime),
                'is_read': not email.UnRead,
                'categories': self._get_categories(email),
                'conversation_id': getattr(email, 'ConversationID', '')
            }
            
            # Extract recipient
            try:
                recipients = email.Recipients
                if recipients.Count > 0:
                    email_dict['recipient'] = recipients.Item(1).Address
            except Exception:
                pass
            
            return email_dict
            
        except Exception as e:
            print(f"Error converting email to dict: {e}")
            raise
    
    def _format_datetime(self, dt) -> str:
        """Format Outlook datetime to ISO string.
        
        Args:
            dt: Outlook datetime object
        
        Returns:
            ISO format datetime string
        """
        try:
            # Outlook datetime is a pywintypes.datetime
            return dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)
        except Exception:
            return ""
    
    def _get_categories(self, email) -> List[str]:
        """Extract categories from email.
        
        Args:
            email: Outlook email COM object
        
        Returns:
            List of category names
        """
        try:
            categories = getattr(email, 'Categories', '')
            if categories:
                return [cat.strip() for cat in categories.split(',')]
            return []
        except Exception:
            return []
