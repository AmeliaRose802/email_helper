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
