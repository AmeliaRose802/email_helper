"""Graph API EmailProvider implementation for Email Helper API.

This module provides Microsoft Graph API implementation of the EmailProvider
interface, enabling cross-platform email access with OAuth2 authentication.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

from backend.clients.graph_client import GraphClient, GraphAPIError
from backend.models.graph_email import EmailNormalizer
from backend.services.email_provider import EmailProvider
from backend.core.config import settings


class GraphEmailProvider(EmailProvider):
    """Microsoft Graph API implementation of EmailProvider interface."""
    
    def __init__(self, client_id: str, client_secret: str, tenant_id: str, redirect_uri: str = None):
        """Initialize Graph email provider.
        
        Args:
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
            tenant_id: Azure AD tenant ID
            redirect_uri: OAuth2 redirect URI
        """
        self.graph_client = GraphClient(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
            redirect_uri=redirect_uri
        )
        
        self.authenticated = False
        self.user_profile = None
        self.logger = logging.getLogger(__name__)
        
        # Cache for folders
        self._folders_cache = None
        self._cache_expiry = None
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Microsoft Graph API.
        
        Args:
            credentials: Authentication credentials
                - For OAuth2 flow: {"authorization_code": "..."}
                - For testing: {"username": "...", "password": "..."}
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            if "authorization_code" in credentials:
                # OAuth2 authorization code flow
                result = self.graph_client.authenticate_with_code(
                    credentials["authorization_code"]
                )
            elif "username" in credentials and "password" in credentials:
                # Username/password flow (for testing only)
                result = self.graph_client.authenticate_with_credentials(
                    credentials["username"],
                    credentials["password"]
                )
            else:
                raise ValueError("Invalid credentials format")
            
            if result and "access_token" in result:
                self.authenticated = True
                
                # Get user profile
                try:
                    self.user_profile = self.graph_client.get_user_profile()
                    self.logger.info(f"Authenticated as {self.user_profile.get('userPrincipalName', 'unknown')}")
                except Exception as e:
                    self.logger.warning(f"Could not retrieve user profile: {e}")
                
                return True
            
            return False
            
        except GraphAPIError as e:
            self.logger.error(f"Graph API authentication error: {e}")
            raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            raise HTTPException(status_code=500, detail=f"Authentication error: {e}")
    
    def get_emails(self, folder_name: str = "Inbox", count: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve emails from the specified folder with pagination.
        
        Args:
            folder_name: Name of the folder (Inbox, Sent Items, etc.)
            count: Number of emails to retrieve (max 100)
            offset: Number of emails to skip for pagination
            
        Returns:
            List of normalized email data
        """
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated with Graph API")
        
        try:
            # Map folder names to Graph API folder IDs
            folder_id = self._get_folder_id(folder_name)
            
            # Get messages from Graph API
            graph_messages = self.graph_client.get_messages(
                folder_id=folder_id,
                count=min(count, 100),  # Graph API limit
                offset=offset
            )
            
            # Normalize messages to internal format
            normalized_emails = EmailNormalizer.batch_normalize_messages(
                graph_messages, folder_name
            )
            
            self.logger.info(f"Retrieved {len(normalized_emails)} emails from {folder_name}")
            return normalized_emails
            
        except GraphAPIError as e:
            self.logger.error(f"Failed to get emails from {folder_name}: {e}")
            if e.status_code == 401:
                raise HTTPException(status_code=401, detail="Authentication expired")
            elif e.status_code == 403:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            elif e.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Folder '{folder_name}' not found")
            else:
                raise HTTPException(status_code=500, detail=f"Graph API error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting emails: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    
    def get_email_content(self, email_id: str) -> Dict[str, Any]:
        """Get full email content by ID.
        
        Args:
            email_id: Email ID from Graph API
            
        Returns:
            Normalized email data with full content
        """
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated with Graph API")
        
        try:
            # Get full message content from Graph API
            graph_message = self.graph_client.get_message_content(email_id)
            
            if not graph_message:
                raise HTTPException(status_code=404, detail=f"Email '{email_id}' not found")
            
            # Normalize message to internal format
            normalized_email = EmailNormalizer.normalize_graph_message(graph_message)
            
            self.logger.debug(f"Retrieved email content for {email_id}")
            return normalized_email
            
        except GraphAPIError as e:
            self.logger.error(f"Failed to get email content for {email_id}: {e}")
            if e.status_code == 401:
                raise HTTPException(status_code=401, detail="Authentication expired")
            elif e.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Email '{email_id}' not found")
            else:
                raise HTTPException(status_code=500, detail=f"Graph API error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting email content: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    
    def get_folders(self) -> List[Dict[str, str]]:
        """List available email folders.
        
        Returns:
            List of normalized folder data
        """
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated with Graph API")
        
        try:
            # Check cache first
            from datetime import datetime, timedelta
            if (self._folders_cache and self._cache_expiry and 
                datetime.now() < self._cache_expiry):
                return self._folders_cache
            
            # Get folders from Graph API
            graph_folders = self.graph_client.get_folders()
            
            # Normalize folders to internal format
            normalized_folders = []
            for graph_folder in graph_folders:
                normalized_folder = EmailNormalizer.normalize_graph_folder(graph_folder)
                normalized_folders.append(normalized_folder)
            
            # Cache results for 5 minutes
            self._folders_cache = normalized_folders
            self._cache_expiry = datetime.now() + timedelta(minutes=5)
            
            self.logger.info(f"Retrieved {len(normalized_folders)} folders")
            return normalized_folders
            
        except GraphAPIError as e:
            self.logger.error(f"Failed to get folders: {e}")
            if e.status_code == 401:
                raise HTTPException(status_code=401, detail="Authentication expired")
            else:
                raise HTTPException(status_code=500, detail=f"Graph API error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting folders: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    
    def mark_as_read(self, email_id: str) -> bool:
        """Mark email as read.
        
        Args:
            email_id: Email ID from Graph API
            
        Returns:
            True if successful, False otherwise
        """
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated with Graph API")
        
        try:
            success = self.graph_client.mark_as_read(email_id)
            
            if success:
                self.logger.debug(f"Marked email {email_id} as read")
            else:
                self.logger.warning(f"Failed to mark email {email_id} as read")
            
            return success
            
        except GraphAPIError as e:
            self.logger.error(f"Failed to mark email {email_id} as read: {e}")
            if e.status_code == 401:
                raise HTTPException(status_code=401, detail="Authentication expired")
            elif e.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Email '{email_id}' not found")
            else:
                raise HTTPException(status_code=500, detail=f"Graph API error: {e}")
    
    def move_email(self, email_id: str, destination_folder: str) -> bool:
        """Move an email to the specified folder.
        
        Args:
            email_id: Email ID from Graph API
            destination_folder: Name of destination folder
            
        Returns:
            True if successful, False otherwise
        """
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated with Graph API")
        
        try:
            # Get destination folder ID
            destination_folder_id = self._get_folder_id(destination_folder)
            
            success = self.graph_client.move_message(email_id, destination_folder_id)
            
            if success:
                self.logger.debug(f"Moved email {email_id} to {destination_folder}")
            else:
                self.logger.warning(f"Failed to move email {email_id} to {destination_folder}")
            
            return success
            
        except GraphAPIError as e:
            self.logger.error(f"Failed to move email {email_id}: {e}")
            if e.status_code == 401:
                raise HTTPException(status_code=401, detail="Authentication expired")
            elif e.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Email or folder not found")
            else:
                raise HTTPException(status_code=500, detail=f"Graph API error: {e}")
    
    def get_conversation_thread(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all emails in a conversation thread.
        
        Args:
            conversation_id: Conversation ID from Graph API
            
        Returns:
            List of normalized email data in conversation
        """
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated with Graph API")
        
        try:
            # Get conversation messages from Graph API
            graph_messages = self.graph_client.get_conversation_messages(conversation_id)
            
            # Normalize messages to internal format
            normalized_emails = EmailNormalizer.batch_normalize_messages(graph_messages)
            
            self.logger.debug(f"Retrieved {len(normalized_emails)} messages in conversation {conversation_id}")
            return normalized_emails
            
        except GraphAPIError as e:
            self.logger.error(f"Failed to get conversation {conversation_id}: {e}")
            if e.status_code == 401:
                raise HTTPException(status_code=401, detail="Authentication expired")
            else:
                raise HTTPException(status_code=500, detail=f"Graph API error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting conversation: {e}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    
    def _get_folder_id(self, folder_name: str) -> str:
        """Get Graph API folder ID from folder name.
        
        Args:
            folder_name: Human-readable folder name
            
        Returns:
            Graph API folder ID or well-known name
        """
        # Map common folder names to Graph API well-known names
        folder_mapping = {
            "inbox": "inbox",
            "sent items": "sentitems",
            "sent": "sentitems",
            "drafts": "drafts",
            "deleted items": "deleteditems",
            "trash": "deleteditems",
            "junk email": "junkemail",
            "spam": "junkemail",
            "outbox": "outbox"
        }
        
        folder_name_lower = folder_name.lower()
        
        # Check if it's a well-known folder
        if folder_name_lower in folder_mapping:
            return folder_mapping[folder_name_lower]
        
        # If not well-known, try to find exact match in folders
        try:
            folders = self.get_folders()
            for folder in folders:
                if folder["name"].lower() == folder_name_lower:
                    return folder["id"]
        except Exception as e:
            self.logger.warning(f"Could not search folders for '{folder_name}': {e}")
        
        # Default to inbox if not found
        self.logger.warning(f"Folder '{folder_name}' not found, defaulting to inbox")
        return "inbox"
    
    def get_authorization_url(self) -> str:
        """Get OAuth2 authorization URL for user consent.
        
        Returns:
            Authorization URL for OAuth2 flow
        """
        return self.graph_client.get_authorization_url()
    
    def is_authenticated(self) -> bool:
        """Check if provider is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.authenticated and self.graph_client.ensure_valid_token()
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user information.
        
        Returns:
            User profile data or None if not authenticated
        """
        return self.user_profile