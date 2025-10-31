"""Outlook COM integration modules.

This package contains the Outlook COM integration code for email access.
These modules provide direct Windows COM interface access to Microsoft Outlook.

Modules:
    outlook_manager: Core OutlookManager class for Outlook COM operations
    adapters.outlook_email_adapter: EmailProvider adapter wrapping OutlookManager
    interfaces: Abstract base classes for email/AI/storage providers

Note: These modules require pywin32 and are Windows-only.
"""

from backend.services.outlook.outlook_manager import (
    OutlookManager,
    INBOX_CATEGORIES,
    NON_INBOX_CATEGORIES,
    CATEGORY_COLORS
)
from backend.services.outlook.interfaces import (
    EmailProvider,
    AIProvider,
    StorageProvider
)

__all__ = [
    'OutlookManager',
    'INBOX_CATEGORIES',
    'NON_INBOX_CATEGORIES',
    'CATEGORY_COLORS',
    'EmailProvider',
    'AIProvider',
    'StorageProvider',
]
