"""Generic EmailProvider interface implementation for Email Helper API.

This module provides the generic EmailProvider service interface
for email access while maintaining compatibility with the existing
EmailProvider interface from src/core/interfaces.py.

Currently only COM-based email access (Outlook on Windows) is supported.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

# Add src to Python path for existing service imports

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
    """Get or create email provider instance.

    CRITICAL: NEVER returns mock providers in production.
    Only COM provider (Windows + Outlook) is supported.

    Set use_com_backend=True in settings to use Outlook COM on Windows.
    """
    global _email_provider

    if _email_provider is None:
        import logging
        logger = logging.getLogger(__name__)

        # Check for COM provider preference (localhost with Outlook)
        if getattr(settings, 'use_com_backend', False):
            try:
                from backend.services.com_email_provider import COMEmailProvider
                logger.info("Attempting to initialize COM email provider")
                _email_provider = COMEmailProvider()
                # Auto-authenticate COM provider on startup
                _email_provider.authenticate({})
                logger.info("COM email provider initialized successfully")
                return _email_provider
            except ImportError as e:
                logger.error(f"COM provider not available: {e}")
                raise RuntimeError(
                    "COM Email Provider requires pywin32 and OutlookEmailAdapter. "
                    "This is only available on Windows. Install pywin32 with: pip install pywin32"
                ) from e
            except Exception as e:
                logger.error(f"COM provider initialization failed: {e}")
                raise RuntimeError(f"Failed to initialize COM email provider: {e}") from e

        # NO FALLBACK - fail explicitly if COM not configured
        raise RuntimeError(
            "No email provider configured. Email Helper requires Outlook COM interface.\n"
            "Please ensure:\n"
            "1. You are running on Windows\n"
            "2. Microsoft Outlook is installed\n"
            "3. pywin32 is installed: pip install pywin32\n"
            "4. Set use_com_backend=True in backend/core/config.py"
        )

    return _email_provider


def get_email_provider() -> EmailProvider:
    """FastAPI dependency for email provider."""
    return get_email_provider_instance()
