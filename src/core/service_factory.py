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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from outlook_manager import OutlookManager
from ai_processor import AIProcessor
from email_analyzer import EmailAnalyzer
from summary_generator import SummaryGenerator
from email_processor import EmailProcessor
from task_persistence import TaskPersistence
from accuracy_tracker import AccuracyTracker
from database.migrations import DatabaseMigrations
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
        
    def get_outlook_manager(self) -> EmailProvider:
        """Get OutlookManager instance."""
        return self._get_or_create('outlook_manager', lambda: OutlookManager())
        
    def get_email_analyzer(self) -> 'EmailAnalyzer':
        """Get EmailAnalyzer instance."""
        return self._get_or_create('email_analyzer', lambda: EmailAnalyzer())
        
    def get_ai_processor(self) -> AIProvider:
        """Get AIProcessor instance with dependencies."""
        def create_ai_processor():
            email_analyzer = self.get_email_analyzer()
            ai_processor = AIProcessor(email_analyzer)
            # Set circular dependency
            email_analyzer.ai_processor = ai_processor
            return ai_processor
            
        return self._get_or_create('ai_processor', create_ai_processor)
        
    def get_summary_generator(self) -> 'SummaryGenerator':
        """Get SummaryGenerator instance."""
        return self._get_or_create('summary_generator', lambda: SummaryGenerator())
        
    def get_email_processor(self) -> 'EmailProcessor':
        """Get EmailProcessor instance with all dependencies."""
        def create_email_processor():
            return EmailProcessor(
                self.get_outlook_manager(),
                self.get_ai_processor(),
                self.get_email_analyzer(),
                self.get_summary_generator()
            )
            
        return self._get_or_create('email_processor', create_email_processor)
        
    def get_task_persistence(self) -> StorageProvider:
        """Get TaskPersistence instance."""
        return self._get_or_create('task_persistence', lambda: TaskPersistence())
        
    def get_accuracy_tracker(self) -> 'AccuracyTracker':
        """Get AccuracyTracker instance."""
        from .config import config
        runtime_data_dir = config.get('storage.base_dir')
        return self._get_or_create('accuracy_tracker', lambda: AccuracyTracker(runtime_data_dir))
    
    def get_database_migrations(self) -> 'DatabaseMigrations':
        """Get DatabaseMigrations instance."""
        from .config import config
        db_path = config.get_storage_path('database/email_helper.db')
        return self._get_or_create('database_migrations', lambda: DatabaseMigrations(db_path))
        
    def reset(self):
        """Reset all instances (useful for testing)."""
        self._instances.clear()
        self.logger.debug("All service instances reset")
        
    def override_service(self, service_name: str, instance: Any):
        """Override a service with a custom instance (for testing)."""
        self._instances[service_name] = instance
        self.logger.debug(f"Service {service_name} overridden with custom instance")