"""Service Factory for Email Helper dependency injection.

This module provides a centralized factory for creating and managing
all service instances in the email helper application. It implements
a dependency injection pattern that promotes loose coupling and
makes the system more testable.

The ServiceFactory:
- Creates instances with proper dependency injection
- Manages singleton instances where appropriate
- Provides configuration-based service selection
- Enables easy mocking for testing
- Handles service lifecycle management

Usage:
    factory = ServiceFactory()
    email_processor = factory.get_email_processor()
    ai_processor = factory.get_ai_processor()
"""

import logging
from typing import Dict, Any, Optional
import sys
import os

# Add src directory to path for imports
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import modules from src directory
from ai_processor import AIProcessor
from task_persistence import TaskPersistence
from .interfaces import EmailProvider, AIProvider, StorageProvider


class ServiceFactory:
    """Factory for creating and managing service instances."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._instances: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
    def _get_or_create(self, service_name: str, factory_func):
        """Get existing instance or create new one."""
        if service_name not in self._instances:
            self.logger.debug(f"Creating new instance of {service_name}")
            self._instances[service_name] = factory_func()
        return self._instances[service_name]
        
    def get_ai_processor(self) -> AIProvider:
        """Get AIProcessor instance."""
        return self._get_or_create('ai_processor', lambda: AIProcessor())
        
    def get_task_persistence(self) -> StorageProvider:
        """Get TaskPersistence instance."""
        return self._get_or_create('task_persistence', lambda: TaskPersistence())
        
    def reset(self):
        """Reset all instances (useful for testing)."""
        self._instances.clear()
        self.logger.debug("All service instances reset")
        
    def override_service(self, service_name: str, instance: Any):
        """Override a service with a custom instance (for testing)."""
        self._instances[service_name] = instance
        self.logger.debug(f"Service {service_name} overridden with custom instance")