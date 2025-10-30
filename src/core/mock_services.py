"""Mock service implementations for testing.

This module provides mock implementations of all service interfaces,
enabling easy testing without real dependencies like Outlook, Azure OpenAI,
or file system operations.

Usage:
    from src.core.mock_services import MockOutlookManager, MockTaskPersistence
    
    # In tests
    factory = ServiceFactory()
    factory.override_service('outlook_manager', MockOutlookManager())
    factory.override_service('task_persistence', MockTaskPersistence())
"""

from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from datetime import datetime
import sqlite3

from .interfaces import (
    OutlookManagerInterface,
    TaskPersistenceInterface,
    DatabaseManagerInterface
)


class MockOutlookManager(OutlookManagerInterface):
    """Mock implementation of OutlookManager for testing."""
    
    def __init__(self):
        self.connected = False
        self.emails = []
        self.conversations = []
        self.moved_emails = []
        self.categorized_emails = []
        
    def connect_to_outlook(self) -> None:
        """Mock connection to Outlook."""
        self.connected = True
    
    def get_recent_emails(self, days_back: Optional[int] = None, max_emails: int = 10000) -> List[Any]:
        """Return mock emails."""
        return self.emails[:max_emails]
    
    def get_emails_with_full_conversations(self, days_back: int = 7, max_emails: int = 10000) -> List[Tuple[str, Dict[str, Any]]]:
        """Return mock conversations."""
        return self.conversations[:max_emails]
    
    def move_email_to_category(self, email: Any, category: str) -> bool:
        """Mock email move operation."""
        self.moved_emails.append({'email': email, 'category': category})
        return True
    
    def get_email_body(self, email: Any) -> str:
        """Return mock email body."""
        return getattr(email, 'body', 'Mock email body')
    
    def apply_categorization_batch(self, email_suggestions: List[Dict[str, Any]], 
                                   confirmation_callback: Optional[Any] = None) -> Tuple[int, int]:
        """Mock batch categorization."""
        self.categorized_emails.extend(email_suggestions)
        return len(email_suggestions), 0
    
    def move_emails_to_done_folder(self, entry_ids: List[str]) -> Tuple[int, int]:
        """Mock move to done folder."""
        return len(entry_ids), 0


class MockTaskPersistence(TaskPersistenceInterface):
    """Mock implementation of TaskPersistence for testing."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or "/tmp/mock_tasks"
        self.outstanding_tasks = {
            'required_actions': [],
            'team_actions': [],
            'completed_team_actions': [],
            'optional_actions': [],
            'job_listings': [],
            'optional_events': [],
            'fyi_notices': [],
            'newsletters': []
        }
        self.completed_tasks = []
        
    def save_outstanding_tasks(self, summary_sections: Dict[str, List[Dict]], 
                              batch_timestamp: Optional[str] = None) -> None:
        """Mock save operation."""
        for section_key, tasks in summary_sections.items():
            if section_key in self.outstanding_tasks:
                self.outstanding_tasks[section_key].extend(tasks)
    
    def load_outstanding_tasks(self, auto_clean_expired: bool = True) -> Dict[str, List[Dict]]:
        """Return mock outstanding tasks."""
        return self.outstanding_tasks.copy()
    
    def mark_tasks_completed(self, completed_task_ids: List[str], 
                            completion_timestamp: Optional[str] = None) -> None:
        """Mock task completion."""
        for section_key in self.outstanding_tasks:
            self.outstanding_tasks[section_key] = [
                task for task in self.outstanding_tasks[section_key]
                if task.get('task_id') not in completed_task_ids
            ]
    
    def get_entry_ids_for_tasks(self, task_ids: List[str]) -> List[str]:
        """Return mock entry IDs."""
        entry_ids = []
        for section_key in self.outstanding_tasks:
            for task in self.outstanding_tasks[section_key]:
                if task.get('task_id') in task_ids:
                    entry_ids.extend(task.get('_entry_ids', []))
        return entry_ids
    
    def get_comprehensive_summary(self, current_summary_sections: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Return mock comprehensive summary."""
        result = self.outstanding_tasks.copy()
        for section_key, tasks in current_summary_sections.items():
            if section_key in result:
                result[section_key].extend(tasks)
        return result
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Return mock statistics."""
        total = sum(len(tasks) for tasks in self.outstanding_tasks.values())
        return {
            'outstanding_total': total,
            'completed_total': len(self.completed_tasks),
            'old_tasks_count': 0,
            'old_tasks': [],
            'sections_breakdown': {
                section: len(tasks) for section, tasks in self.outstanding_tasks.items()
            }
        }


class MockDatabaseManager(DatabaseManagerInterface):
    """Mock implementation of DatabaseManager for testing."""
    
    def __init__(self):
        self.db_path = ":memory:"
        self._setup_mock_database()
    
    def _setup_mock_database(self):
        """Set up in-memory database schema for testing."""
        # This creates a persistent in-memory connection
        # All connections will share the same memory database
        self._shared_connection = sqlite3.connect(":memory:", check_same_thread=False)
        self._shared_connection.row_factory = sqlite3.Row
        
        # Create basic tables
        self._shared_connection.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'todo',
                priority TEXT DEFAULT 'medium',
                category TEXT,
                due_date TIMESTAMP,
                tags TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                email_id TEXT,
                user_id INTEGER
            )
        ''')
        
        self._shared_connection.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                sender TEXT NOT NULL,
                recipient TEXT,
                content TEXT,
                received_date TIMESTAMP,
                category TEXT,
                confidence REAL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER
            )
        ''')
        
        self._shared_connection.commit()
    
    @contextmanager
    def get_connection(self):
        """Get mock database connection context manager."""
        # Return the shared connection
        try:
            yield self._shared_connection
        except Exception:
            self._shared_connection.rollback()
            raise
    
    def get_connection_sync(self):
        """Get mock synchronous database connection."""
        return self._shared_connection


# Mock email object for testing
class MockEmail:
    """Mock email object that mimics Outlook COM email."""
    
    def __init__(self, subject: str, sender: str, body: str, entry_id: str = None):
        self.Subject = subject
        self.SenderEmailAddress = sender
        self.Body = body
        self.EntryID = entry_id or f"mock_entry_{hash(subject)}"
        self.ReceivedTime = datetime.now()
        self.Class = 43  # olMail constant
        self.ConversationID = f"conv_{hash(subject) % 1000}"
        self.ConversationTopic = subject
        
    def Move(self, folder):
        """Mock move operation."""
        pass
    
    def Save(self):
        """Mock save operation."""
        pass
