"""Comprehensive test utilities and helpers for Email Helper test suite.

This module provides reusable test utilities including:
- Mock factories for common dependencies
- Test data generators
- Assertion helpers
- Fixture builders
- Common test patterns

NO EMOJIS in this file - Windows console compatibility.
"""

import os
import sys
import json
import tempfile
import sqlite3
from typing import Dict, Any, List, Optional, Callable
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path if not already present
src_path = os.path.join(os.path.dirname(__file__), "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


# ============================================================================
# Mock Factories
# ============================================================================

class MockFactory:
    """Factory for creating commonly-used mock objects."""
    
    @staticmethod
    def create_outlook_manager(
        connected: bool = True,
        emails: Optional[List[Dict[str, Any]]] = None,
        folders: Optional[List[Dict[str, Any]]] = None
    ) -> Mock:
        """Create a mock OutlookManager.
        
        Args:
            connected: Whether the manager is connected
            emails: List of emails to return from get_emails()
            folders: List of folders to return from get_folders()
            
        Returns:
            Mock: Configured OutlookManager mock
        """
        manager = Mock()
        manager.connect = Mock(return_value=connected)
        manager.is_connected = connected
        manager.get_emails = Mock(return_value=emails or [])
        manager.get_folder_emails = Mock(return_value=emails or [])
        manager.get_folders = Mock(return_value=folders or [])
        manager.mark_as_read = Mock(return_value=True)
        manager.move_email = Mock(return_value=True)
        manager.delete_email = Mock(return_value=True)
        manager.disconnect = Mock()
        return manager
    
    @staticmethod
    def create_ai_processor(
        classification: str = "required_personal_action",
        action_items: Optional[Dict[str, Any]] = None,
        summary: Optional[str] = None,
        confidence: float = 0.85
    ) -> Mock:
        """Create a mock AIProcessor.
        
        Args:
            classification: Default classification result
            action_items: Default action items result
            summary: Default summary result
            confidence: Default confidence score
            
        Returns:
            Mock: Configured AIProcessor mock
        """
        processor = Mock()
        
        processor.azure_config = {
            "endpoint": "https://test.openai.azure.com/",
            "api_key": "test-key",
            "deployment_name": "test-deployment",
            "api_version": "2024-02-15-preview"
        }
        
        processor.classify_email = Mock(return_value=classification)
        processor.classify_email_improved = Mock(return_value=classification)
        
        processor.extract_action_items = Mock(return_value=action_items or {
            "action_required": "Test action",
            "due_date": "Tomorrow",
            "priority": "medium",
            "confidence": confidence
        })
        
        processor.generate_summary = Mock(return_value=summary or "Test summary")
        
        processor.execute_prompty = Mock(return_value={
            "category": classification,
            "confidence": confidence
        })
        
        processor.get_username = Mock(return_value="test_user")
        processor.load_learning_data = Mock(return_value={})
        
        processor.CONFIDENCE_THRESHOLDS = {
            'optional_action': 0.8,
            'work_relevant': 0.8,
            'required_personal_action': 0.9
        }
        
        return processor
    
    @staticmethod
    def create_task_persistence(
        existing_tasks: Optional[List[Dict[str, Any]]] = None
    ) -> Mock:
        """Create a mock TaskPersistence.
        
        Args:
            existing_tasks: List of existing tasks
            
        Returns:
            Mock: Configured TaskPersistence mock
        """
        persistence = Mock()
        persistence.save_task = Mock(return_value="task-123")
        persistence.get_task = Mock(return_value=existing_tasks[0] if existing_tasks else None)
        persistence.get_all_tasks = Mock(return_value=existing_tasks or [])
        persistence.update_task = Mock(return_value=True)
        persistence.delete_task = Mock(return_value=True)
        persistence.mark_completed = Mock(return_value=True)
        return persistence
    
    @staticmethod
    def create_database_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
        """Create a temporary in-memory database connection.
        
        Args:
            db_path: Optional path to database file (uses :memory: if not provided)
            
        Returns:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(db_path or ":memory:")
        conn.row_factory = sqlite3.Row
        return conn


# ============================================================================
# Test Data Generators
# ============================================================================

class DataGenerator:
    """Generator for test data objects."""
    
    @staticmethod
    def generate_email_id(prefix: str = "test") -> str:
        """Generate a unique email ID.
        
        Args:
            prefix: Prefix for the ID
            
        Returns:
            str: Unique email ID
        """
        timestamp = datetime.now().timestamp()
        return f"{prefix}-{int(timestamp * 1000000)}"
    
    @staticmethod
    def create_email(
        subject: str = "Test Email",
        body: str = "Test email body",
        sender: str = "sender@example.com",
        sender_name: str = "Test Sender",
        received_time: Optional[datetime] = None,
        is_read: bool = False,
        categories: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a test email object.
        
        Args:
            subject: Email subject
            body: Email body
            sender: Sender email address
            sender_name: Sender display name
            received_time: Time email was received
            is_read: Whether email is read
            categories: Email categories
            **kwargs: Additional email fields
            
        Returns:
            dict: Email object
        """
        email_id = DataGenerator.generate_email_id()
        received = received_time or datetime.now()
        
        email = {
            "id": email_id,
            "entry_id": email_id,
            "message_id": f"{email_id}@example.com",
            "subject": subject,
            "body": body,
            "from": sender,
            "sender": sender,
            "sender_name": sender_name,
            "from_name": sender_name,
            "to": "recipient@example.com",
            "received_time": received.isoformat() if isinstance(received, datetime) else received,
            "is_read": is_read,
            "categories": categories or [],
            "conversation_id": f"conv-{email_id}",
            "has_attachments": False,
            "importance": "normal"
        }
        
        email.update(kwargs)
        return email
    
    @staticmethod
    def create_email_batch(
        count: int,
        base_subject: str = "Test Email",
        time_offset_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Create a batch of test emails.
        
        Args:
            count: Number of emails to create
            base_subject: Base subject line
            time_offset_hours: Hours between emails
            
        Returns:
            list: Batch of email objects
        """
        emails = []
        base_time = datetime.now()
        
        for i in range(count):
            offset = timedelta(hours=i * (time_offset_hours / count))
            received = base_time - offset
            
            email = DataGenerator.create_email(
                subject=f"{base_subject} {i + 1}",
                body=f"This is test email number {i + 1}.",
                sender=f"sender{i}@example.com",
                sender_name=f"Sender {i + 1}",
                received_time=received,
                is_read=(i % 3 == 0)  # Every 3rd email is read
            )
            emails.append(email)
        
        return emails
    
    @staticmethod
    def create_action_item_email(
        action: str = "Review document",
        due_date: str = "Tomorrow",
        priority: str = "high"
    ) -> Dict[str, Any]:
        """Create an email with action items.
        
        Args:
            action: Action description
            due_date: Due date for action
            priority: Action priority
            
        Returns:
            dict: Email with action items
        """
        return DataGenerator.create_email(
            subject=f"Action Required: {action}",
            body=f"""
Hi,

Please complete the following action:

ACTION: {action}
DUE DATE: {due_date}
PRIORITY: {priority}

This requires your immediate attention.

Thanks,
Sender
""",
            sender="action-sender@example.com",
            sender_name="Action Sender"
        )
    
    @staticmethod
    def create_meeting_email(
        meeting_time: Optional[datetime] = None,
        duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """Create a meeting request email.
        
        Args:
            meeting_time: Meeting start time
            duration_minutes: Meeting duration
            
        Returns:
            dict: Meeting request email
        """
        meeting_dt = meeting_time or (datetime.now() + timedelta(days=1))
        end_time = meeting_dt + timedelta(minutes=duration_minutes)
        
        return DataGenerator.create_email(
            subject=f"Meeting: Project Sync",
            body=f"""
You are invited to a meeting.

TIME: {meeting_dt.strftime('%Y-%m-%d %I:%M %p')}
DURATION: {duration_minutes} minutes
LOCATION: Conference Room A

Please confirm your attendance.
""",
            sender="organizer@example.com",
            sender_name="Meeting Organizer"
        )
    
    @staticmethod
    def create_newsletter_email(
        newsletter_name: str = "Tech Newsletter"
    ) -> Dict[str, Any]:
        """Create a newsletter email.
        
        Args:
            newsletter_name: Name of newsletter
            
        Returns:
            dict: Newsletter email
        """
        return DataGenerator.create_email(
            subject=f"{newsletter_name}: Weekly Update",
            body=f"""
{newsletter_name} - This Week's Top Stories

1. Technology Update
2. Industry News
3. Product Launches

Read more at our website...

Unsubscribe | Manage Preferences
""",
            sender=f"noreply@{newsletter_name.lower().replace(' ', '')}.com",
            sender_name=newsletter_name
        )
    
    @staticmethod
    def create_task(
        title: str = "Test Task",
        description: str = "Test task description",
        due_date: Optional[str] = None,
        priority: str = "medium",
        status: str = "pending"
    ) -> Dict[str, Any]:
        """Create a test task object.
        
        Args:
            title: Task title
            description: Task description
            due_date: Task due date
            priority: Task priority
            status: Task status
            
        Returns:
            dict: Task object
        """
        return {
            "id": DataGenerator.generate_email_id("task"),
            "title": title,
            "description": description,
            "due_date": due_date or (datetime.now() + timedelta(days=7)).isoformat(),
            "priority": priority,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }


# ============================================================================
# Assertion Helpers
# ============================================================================

class AssertionHelper:
    """Helper functions for common test assertions."""
    
    @staticmethod
    def assert_email_structure(email: Dict[str, Any]) -> None:
        """Assert email has required structure.
        
        Args:
            email: Email object to validate
            
        Raises:
            AssertionError: If structure is invalid
        """
        required_fields = ["id", "subject", "body", "from", "received_time"]
        
        for field in required_fields:
            assert field in email, f"Email missing required field: {field}"
        
        assert isinstance(email["id"], str), "Email ID must be string"
        assert isinstance(email["subject"], str), "Subject must be string"
        assert isinstance(email["body"], str), "Body must be string"
        assert len(email["subject"]) > 0, "Subject cannot be empty"
    
    @staticmethod
    def assert_classification_valid(
        classification: str,
        valid_categories: Optional[List[str]] = None
    ) -> None:
        """Assert classification is valid.
        
        Args:
            classification: Classification result
            valid_categories: List of valid categories
            
        Raises:
            AssertionError: If classification is invalid
        """
        if valid_categories is None:
            valid_categories = [
                "required_personal_action",
                "optional_action",
                "work_relevant",
                "fyi_team",
                "newsletter",
                "spam"
            ]
        
        assert classification in valid_categories, \
            f"Invalid classification: {classification}. Must be one of {valid_categories}"
    
    @staticmethod
    def assert_action_items_structure(action_items: Dict[str, Any]) -> None:
        """Assert action items have valid structure.
        
        Args:
            action_items: Action items object to validate
            
        Raises:
            AssertionError: If structure is invalid
        """
        assert "action_required" in action_items, "Missing action_required field"
        assert "confidence" in action_items, "Missing confidence field"
        
        confidence = action_items["confidence"]
        assert isinstance(confidence, (int, float)), "Confidence must be numeric"
        assert 0 <= confidence <= 1, "Confidence must be between 0 and 1"
    
    @staticmethod
    def assert_task_structure(task: Dict[str, Any]) -> None:
        """Assert task has valid structure.
        
        Args:
            task: Task object to validate
            
        Raises:
            AssertionError: If structure is invalid
        """
        required_fields = ["id", "title", "description", "status"]
        
        for field in required_fields:
            assert field in task, f"Task missing required field: {field}"
        
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        assert task["status"] in valid_statuses, \
            f"Invalid status: {task['status']}. Must be one of {valid_statuses}"
    
    @staticmethod
    def assert_database_has_table(conn: sqlite3.Connection, table_name: str) -> None:
        """Assert database has a specific table.
        
        Args:
            conn: Database connection
            table_name: Name of table to check
            
        Raises:
            AssertionError: If table doesn't exist
        """
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        result = cursor.fetchone()
        assert result is not None, f"Table {table_name} does not exist"
    
    @staticmethod
    def assert_mock_called_with_email(mock: Mock, email_id: str) -> None:
        """Assert mock was called with specific email ID.
        
        Args:
            mock: Mock object to check
            email_id: Expected email ID
            
        Raises:
            AssertionError: If mock wasn't called with email_id
        """
        found = False
        for call in mock.call_args_list:
            args, kwargs = call
            if email_id in args or email_id in kwargs.values():
                found = True
                break
        
        assert found, f"Mock not called with email_id: {email_id}"


# ============================================================================
# Fixture Builders
# ============================================================================

class FixtureBuilder:
    """Builder for complex test fixtures."""
    
    @staticmethod
    def build_email_workflow_scenario(
        num_emails: int = 5,
        include_action_items: bool = True,
        include_meetings: bool = True,
        include_newsletters: bool = True
    ) -> Dict[str, Any]:
        """Build a complete email workflow scenario.
        
        Args:
            num_emails: Number of regular emails
            include_action_items: Include action item emails
            include_meetings: Include meeting requests
            include_newsletters: Include newsletters
            
        Returns:
            dict: Complete scenario with emails and expected results
        """
        emails = DataGenerator.create_email_batch(num_emails)
        
        if include_action_items:
            emails.append(DataGenerator.create_action_item_email())
            emails.append(DataGenerator.create_action_item_email(
                action="Approve budget",
                due_date="Friday",
                priority="critical"
            ))
        
        if include_meetings:
            emails.append(DataGenerator.create_meeting_email())
        
        if include_newsletters:
            emails.append(DataGenerator.create_newsletter_email())
        
        return {
            "emails": emails,
            "total_count": len(emails),
            "action_items_count": 2 if include_action_items else 0,
            "meetings_count": 1 if include_meetings else 0,
            "newsletters_count": 1 if include_newsletters else 0
        }
    
    @staticmethod
    def build_database_schema(conn: sqlite3.Connection) -> None:
        """Build standard test database schema.
        
        Args:
            conn: Database connection
        """
        cursor = conn.cursor()
        
        # Emails table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                body TEXT,
                sender TEXT,
                sender_name TEXT,
                received_time TEXT,
                is_read INTEGER DEFAULT 0,
                category TEXT,
                processed INTEGER DEFAULT 0
            )
        """)
        
        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                email_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                priority TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (email_id) REFERENCES emails(id)
            )
        """)
        
        # Classifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT,
                category TEXT NOT NULL,
                confidence REAL,
                created_at TEXT,
                FOREIGN KEY (email_id) REFERENCES emails(id)
            )
        """)
        
        conn.commit()


