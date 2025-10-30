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
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import HTTPException

try:
    import pythoncom
    PYTHONCOM_AVAILABLE = True
except ImportError:
    PYTHONCOM_AVAILABLE = False
    pythoncom = None

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from backend.services.email_provider import EmailProvider

# Import OutlookEmailAdapter - only available on Windows
try:
    from adapters.outlook_email_adapter import OutlookEmailAdapter
    COM_AVAILABLE = True
except ImportError:
    COM_AVAILABLE = False
    OutlookEmailAdapter = None


# Category mappings from Python version (outlook_manager.py)
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
            self.logger.info("Attempting to connect to Outlook COM interface...")
            
            success = self.adapter.connect()
            
            if success:
                self.authenticated = True
                self.logger.info("Successfully connected to Outlook COM interface")
                return True
            else:
                self.authenticated = False
                error_msg = (
                    "Could not connect to Outlook. "
                    "Please ensure Microsoft Outlook is running and you have access to it."
                )
                self.logger.error(error_msg)
                raise HTTPException(
                    status_code=503,
                    detail=error_msg
                )
                
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            self.authenticated = False
            error_detail = str(e)
            self.logger.error(f"Outlook COM connection error: {error_detail}")
            
            # Provide helpful error messages based on common issues
            if "pywintypes.com_error" in error_detail or "-2147221005" in error_detail:
                helpful_msg = (
                    "Cannot connect to Outlook COM interface. "
                    "Please ensure Microsoft Outlook is running and not blocked by security policies."
                )
            elif "CoInitialize" in error_detail:
                helpful_msg = (
                    "COM initialization error. "
                    "The application may need to run in a different threading mode."
                )
            else:
                helpful_msg = f"Outlook connection failed: {error_detail}"
            
            raise HTTPException(
                status_code=503,
                detail=helpful_msg
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
            HTTPException: If adapter not connected or retrieval fails
        """
        try:
            # Initialize COM on this thread (required for multi-threaded servers)
            if PYTHONCOM_AVAILABLE:
                try:
                    pythoncom.CoInitialize()
                except:
                    pass  # Already initialized on this thread
            
            self.logger.debug(
                f"Retrieving emails from {folder_name}: count={count}, offset={offset}"
            )
            
            # Reconnect adapter to ensure COM objects are on this thread
            if not self.adapter.connect():
                self.logger.warning("Adapter connection failed, retrying...")
                # Retry once
                import time
                time.sleep(0.2)
                if not self.adapter.connect():
                    raise RuntimeError("Failed to connect to Outlook after retry")
            
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
    
    def get_email_by_id(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get a single email by its ID.
        
        Args:
            email_id: Email EntryID from Outlook
        
        Returns:
            Email dictionary if found, None otherwise
        
        Raises:
            HTTPException: If adapter not connected or retrieval fails
        """
        try:
            # Initialize COM on this thread
            if PYTHONCOM_AVAILABLE:
                try:
                    pythoncom.CoInitialize()
                except:
                    pass
            
            self.logger.debug(f"Retrieving email by ID: {email_id}")
            
            # Reconnect to ensure COM objects are on this thread
            self.adapter.connect()
            
            # Use adapter's get_email_by_id if available, otherwise search
            if hasattr(self.adapter, 'get_email_by_id'):
                email = self.adapter.get_email_by_id(email_id)
            else:
                # Fallback: search through recent emails
                # This is inefficient but works as a fallback
                all_emails = self.adapter.get_emails(folder_name="Inbox", count=500)
                email = next((e for e in all_emails if e.get('id') == email_id), None)
            
            if email:
                self.logger.info(f"Found email: {email_id}")
            else:
                self.logger.warning(f"Email not found: {email_id}")
            
            return email
            
        except RuntimeError as e:
            self.logger.error(f"Connection error: {e}")
            self.authenticated = False
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            self.logger.error(f"Error retrieving email by ID: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve email: {str(e)}"
            )

    async def get_email_content(self, email_id: str) -> Dict[str, Any]:
        """Get full email content by ID.
        
        Retrieves complete email details including full body content.
        
        Args:
            email_id: Email EntryID from Outlook
        
        Returns:
            Email dictionary with full content, or None if not found
        
        Raises:
            HTTPException: If adapter not connected or retrieval fails
        """
        try:
            # Run sync COM operations in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._get_email_content_sync, email_id)
            
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
    
    def _get_email_content_sync(self, email_id: str) -> Dict[str, Any]:
        """Synchronous helper to get email content (runs in thread pool)."""
        # Initialize COM on this thread
        if PYTHONCOM_AVAILABLE:
            try:
                pythoncom.CoInitialize()
            except:
                pass
        
        self.logger.debug(f"Retrieving email content for ID: {email_id}")
        
        # Reconnect to ensure COM objects are on this thread
        self.adapter.connect()
        
        # Use the adapter's get_email_by_id method - it already handles all the metadata extraction correctly!
        # This is the SAME method used by get_emails() which works perfectly
        email_dict = self.adapter.get_email_by_id(email_id)
        
        if not email_dict:
            raise HTTPException(
                status_code=404,
                detail=f"Email with ID '{email_id}' not found"
            )
        
        # Get full body content (adapter truncates it for list view)
        try:
            full_body = self.adapter.get_email_body(email_id)
            email_dict['body'] = full_body or email_dict.get('body', '')
        except Exception as e:
            self.logger.warning(f"Could not retrieve full body for {email_id}: {e}")
            # Keep the truncated body from email_dict
        
        # Map importance format if needed
        if 'importance' not in email_dict or not email_dict['importance']:
            email_dict['importance'] = 'Normal'
        
        return email_dict
    
    def get_folders(self) -> List[Dict[str, str]]:
        """List available email folders.
        
        Returns:
            List of folder dictionaries with id, name, and type
        
        Raises:
            HTTPException: If adapter not connected or listing fails
        """
        try:
            # Initialize COM on this thread
            if PYTHONCOM_AVAILABLE:
                try:
                    pythoncom.CoInitialize()
                except:
                    pass
            
            self.logger.debug("Retrieving folder list")
            
            # Reconnect to ensure COM objects are on this thread
            self.adapter.connect()
            
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
            HTTPException: If adapter not connected or operation fails
        """
        try:
            # Initialize COM on this thread
            if PYTHONCOM_AVAILABLE:
                try:
                    pythoncom.CoInitialize()
                except:
                    pass
            
            self.logger.debug(f"Marking email as read: {email_id}")
            
            # Reconnect to ensure COM objects are on this thread
            self.adapter.connect()
            
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
            HTTPException: If adapter not connected or operation fails
        """
        try:
            # Initialize COM on this thread
            if PYTHONCOM_AVAILABLE:
                try:
                    pythoncom.CoInitialize()
                except:
                    pass
            
            self.logger.info(f"[COM Provider] Moving email {email_id[:20]}... to folder: '{destination_folder}'")
            
            # Reconnect to ensure COM objects are on this thread
            self.adapter.connect()
            
            success = self.adapter.move_email(email_id, destination_folder)
            
            if success:
                self.logger.info(f"[COM Provider] [OK] Successfully moved email to '{destination_folder}'")
            else:
                self.logger.warning(f"[COM Provider] [FAIL] Failed to move email to '{destination_folder}'")
            
            return success
            
        except RuntimeError as e:
            self.logger.error(f"[COM Provider] Connection error while moving email: {e}")
            self.authenticated = False
            return False  # Return False instead of raising to allow batch processing to continue
        except Exception as e:
            self.logger.error(f"[COM Provider] Error moving email to {destination_folder}: {e}")
            return False  # Return False instead of raising to allow batch processing to continue
    
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
            HTTPException: If adapter not connected or retrieval fails
        """
        try:
            # Initialize COM on this thread
            if PYTHONCOM_AVAILABLE:
                try:
                    pythoncom.CoInitialize()
                except:
                    pass
            
            self.logger.debug(f"Retrieving conversation thread: {conversation_id}")
            
            # Reconnect to ensure COM objects are on this thread
            self.adapter.connect()
            
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
