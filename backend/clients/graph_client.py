"""Microsoft Graph API client for Email Helper API.

This module provides Microsoft Graph API integration with OAuth2 authentication,
email retrieval, folder management, and email operations for cross-platform
mobile app compatibility.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import msal
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from backend.core.config import settings


class GraphAPIError(Exception):
    """Custom exception for Graph API errors."""
    
    def __init__(self, message: str, status_code: int = None, error_code: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class GraphClient:
    """Microsoft Graph API client with OAuth2 authentication."""
    
    def __init__(self, client_id: str, client_secret: str, tenant_id: str, redirect_uri: str = None):
        """Initialize Graph client.
        
        Args:
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
            tenant_id: Azure AD tenant ID
            redirect_uri: OAuth2 redirect URI for user consent flow
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.redirect_uri = redirect_uri or "http://localhost:8000/auth/callback"
        
        # Graph API configuration
        self.graph_base_url = "https://graph.microsoft.com/v1.0"
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scopes = [
            "https://graph.microsoft.com/Mail.Read",
            "https://graph.microsoft.com/Mail.ReadWrite",
            "https://graph.microsoft.com/Mail.Send",
            "https://graph.microsoft.com/User.Read"
        ]
        
        # Initialize MSAL client
        self.app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=self.authority
        )
        
        # Token storage
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        # HTTP session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        
        self.logger = logging.getLogger(__name__)
    
    def get_authorization_url(self) -> str:
        """Get OAuth2 authorization URL for user consent."""
        auth_url = self.app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        return auth_url
    
    def authenticate_with_code(self, authorization_code: str) -> Dict[str, Any]:
        """Authenticate using authorization code from OAuth2 flow.
        
        Args:
            authorization_code: Authorization code from OAuth2 callback
            
        Returns:
            Token response with access_token, refresh_token, etc.
        """
        try:
            result = self.app.acquire_token_by_authorization_code(
                authorization_code,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.refresh_token = result.get("refresh_token")
                
                # Calculate token expiration
                expires_in = result.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                self.logger.info("Successfully authenticated with Microsoft Graph API")
                return result
            else:
                error_msg = result.get("error_description", "Authentication failed")
                raise GraphAPIError(f"Authentication failed: {error_msg}")
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            raise GraphAPIError(f"Authentication error: {e}")
    
    def authenticate_with_credentials(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate using username/password (for testing only).
        
        Note: This method uses Resource Owner Password Credentials flow
        which is not recommended for production apps.
        """
        try:
            result = self.app.acquire_token_by_username_password(
                username=username,
                password=password,
                scopes=self.scopes
            )
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.refresh_token = result.get("refresh_token")
                
                expires_in = result.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                self.logger.info("Successfully authenticated with username/password")
                return result
            else:
                error_msg = result.get("error_description", "Authentication failed")
                raise GraphAPIError(f"Authentication failed: {error_msg}")
                
        except Exception as e:
            self.logger.error(f"Credential authentication error: {e}")
            raise GraphAPIError(f"Credential authentication error: {e}")
    
    def refresh_access_token(self) -> bool:
        """Refresh access token using refresh token."""
        if not self.refresh_token:
            return False
        
        try:
            result = self.app.acquire_token_by_refresh_token(
                self.refresh_token,
                scopes=self.scopes
            )
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.refresh_token = result.get("refresh_token", self.refresh_token)
                
                expires_in = result.get("expires_in", 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                self.logger.info("Successfully refreshed access token")
                return True
            else:
                self.logger.warning("Failed to refresh token")
                return False
                
        except Exception as e:
            self.logger.error(f"Token refresh error: {e}")
            return False
    
    def ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token."""
        if not self.access_token:
            return False
        
        # Check if token is expired (with 5-minute buffer)
        if self.token_expires_at and datetime.now() >= (self.token_expires_at - timedelta(minutes=5)):
            return self.refresh_access_token()
        
        return True
    
    def _make_graph_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, 
                           data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to Graph API."""
        if not self.ensure_valid_token():
            raise GraphAPIError("No valid access token available", status_code=401)
        
        url = f"{self.graph_base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                time.sleep(retry_after)
                
                # Retry the request
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data,
                    timeout=30
                )
            
            if response.status_code >= 400:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                error_code = error_data.get("error", {}).get("code")
                
                raise GraphAPIError(error_msg, response.status_code, error_code)
            
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Graph API request error: {e}")
            raise GraphAPIError(f"Graph API request error: {e}")
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get current user profile."""
        return self._make_graph_request("GET", "/me")
    
    def get_messages(self, folder_id: str = "inbox", count: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get messages from specified folder.
        
        Args:
            folder_id: Folder ID or well-known name (inbox, sentitems, drafts)
            count: Number of messages to retrieve (max 100)
            offset: Number of messages to skip for pagination
            
        Returns:
            List of message objects
        """
        params = {
            "$top": min(count, 100),
            "$skip": offset,
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,toRecipients,receivedDateTime,hasAttachments,isRead,conversationId,categories,importance,bodyPreview"
        }
        
        endpoint = f"/me/mailFolders/{folder_id}/messages"
        result = self._make_graph_request("GET", endpoint, params=params)
        
        return result.get("value", [])
    
    def get_message_content(self, message_id: str) -> Dict[str, Any]:
        """Get full message content by ID."""
        endpoint = f"/me/messages/{message_id}"
        params = {
            "$select": "id,subject,from,toRecipients,receivedDateTime,hasAttachments,isRead,conversationId,categories,importance,body,bodyPreview"
        }
        
        return self._make_graph_request("GET", endpoint, params=params)
    
    def get_folders(self) -> List[Dict[str, Any]]:
        """Get mail folders."""
        endpoint = "/me/mailFolders"
        params = {
            "$select": "id,displayName,parentFolderId,childFolderCount,unreadItemCount,totalItemCount"
        }
        
        result = self._make_graph_request("GET", endpoint, params=params)
        return result.get("value", [])
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read."""
        endpoint = f"/me/messages/{message_id}"
        data = {"isRead": True}
        
        try:
            self._make_graph_request("PATCH", endpoint, data=data)
            return True
        except GraphAPIError as e:
            self.logger.error(f"Failed to mark message as read: {e}")
            return False
    
    def move_message(self, message_id: str, destination_folder_id: str) -> bool:
        """Move message to another folder."""
        endpoint = f"/me/messages/{message_id}/move"
        data = {"destinationId": destination_folder_id}
        
        try:
            self._make_graph_request("POST", endpoint, data=data)
            return True
        except GraphAPIError as e:
            self.logger.error(f"Failed to move message: {e}")
            return False
    
    def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a conversation thread."""
        params = {
            "$filter": f"conversationId eq '{conversation_id}'",
            "$orderby": "receivedDateTime asc",
            "$select": "id,subject,from,toRecipients,receivedDateTime,hasAttachments,isRead,conversationId,categories,importance,bodyPreview"
        }
        
        result = self._make_graph_request("GET", "/me/messages", params=params)
        return result.get("value", [])