# ============================================================================
# Test Patterns
# ============================================================================

class TestPattern:
    """Common test patterns and utilities."""
    
    @staticmethod
    def with_temp_directory() -> tempfile.TemporaryDirectory:
        """Create a temporary directory for tests.
        
        Returns:
            TemporaryDirectory: Temporary directory context manager
        """
        return tempfile.TemporaryDirectory()
    
    @staticmethod
    def with_temp_file(suffix: str = ".txt", content: str = "") -> str:
        """Create a temporary file for tests.
        
        Args:
            suffix: File suffix
            content: Initial file content
            
        Returns:
            str: Path to temporary file
        """
        fd, path = tempfile.mkstemp(suffix=suffix)
        if content:
            os.write(fd, content.encode())
        os.close(fd)
        return path
    
    @staticmethod
    def capture_logs(logger_name: str) -> List[str]:
        """Capture log messages for testing.
        
        Args:
            logger_name: Name of logger to capture
            
        Returns:
            list: Captured log messages
        """
        import logging
        
        logs = []
        handler = logging.Handler()
        handler.emit = lambda record: logs.append(record.getMessage())
        
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)
        
        return logs
    
    @staticmethod
    def mock_datetime(fixed_time: datetime):
        """Mock datetime for testing.
        
        Args:
            fixed_time: Fixed datetime to return
            
        Returns:
            Mock: Mocked datetime
        """
        mock_dt = Mock()
        mock_dt.now = Mock(return_value=fixed_time)
        return patch('datetime.datetime', mock_dt)


# ============================================================================
# Cleanup Utilities
# ============================================================================

def cleanup_test_files(directory: str, pattern: str = "test_*") -> None:
    """Clean up test files in a directory.
    
    Args:
        directory: Directory to clean
        pattern: File pattern to match
    """
    from glob import glob
    
    for file_path in glob(os.path.join(directory, pattern)):
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception:
            pass  # Ignore cleanup errors


def reset_all_mocks(*mocks: Mock) -> None:
    """Reset multiple mock objects.
    
    Args:
        *mocks: Mock objects to reset
    """
    for mock in mocks:
        if hasattr(mock, 'reset_mock'):
            mock.reset_mock()
