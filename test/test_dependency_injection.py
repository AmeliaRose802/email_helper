"""Tests demonstrating dependency injection patterns.

This test module shows how the new DI system works and validates
that services can be properly injected and mocked.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import directly to avoid circular dependencies
from core.mock_services import (
    MockOutlookManager,
    MockTaskPersistence,
    MockDatabaseManager,
    MockEmail
)
from core.interfaces import (
    OutlookManagerInterface,
    TaskPersistenceInterface,
    DatabaseManagerInterface
)


class TestServiceFactoryBasics:
    """Test ServiceFactory basic functionality without circular imports."""
    
    def test_factory_can_be_imported(self):
        """Test that factory can be imported and instantiated."""
        # Import here to test lazy loading
        from core.service_factory import ServiceFactory
        
        factory = ServiceFactory()
        assert factory is not None
        assert hasattr(factory, 'get_outlook_manager')
        assert hasattr(factory, 'get_task_persistence')
    
    def test_factory_reset_works(self):
        """Test that factory reset clears instances."""
        from core.service_factory import ServiceFactory
        
        factory = ServiceFactory()
        factory._instances['test'] = "test_value"
        
        assert factory.has_service('test')
        factory.reset()
        assert not factory.has_service('test')
    
    def test_factory_override(self):
        """Test that factory can override services."""
        from core.service_factory import ServiceFactory
        
        factory = ServiceFactory()
        mock = MockOutlookManager()
        
        factory.override_service('outlook_manager', mock)
        
        result = factory._instances.get('outlook_manager')
        assert result is mock


class TestMockOutlookManager:
    """Test MockOutlookManager functionality."""
    
    def test_mock_connection(self):
        """Test mock Outlook connection."""
        mock = MockOutlookManager()
        
        assert not mock.connected
        mock.connect_to_outlook()
        assert mock.connected
    
    def test_mock_email_retrieval(self):
        """Test mock email retrieval."""
        mock = MockOutlookManager()
        email1 = MockEmail("Test 1", "sender@test.com", "Body 1")
        email2 = MockEmail("Test 2", "sender@test.com", "Body 2")
        
        mock.emails = [email1, email2]
        
        result = mock.get_recent_emails(max_emails=10)
        assert len(result) == 2
        assert result[0] is email1
    
    def test_mock_email_categorization(self):
        """Test mock email categorization."""
        mock = MockOutlookManager()
        email = MockEmail("Test", "sender@test.com", "Body")
        
        result = mock.move_email_to_category(email, "work")
        
        assert result is True
        assert len(mock.moved_emails) == 1
        assert mock.moved_emails[0]['category'] == 'work'
    
    def test_mock_batch_categorization(self):
        """Test mock batch categorization."""
        mock = MockOutlookManager()
        
        suggestions = [
            {'email_object': MockEmail("Test 1", "s@test.com", "B1"), 'ai_suggestion': 'work'},
            {'email_object': MockEmail("Test 2", "s@test.com", "B2"), 'ai_suggestion': 'personal'}
        ]
        
        success, errors = mock.apply_categorization_batch(suggestions)
        
        assert success == 2
        assert errors == 0
        assert len(mock.categorized_emails) == 2


class TestMockTaskPersistence:
    """Test MockTaskPersistence functionality."""
    
    def test_mock_save_and_load(self):
        """Test mock task persistence save and load."""
        mock = MockTaskPersistence()
        
        tasks = {
            'required_actions': [
                {'task_id': '1', 'title': 'Test Task'}
            ]
        }
        
        mock.save_outstanding_tasks(tasks)
        result = mock.load_outstanding_tasks()
        
        assert len(result['required_actions']) == 1
        assert result['required_actions'][0]['title'] == 'Test Task'
    
    def test_mock_task_completion(self):
        """Test mock task completion."""
        mock = MockTaskPersistence()
        
        mock.outstanding_tasks['required_actions'] = [
            {'task_id': '1', 'title': 'Task 1'},
            {'task_id': '2', 'title': 'Task 2'}
        ]
        
        mock.mark_tasks_completed(['1'])
        result = mock.load_outstanding_tasks()
        
        assert len(result['required_actions']) == 1
        assert result['required_actions'][0]['task_id'] == '2'
    
    def test_mock_get_statistics(self):
        """Test mock task statistics."""
        mock = MockTaskPersistence()
        
        mock.outstanding_tasks['required_actions'] = [
            {'task_id': '1'},
            {'task_id': '2'}
        ]
        
        stats = mock.get_task_statistics()
        
        assert stats['outstanding_total'] == 2
        assert stats['sections_breakdown']['required_actions'] == 2


class TestMockDatabaseManager:
    """Test MockDatabaseManager functionality."""
    
    def test_mock_database_connection(self):
        """Test mock database connection."""
        mock = MockDatabaseManager()
        
        with mock.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM tasks")
            count = cursor.fetchone()[0]
            assert count == 0
    
    def test_mock_database_operations(self):
        """Test mock database CRUD operations."""
        mock = MockDatabaseManager()
        
        with mock.get_connection() as conn:
            conn.execute(
                "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
                ("Test Task", "Description", "todo")
            )
            conn.commit()
            
            cursor = conn.execute("SELECT * FROM tasks WHERE title = ?", ("Test Task",))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['title'] == "Test Task"
            assert row['status'] == "todo"


class TestDependencyInjectionPattern:
    """Test real-world dependency injection scenarios."""
    
    def test_service_with_injected_dependencies(self):
        """Test creating a service with injected mock dependencies."""
        # This demonstrates the pattern for testing services
        mock_persistence = MockTaskPersistence()
        mock_persistence.outstanding_tasks['required_actions'] = [
            {'task_id': '123', 'title': 'Important Task'}
        ]
        
        # In production code, you'd inject this into a service
        # For example: TaskService(task_persistence=mock_persistence)
        
        # Verify mock works as expected
        tasks = mock_persistence.load_outstanding_tasks()
        assert len(tasks['required_actions']) == 1
        assert tasks['required_actions'][0]['title'] == 'Important Task'
    
    def test_interfaces_are_properly_defined(self):
        """Test that interfaces have expected methods."""
        # Verify OutlookManagerInterface
        assert hasattr(OutlookManagerInterface, 'connect_to_outlook')
        assert hasattr(OutlookManagerInterface, 'get_recent_emails')
        assert hasattr(OutlookManagerInterface, 'move_email_to_category')
        
        # Verify TaskPersistenceInterface
        assert hasattr(TaskPersistenceInterface, 'save_outstanding_tasks')
        assert hasattr(TaskPersistenceInterface, 'load_outstanding_tasks')
        assert hasattr(TaskPersistenceInterface, 'mark_tasks_completed')
        
        # Verify DatabaseManagerInterface
        assert hasattr(DatabaseManagerInterface, 'get_connection')
        assert hasattr(DatabaseManagerInterface, 'get_connection_sync')
    
    def test_mock_email_object(self):
        """Test MockEmail helper class."""
        email = MockEmail(
            subject="Test Subject",
            sender="test@example.com",
            body="Test body content",
            entry_id="ENTRY123"
        )
        
        assert email.Subject == "Test Subject"
        assert email.SenderEmailAddress == "test@example.com"
        assert email.Body == "Test body content"
        assert email.EntryID == "ENTRY123"
        assert email.Class == 43  # olMail constant
        
        # Test mock methods
        email.Move(None)  # Should not raise
        email.Save()  # Should not raise


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
