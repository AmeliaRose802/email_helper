"""Generic EmailProvider interface implementation for Email Helper API.

This module provides the generic EmailProvider service that abstracts
email access across different providers (Graph API, IMAP, etc.) while
maintaining compatibility with the existing EmailProvider interface
from src/core/interfaces.py.
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from fastapi import Depends, HTTPException

# Add src to Python path for existing service imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from backend.core.config import settings

try:
    from core.interfaces import EmailProvider as CoreEmailProvider
except ImportError:
    # Fallback if src modules can't be imported
    class CoreEmailProvider(ABC):
        @abstractmethod
        def get_emails(self, folder_name: str = "Inbox", count: int = 50) -> List[Dict[str, Any]]:
            pass
        
        @abstractmethod
        def move_email(self, email_id: str, destination_folder: str) -> bool:
            pass
        
        @abstractmethod
        def get_email_body(self, email_id: str) -> str:
            pass


class EmailProvider(CoreEmailProvider):
    """Enhanced EmailProvider interface for backend API."""
    
    @abstractmethod
    def get_emails(self, folder_name: str = "Inbox", count: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve emails from the specified folder with pagination."""
        pass
    
    @abstractmethod
    def get_email_content(self, email_id: str) -> Dict[str, Any]:
        """Get full email content by ID."""
        pass
    
    @abstractmethod
    def get_folders(self) -> List[Dict[str, str]]:
        """List available email folders."""
        pass
    
    @abstractmethod
    def mark_as_read(self, email_id: str) -> bool:
        """Mark email as read."""
        pass
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with email provider."""
        pass
    
    @abstractmethod
    def get_conversation_thread(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all emails in a conversation thread."""
        pass

    def get_email_body(self, email_id: str) -> str:
        """Get email body text (compatibility method)."""
        email = self.get_email_content(email_id)
        return email.get('body', '') if email else ''


class MockEmailProvider(EmailProvider):
    """Mock email provider for testing and development."""
    
    def __init__(self):
        self.authenticated = False
        self.mock_emails = [
            {
                'id': 'mock-email-1',
                'subject': 'Test Email 1',
                'sender': 'test1@example.com',
                'recipient': 'user@example.com',
                'body': 'This is a test email body.',
                'received_time': '2024-01-01T10:00:00Z',
                'conversation_id': 'conv-1',
                'categories': ['Test'],
                'folder': 'Inbox',
                'is_read': False
            },
            {
                'id': 'mock-email-2',
                'subject': 'Test Email 2',
                'sender': 'test2@example.com',
                'recipient': 'user@example.com',
                'body': 'This is another test email body.',
                'received_time': '2024-01-01T11:00:00Z',
                'conversation_id': 'conv-2',
                'categories': ['Work'],
                'folder': 'Inbox',
                'is_read': True
            }
        ]
        self.mock_folders = [
            {'id': 'inbox', 'name': 'Inbox', 'type': 'inbox'},
            {'id': 'sent', 'name': 'Sent Items', 'type': 'sent'},
            {'id': 'drafts', 'name': 'Drafts', 'type': 'drafts'},
        ]
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Mock authentication."""
        self.authenticated = True
        return True
    
    def get_emails(self, folder_name: str = "Inbox", count: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get mock emails with pagination."""
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        folder_emails = [email for email in self.mock_emails if email['folder'] == folder_name]
        return folder_emails[offset:offset + count]
    
    def get_email_content(self, email_id: str) -> Dict[str, Any]:
        """Get mock email content."""
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        for email in self.mock_emails:
            if email['id'] == email_id:
                return email
        return None
    
    def get_folders(self) -> List[Dict[str, str]]:
        """Get mock folders."""
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        return self.mock_folders
    
    def mark_as_read(self, email_id: str) -> bool:
        """Mark mock email as read."""
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        for email in self.mock_emails:
            if email['id'] == email_id:
                email['is_read'] = True
                return True
        return False
    
    def move_email(self, email_id: str, destination_folder: str) -> bool:
        """Move mock email to folder."""
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        for email in self.mock_emails:
            if email['id'] == email_id:
                email['folder'] = destination_folder
                return True
        return False
    
    def get_conversation_thread(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get mock conversation thread."""
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        return [email for email in self.mock_emails if email['conversation_id'] == conversation_id]


# Global email provider instance
_email_provider: Optional[EmailProvider] = None


def get_email_provider_instance() -> EmailProvider:
    """Get or create email provider instance."""
    global _email_provider
    
    if _email_provider is None:
        # Check if Graph API credentials are configured
        if (settings.graph_client_id and 
            settings.graph_client_secret and 
            settings.graph_tenant_id):
            # Use Graph API provider in production
            from backend.services.graph_email_provider import GraphEmailProvider
            _email_provider = GraphEmailProvider(
                client_id=settings.graph_client_id,
                client_secret=settings.graph_client_secret,
                tenant_id=settings.graph_tenant_id,
                redirect_uri=settings.graph_redirect_uri
            )
        else:
            # Use mock provider for development/testing
            _email_provider = MockEmailProvider()
    
    return _email_provider


def get_email_provider() -> EmailProvider:
    """FastAPI dependency for email provider."""
    return get_email_provider_instance()