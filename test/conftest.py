"""
Pytest configuration and shared fixtures for email helper tests.
"""
import pytest
import os
import sys
import tempfile
import sqlite3
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

@pytest.fixture
def temp_database():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        db_path = temp_file.name
    yield db_path
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass

@pytest.fixture
def sample_email_data():
    """Sample email data for testing."""
    return {
        "subject": "Test Meeting Request",
        "body": "Please join our team meeting tomorrow at 2 PM to discuss project updates.",
        "sender": "manager@company.com",
        "sender_name": "Project Manager",
        "received_time": "2025-01-15 10:00:00",
        "entry_id": "test_entry_123",
        "message_id": "msg_123@company.com"
    }

@pytest.fixture
def mock_outlook_manager():
    """Mock OutlookManager for testing."""
    mock = Mock()
    mock.connect.return_value = True
    mock.get_emails.return_value = []
    mock.get_folder_emails.return_value = []
    mock.is_connected = True
    return mock

@pytest.fixture  
def mock_ai_processor():
    """Mock AIProcessor for testing."""
    mock = Mock()
    mock.azure_config = {"endpoint": "test", "api_key": "test"}
    mock.classify_email.return_value = "required_personal_action"
    mock.classify_email_improved.return_value = "required_personal_action"
    mock.extract_action_items.return_value = {
        "action_required": "Review document",
        "due_date": "Tomorrow",
        "priority": "high"
    }
    mock.get_username.return_value = "test_user"
    mock.load_learning_data.return_value = {}
    return mock

