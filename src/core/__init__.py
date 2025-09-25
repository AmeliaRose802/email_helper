"""Core business logic package for Email Helper.

This package contains the essential business logic classes organized for
better maintainability and testability. It provides:

- Service factory for dependency injection
- Base classes for common patterns
- Configuration management
- Core interfaces and abstractions

The core package promotes loose coupling between components and makes
the system more testable and extensible.
"""

from .service_factory import ServiceFactory
from .base_processor import BaseProcessor
from .interfaces import EmailProvider, AIProvider, StorageProvider

__all__ = [
    'ServiceFactory',
    'BaseProcessor', 
    'EmailProvider',
    'AIProvider',
    'StorageProvider'
]