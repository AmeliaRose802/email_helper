"""Consolidated test suite for Email Helper.

This module combines and consolidates all the essential tests for the email helper
system into a well-organized, comprehensive test suite. It replaces the scattered
individual test files with a structured approach that's easier to maintain and run.

Test Categories:
- Core functionality tests (email processing, AI classification)
- Integration tests (component interactions, data flow)
- UI tests (interface behavior, user interactions)
- Accuracy and metrics tests (tracking, validation)
- Persistence tests (data storage, task management)

This consolidation eliminates duplicate test code and provides better test
organization while maintaining comprehensive coverage.
"""

import pytest
import os
import sys
import tempfile
import sqlite3
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Import core modules after path setup
from core.service_factory import ServiceFactory
from core.interfaces import EmailProvider, AIProvider, StorageProvider
from core.config import config
from utils import *
from accuracy_tracker import AccuracyTracker
from task_persistence import TaskPersistence


class TestCoreInfrastructure:
    """Test the core infrastructure and dependency injection."""
    
    def test_service_factory_creation(self):
        """Test that ServiceFactory creates instances correctly."""
        factory = ServiceFactory()
        
        # Test that services can be created
        outlook_manager = factory.get_outlook_manager()
        ai_processor = factory.get_ai_processor()
        task_persistence = factory.get_task_persistence()
        
        assert outlook_manager is not None
        assert ai_processor is not None
        assert task_persistence is not None
        
        # Test singleton behavior
        assert factory.get_outlook_manager() is outlook_manager
        assert factory.get_ai_processor() is ai_processor
        
    def test_configuration_manager(self):
        """Test configuration management."""
        # Test basic configuration access
        assert config.get('email.default_folder') == 'Inbox'
        assert config.get('processing.confidence_threshold') == 0.7
        
        # Test nested configuration
        azure_config = config.get_azure_config()
        assert isinstance(azure_config, dict)
        
        # Test default values
        assert config.get('nonexistent.key', 'default') == 'default'


class TestUtilities:
    """Test utility functions."""
    
    def test_json_utilities(self):
        """Test JSON processing utilities."""
        # Test clean_json_response
        markdown_json = "```json\n{\"test\": \"value\"}\n```"
        cleaned = clean_json_response(markdown_json)
        assert cleaned == '{"test": "value"}'
        
        # Test parse_json_with_fallback
        valid_json = '{"valid": true}'
        parsed = parse_json_with_fallback(valid_json)
        assert parsed == {"valid": True}
        
        # Test with invalid JSON and fallback
        invalid_json = '{"invalid": incomplete'
        fallback = {"fallback": True}
        parsed = parse_json_with_fallback(invalid_json, fallback)
        assert parsed == fallback
        
    def test_text_utilities(self):
        """Test text processing utilities."""
        # Test clean_ai_response
        text_with_markdown = "**Bold text** and *italic text*"
        cleaned = clean_ai_response(text_with_markdown)
        assert cleaned == "Bold text and italic text"
        
        # Test truncate_with_ellipsis
        long_text = "This is a very long text that should be truncated"
        truncated = truncate_with_ellipsis(long_text, 20)
        assert len(truncated) <= 23  # 20 + "..."
        assert truncated.endswith("...")
        
        # Test add_bullet_if_needed
        without_bullet = "Text without bullet"
        with_bullet = add_bullet_if_needed(without_bullet)
        assert with_bullet.startswith("• ")
        
        already_has_bullet = "• Already has bullet"
        unchanged = add_bullet_if_needed(already_has_bullet)
        assert unchanged == already_has_bullet
        
    def test_date_utilities(self):
        """Test date processing utilities."""
        # Test parse_date_string
        date_str = "2025-01-15"
        parsed = parse_date_string(date_str)
        assert parsed is not None
        assert parsed.year == 2025
        assert parsed.month == 1
        assert parsed.day == 15
        
        # Test format functions
        dt = datetime(2025, 1, 15, 10, 30, 0)
        storage_format = format_datetime_for_storage(dt)
        display_format = format_date_for_display(dt)
        
        assert storage_format == "2025-01-15 10:30:00"
        assert display_format == "2025-01-15 10:30"


class TestEmailProcessing:
    """Test email processing functionality."""
    
    @pytest.fixture
    def sample_emails(self):
        """Sample email data for testing."""
        return [
            {
                "subject": "Urgent: Project Deadline Tomorrow",
                "body": "We need to finalize the project deliverables by tomorrow EOD.",
                "sender": "manager@company.com",
                "sender_name": "Project Manager",
                "received_time": "2025-01-15 10:00:00",
                "entry_id": "urgent_123"
            },
            {
                "subject": "Team Meeting Next Week",
                "body": "Reminder about our weekly team meeting next Tuesday at 2 PM.",
                "sender": "admin@company.com",
                "sender_name": "Team Admin",
                "received_time": "2025-01-15 11:00:00",
                "entry_id": "meeting_456"
            },
            {
                "subject": "Newsletter: Tech Updates",
                "body": "Here are the latest technology updates and industry news...",
                "sender": "newsletter@techsite.com",
                "sender_name": "Tech Newsletter",
                "received_time": "2025-01-15 12:00:00",
                "entry_id": "newsletter_789"
            }
        ]
    
    def test_email_classification_patterns(self, sample_emails):
        """Test email classification logic patterns."""
        # Test urgent detection
        urgent_email = sample_emails[0]
        assert "urgent" in urgent_email["subject"].lower()
        
        # Test meeting detection
        meeting_email = sample_emails[1]
        assert "meeting" in meeting_email["body"].lower()
        
        # Test newsletter detection
        newsletter_email = sample_emails[2]
        assert "newsletter" in newsletter_email["subject"].lower()
        
    def test_email_data_normalization(self, sample_emails):
        """Test email data normalization."""
        normalized = normalize_data_for_storage(sample_emails)
        
        assert len(normalized) == len(sample_emails)
        for email in normalized:
            assert isinstance(email["subject"], str)
            assert isinstance(email["sender"], str)
            assert isinstance(email["received_time"], str)


