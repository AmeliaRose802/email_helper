"""Core interfaces for Email Helper components.

This module defines the abstract base classes and interfaces that
provide structure and contracts for the email helper system components.
Using these interfaces promotes loose coupling and makes the system
more testable and extensible.

The interfaces define the core contracts for:
- EmailProvider: Email access and manipulation
- AIProvider: AI processing and classification
- StorageProvider: Data persistence and retrieval

These interfaces enable dependency injection and make it easier to
create mock implementations for testing.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class EmailProvider(ABC):
    """Abstract interface for email access providers."""
    
    @abstractmethod
    def get_emails(self, folder_name: str = "Inbox", count: int = 50) -> List[Dict[str, Any]]:
        """Retrieve emails from the specified folder."""
        pass
    
    @abstractmethod
    def move_email(self, email_id: str, destination_folder: str) -> bool:
        """Move an email to the specified folder."""
        pass
    
    @abstractmethod
    def get_email_body(self, email_id: str) -> str:
        """Get the full body text of an email."""
        pass


class AIProvider(ABC):
    """Abstract interface for AI processing providers."""
    
    @abstractmethod
    def classify_email(self, email_content: str, context: str = "") -> Dict[str, Any]:
        """Classify an email and return structured results."""
        pass
    
    @abstractmethod
    def analyze_batch(self, emails: List[Dict[str, Any]], context: str = "") -> Dict[str, Any]:
        """Analyze a batch of emails for relationships and priority."""
        pass


class StorageProvider(ABC):
    """Abstract interface for data storage providers."""
    
    @abstractmethod
    def save_tasks(self, tasks: List[Dict[str, Any]]) -> bool:
        """Save task data to persistent storage."""
        pass
    
    @abstractmethod
    def load_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load tasks from persistent storage."""
        pass
    
    @abstractmethod
    def save_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Save accuracy metrics to storage."""
        pass


class OutlookManagerInterface(ABC):
    """Abstract interface for Outlook email management."""
    
    @abstractmethod
    def connect_to_outlook(self) -> None:
        """Connect to Outlook application."""
        pass
    
    @abstractmethod
    def get_recent_emails(self, days_back: Optional[int] = None, max_emails: int = 10000) -> List[Any]:
        """Retrieve recent emails from Outlook."""
        pass
    
    @abstractmethod
    def move_email_to_category(self, email: Any, category: str) -> bool:
        """Move an email to a category folder."""
        pass


class TaskPersistenceInterface(ABC):
    """Abstract interface for task persistence operations."""
    
    @abstractmethod
    def save_outstanding_tasks(self, summary_sections: Dict[str, List[Dict]], 
                              batch_timestamp: Optional[str] = None) -> None:
        """Save outstanding tasks to persistent storage."""
        pass
    
    @abstractmethod
    def load_outstanding_tasks(self, auto_clean_expired: bool = True) -> Dict[str, List[Dict]]:
        """Load outstanding tasks from persistent storage."""
        pass
    
    @abstractmethod
    def mark_tasks_completed(self, completed_task_ids: List[str], 
                            completion_timestamp: Optional[str] = None) -> None:
        """Mark tasks as completed."""
        pass


class DatabaseManagerInterface(ABC):
    """Abstract interface for database management."""
    
    @abstractmethod
    def get_connection(self):
        """Get database connection context manager."""
        pass
    
    @abstractmethod
    def get_connection_sync(self):
        """Get synchronous database connection."""
        pass