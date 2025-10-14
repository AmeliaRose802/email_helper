"""Adapter layer for Email Helper backend integration.

This package provides adapters that wrap existing Email Helper services
(OutlookManager, AIProcessor) to implement clean interface contracts
defined in src/core/interfaces.py.

The adapters enable:
- Backend API integration without code duplication
- Clean separation between COM/AI logic and API layer
- Easy testing through dependency injection
- Backward compatibility with existing code

Adapters:
- OutlookEmailAdapter: Wraps OutlookManager for EmailProvider interface
- AIProcessorAdapter: Wraps AIProcessor for AIProvider interface
"""

from .outlook_email_adapter import OutlookEmailAdapter
from .ai_processor_adapter import AIProcessorAdapter

__all__ = [
    'OutlookEmailAdapter',
    'AIProcessorAdapter',
]