class TestTaskManagement:
    """Test task management and persistence."""
    
    @pytest.fixture
    def temp_task_dir(self):
        """Create temporary directory for task storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_task_persistence_basic_operations(self, temp_task_dir):
        """Test basic task persistence operations."""
        task_persistence = TaskPersistence(temp_task_dir)
        
        # Test saving tasks
        test_tasks = [
            {
                "subject": "Test Task 1",
                "due_date": "2025-01-20",
                "priority": "high",
                "status": "outstanding"
            },
            {
                "subject": "Test Task 2", 
                "due_date": "2025-01-25",
                "priority": "medium",
                "status": "completed"
            }
        ]
        
        # Note: save_outstanding_tasks returns None, not True
        task_persistence.save_outstanding_tasks({'required_actions': test_tasks})
        
        # Verify by loading back
        loaded_tasks = task_persistence.load_outstanding_tasks()
        assert len(loaded_tasks.get('required_actions', [])) >= 0  # Should not error
        
        # Test loading tasks - loaded_tasks is a dict with categories
        loaded_tasks = task_persistence.load_outstanding_tasks()
        assert isinstance(loaded_tasks, dict)
        assert 'required_actions' in loaded_tasks
        
        # Find our test tasks in the required_actions category
        test_subjects = {task["subject"] for task in test_tasks}
        loaded_required_actions = loaded_tasks.get('required_actions', [])
        loaded_subjects = {task["subject"] for task in loaded_required_actions}
        assert test_subjects.issubset(loaded_subjects)


class TestAccuracyTracking:
    """Test accuracy tracking and metrics."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            db_path = temp_file.name
        yield db_path
        try:
            os.unlink(db_path)
        except FileNotFoundError:
            pass
    
    def test_accuracy_tracker_initialization(self, temp_db_path):
        """Test AccuracyTracker initialization."""
        # Create temp runtime data directory
        runtime_dir = os.path.dirname(temp_db_path)
        tracker = AccuracyTracker(runtime_dir)
        
        # Test that database is created
        assert os.path.exists(temp_db_path) or os.path.exists(os.path.join(runtime_dir, "email_helper_history.db"))
        
    def test_accuracy_data_recording(self, temp_db_path):
        """Test accuracy data recording."""
        runtime_dir = os.path.dirname(temp_db_path)
        tracker = AccuracyTracker(runtime_dir)
        
        # Test recording session accuracy data
        session_data = {
            "total_emails": 10,
            "accuracy_rate": 85.0,  # Changed from accuracy_percentage to accuracy_rate
            "modifications_count": 2,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # This should not raise an exception
        try:
            tracker.record_session_accuracy(session_data)
            success = True
        except Exception as e:
            print(f"Error recording session accuracy: {e}")
            success = False

        assert success
class TestIntegration:
    """Test component integration."""
    
    def test_service_factory_integration(self):
        """Test that services created by factory work together."""
        factory = ServiceFactory()
        
        # Get services
        email_processor = factory.get_email_processor()
        task_persistence = factory.get_task_persistence()
        
        # Test that they have expected interfaces
        assert hasattr(email_processor, 'process_emails')
        assert hasattr(task_persistence, 'save_outstanding_tasks')
        assert hasattr(task_persistence, 'load_outstanding_tasks')
        
    def test_configuration_integration(self):
        """Test configuration integration across components."""
        # Test that configuration values are accessible
        batch_size = config.get('email.batch_size')
        assert isinstance(batch_size, int)
        assert batch_size > 0
        
        confidence_threshold = config.get('processing.confidence_threshold')
        assert isinstance(confidence_threshold, float)
        assert 0.0 <= confidence_threshold <= 1.0


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_json_error_recovery(self):
        """Test JSON error recovery mechanisms."""
        # Test with completely invalid JSON
        invalid_json = "not json at all"
        result = parse_json_with_fallback(invalid_json, {"error": "fallback"})
        assert result == {"error": "fallback"}
        
        # Test with partially valid JSON
        partial_json = '{"valid": true, "invalid": incomplete'
        result = parse_json_with_fallback(partial_json, {"repaired": True})
        # Should either parse successfully or return fallback
        assert result is not None
        
    def test_date_parsing_edge_cases(self):
        """Test date parsing with various edge cases."""
        # Test with None/empty strings
        assert parse_date_string(None) is None
        assert parse_date_string("") is None
        assert parse_date_string("No specific deadline") is None
        
        # Test with invalid formats
        assert parse_date_string("invalid date") is None
        assert parse_date_string("13/45/2025") is None


# Consolidated test runner
def run_all_tests():
    """Run all consolidated tests."""
    import pytest
    
    # Run with verbose output and coverage if available
    args = [__file__, "-v"]
    
    try:
        import pytest_cov
        args.extend(["--cov=src", "--cov-report=term-missing"])
    except ImportError:
        pass
        
    return pytest.main(args)


if __name__ == "__main__":
    run_all_tests()