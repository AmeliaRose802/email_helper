"""
Services Package for Email Helper

This package contains service layer classes that handle business logic
and coordinate between GUI components and backend modules.
"""

# Service layer classes
from .email_service import EmailService
from .ui_service import UIService
from .notification_service import NotificationService

__all__ = [
    'EmailService',
    'UIService', 
    'NotificationService'
]