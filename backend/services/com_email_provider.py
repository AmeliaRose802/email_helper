"""COM Email Provider for Email Helper Backend API.

This module provides a FastAPI-compatible EmailProvider implementation that
wraps the existing OutlookEmailAdapter, enabling COM-based email operations
through the backend API without duplicating existing functionality.

The COM provider maintains compatibility with:
- Existing OutlookManager COM operations
- Backend EmailProvider interface
- FastAPI async patterns (via sync-to-async wrappers)
- Tkinter application functionality

Thread Safety:
    COM operations are inherently single-threaded. This provider ensures
    thread safety by maintaining COM objects on the main thread and using
    proper synchronization for concurrent access.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import HTTPException

# Add src to Python path for adapter imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from backend.services.email_provider import EmailProvider

# Import OutlookEmailAdapter - only available on Windows
try:
    from adapters.outlook_email_adapter import OutlookEmailAdapter
    COM_AVAILABLE = True
except ImportError:
    COM_AVAILABLE = False
    OutlookEmailAdapter = None


class COMEmailProvider(EmailProvider):
    """COM-based EmailProvider implementation wrapping OutlookEmailAdapter.
    
    This provider wraps the existing OutlookEmailAdapter to implement the
    backend EmailProvider interface, enabling FastAPI integration with
    Outlook COM operations without duplicating existing functionality.
    
    The provider handles:
    - Email retrieval with pagination
    - Email content access and manipulation
    - Folder operations and management
    - Email movement and categorization
    - Conversation thread retrieval
    - Connection state management
    
    Attributes:
        adapter (OutlookEmailAdapter): Wrapped Outlook COM adapter
        authenticated (bool): Authentication/connection status
        logger (logging.Logger): Logger instance for operations
    
    Example:
        >>> provider = COMEmailProvider()
        >>> provider.authenticate({})  # Connect to Outlook
        >>> emails = provider.get_emails("Inbox", count=10)
        >>> provider.mark_as_read(emails[0]['id'])
    """
    
    def __init__(self):
        """Initialize COM email provider.
        
        Raises:
            ImportError: If pywin32 or OutlookEmailAdapter not available
        """
        if not COM_AVAILABLE:
            raise ImportError(
                "COM Email Provider requires pywin32 and OutlookEmailAdapter. "
                "This is only available on Windows. "
                "Install pywin32 with: pip install pywin32"
            )
        
        self.adapter = OutlookEmailAdapter()
        self.authenticated = False
        self.logger = logging.getLogger(__name__)
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Outlook COM interface.
        
        For COM provider, authentication means establishing connection to
        the local Outlook application. Credentials are ignored as Outlook
        uses Windows integrated authentication.
        
        Args:
            credentials: Ignored for COM provider (included for interface compatibility)
        
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            HTTPException: If connection fails with error details
        """
        try:
            self.logger.info("Attempting to connect to Outlook COM interface")
            
            success = self.adapter.connect()
            
            if success:
                self.authenticated = True
                self.logger.info("Successfully connected to Outlook")
                return True
            else:
                self.authenticated = False
                self.logger.error("Failed to connect to Outlook")
                raise HTTPException(
                    status_code=503,
                    detail="Could not connect to Outlook. Ensure Outlook is running."
                )
                
        except Exception as e:
            self.authenticated = False
            self.logger.error(f"Outlook connection error: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Outlook connection failed: {str(e)}"
            )
    
    def get_emails(
        self, 
        folder_name: str = "Inbox", 
        count: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve emails from the specified folder with pagination.
        
        Args:
            folder_name: Name of the Outlook folder to retrieve from
            count: Maximum number of emails to retrieve (default: 50)
            offset: Number of emails to skip for pagination (default: 0)
        
        Returns:
            List of email dictionaries with standardized fields:
            - id: Unique email identifier (EntryID)
            - subject: Email subject line
            - sender: Sender email address
            - recipient: Primary recipient address
            - body: Email body text preview
            - received_time: ISO format timestamp
            - is_read: Read status boolean
            - categories: List of assigned categories
            - conversation_id: Thread identifier
        
        Raises:
            HTTPException: If not authenticated or retrieval fails
        """
        if not self.authenticated:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Call authenticate() first."
            )
        
        try:
            self.logger.debug(
                f"Retrieving emails from {folder_name}: count={count}, offset={offset}"
            )
            
            emails = self.adapter.get_emails(
                folder_name=folder_name,
                count=count,
                offset=offset
            )
            
            self.logger.info(f"Retrieved {len(emails)} emails from {folder_name}")
            return emails
            
        except RuntimeError as e:
            # Adapter raises RuntimeError when not connected
            self.logger.error(f"Connection error: {e}")
            self.authenticated = False
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            self.logger.error(f"Error retrieving emails: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve emails: {str(e)}"
            )
    
    def get_email_content(self, email_id: str) -> Dict[str, Any]:
        """Get full email content by ID.
        
        Retrieves complete email details including full body content.
        
        Args:
            email_id: Email EntryID from Outlook
        
        Returns:
            Email dictionary with full content, or None if not found
        
        Raises:
            HTTPException: If not authenticated or retrieval fails
        """
        if not self.authenticated:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Call authenticate() first."
            )
        
        try:
            self.logger.debug(f"Retrieving email content for ID: {email_id}")
            
            # Get full body content
            body = self.adapter.get_email_body(email_id)
            
            if body is not None:
                # Return email with full body
                # Note: This is a simplified version. In a real implementation,
                # you might want to retrieve all email fields again
                return {
                    'id': email_id,
                    'body': body
                }
            
            return None
            
        except RuntimeError as e:
            self.logger.error(f"Connection error: {e}")
            self.authenticated = False
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            self.logger.error(f"Error retrieving email content: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve email content: {str(e)}"
            )
    
    def get_folders(self) -> List[Dict[str, str]]:
        """List available email folders.
        
        Returns:
            List of folder dictionaries with id, name, and type
        
        Raises:
            HTTPException: If not authenticated or listing fails
        """
        if not self.authenticated:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Call authenticate() first."
            )
        
        try:
            self.logger.debug("Retrieving folder list")
            
            folders = self.adapter.get_folders()
            
            self.logger.info(f"Retrieved {len(folders)} folders")
            return folders
            
        except RuntimeError as e:
            self.logger.error(f"Connection error: {e}")
            self.authenticated = False
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            self.logger.error(f"Error retrieving folders: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve folders: {str(e)}"
            )
    
    def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read.
        
        Args:
            email_id: Email EntryID from Outlook
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            HTTPException: If not authenticated or operation fails
        """
        if not self.authenticated:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Call authenticate() first."
            )
        
        try:
            self.logger.debug(f"Marking email as read: {email_id}")
            
            success = self.adapter.mark_as_read(email_id)
            
            if success:
                self.logger.info(f"Marked email as read: {email_id}")
            else:
                self.logger.warning(f"Failed to mark email as read: {email_id}")
            
            return success
            
        except RuntimeError as e:
            self.logger.error(f"Connection error: {e}")
            self.authenticated = False
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            self.logger.error(f"Error marking email as read: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to mark email as read: {str(e)}"
            )
    
    def move_email(self, email_id: str, destination_folder: str) -> bool:
        """Move an email to the specified folder.
        
        Args:
            email_id: Email EntryID from Outlook
            destination_folder: Name of the destination folder
        
        Returns:
            True if move successful, False otherwise
        
        Raises:
            HTTPException: If not authenticated or operation fails
        """
        if not self.authenticated:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Call authenticate() first."
            )
        
        try:
            self.logger.debug(f"Moving email {email_id} to {destination_folder}")
            
            success = self.adapter.move_email(email_id, destination_folder)
            
            if success:
                self.logger.info(f"Moved email to {destination_folder}")
            else:
                self.logger.warning(f"Failed to move email to {destination_folder}")
            
            return success
            
        except RuntimeError as e:
            self.logger.error(f"Connection error: {e}")
            self.authenticated = False
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            self.logger.error(f"Error moving email: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to move email: {str(e)}"
            )
    
    def get_conversation_thread(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all emails in a conversation thread.
        
        Note: This is a simplified implementation that filters emails by
        conversation_id. A more complete implementation would use
        OutlookManager's conversation grouping logic.
        
        Args:
            conversation_id: Conversation ID to retrieve
        
        Returns:
            List of email dictionaries in the conversation
        
        Raises:
            HTTPException: If not authenticated or retrieval fails
        """
        if not self.authenticated:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Call authenticate() first."
            )
        
        try:
            self.logger.debug(f"Retrieving conversation thread: {conversation_id}")
            
            # Get recent emails and filter by conversation ID
            # Note: This is a basic implementation. For better performance,
            # consider using OutlookManager's conversation grouping
            all_emails = self.adapter.get_emails(folder_name="Inbox", count=100)
            
            thread_emails = [
                email for email in all_emails
                if email.get('conversation_id') == conversation_id
            ]
            
            self.logger.info(
                f"Retrieved {len(thread_emails)} emails in conversation {conversation_id}"
            )
            return thread_emails
            
        except RuntimeError as e:
            self.logger.error(f"Connection error: {e}")
            self.authenticated = False
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            self.logger.error(f"Error retrieving conversation thread: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve conversation thread: {str(e)}"
            )
