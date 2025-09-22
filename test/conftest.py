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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def temp_database():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
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
        'subject': 'Test Meeting Request',
        'body': 'Please join our team meeting tomorrow at 2 PM to discuss project updates.',
        'sender': 'manager@company.com',
        'sender_name': 'Project Manager',
        'received_time': '2025-01-15 10:00:00',
        'entry_id': 'test_entry_123',
        'message_id': 'msg_123@company.com'
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
    mock.azure_config = {'endpoint': 'test', 'api_key': 'test'}
    mock.classify_email.return_value = 'required_personal_action'
    mock.classify_email_improved.return_value = 'required_personal_action'
    mock.extract_action_items.return_value = {
        'action_required': 'Review document',
        'due_date': 'Tomorrow',
        'priority': 'high'
    }
    mock.get_username.return_value = 'test_user'
    mock.load_learning_data.return_value = {}
    return mock

@pytest.fixture
def mock_email_analyzer():
    """Mock EmailAnalyzer for testing."""
    mock = Mock()
    mock.extract_due_date_intelligent.return_value = 'January 16, 2025'
    mock.extract_links_intelligent.return_value = []
    mock.is_job_related.return_value = False
    mock.extract_qualification_match.return_value = '0%'
    return mock

@pytest.fixture
def mock_task_persistence():
    """Mock TaskPersistence for testing."""
    mock = Mock()
    mock.save_task.return_value = True
    mock.load_tasks.return_value = []
    mock.mark_completed.return_value = True
    mock.get_task_by_id.return_value = None
    return mock

@pytest.fixture
def sample_classification_result():
    """Sample AI classification result."""
    return {
        'category': 'meeting_request',
        'priority': 'high',
        'action_required': True,
        'confidence': 0.95
    }

@pytest.fixture
def sample_action_items():
    """Sample action items data structure."""
    return {
        'required_actions': [
            {
                'subject': 'Test Action Item',
                'sender': 'test@example.com',
                'due_date': '2025-01-20',
                'action_required': 'Review document',
                'explanation': 'Test explanation',
                'task_id': 'test_123',
                'batch_count': 1
            }
        ],
        'team_actions': [],
        'job_listings': [],
        'optional_events': [],
        'fyi_items': []
    }

@pytest.fixture
def mock_azure_config():
    """Mock Azure configuration."""
    return {
        'endpoint': 'https://test.openai.azure.com/',
        'api_key': 'test_key_123',
        'api_version': '2024-02-15-preview',
        'deployment_name': 'test-deployment'
    }

@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path, monkeypatch):
    """Set up isolated test environment."""
    # Create temporary directories for test data
    test_data_dir = tmp_path / "test_data"
    test_data_dir.mkdir()
    
    # Mock environment variables
    monkeypatch.setenv('AZURE_OPENAI_ENDPOINT', 'https://test.openai.azure.com/')
    monkeypatch.setenv('AZURE_OPENAI_API_KEY', 'test_key_123')
    
    # Return paths for use in tests
    return {
        'data_dir': str(test_data_dir),
        'tmp_path': str(tmp_path)
    }

@pytest.fixture
def email_factory():
    """Factory for creating test email data."""
    class EmailFactory:
        @staticmethod
        def create_meeting_request(subject="Team Meeting", sender="manager@company.com", days_ahead=1):
            return {
                'subject': subject,
                'body': f"Please join our {subject.lower()} tomorrow at 2 PM.",
                'sender': sender,
                'sender_name': sender.split('@')[0].title(),
                'received_time': (datetime.now() + timedelta(days=days_ahead)).isoformat(),
                'entry_id': f'entry_{hash(subject)}',
                'message_id': f'msg_{hash(subject)}@company.com'
            }
        
        @staticmethod
        def create_fyi_notice(subject="Company Update", sender="hr@company.com"):
            return {
                'subject': subject,
                'body': f"This is an FYI notice about {subject.lower()}.",
                'sender': sender,
                'sender_name': 'HR Department',
                'received_time': datetime.now().isoformat(),
                'entry_id': f'entry_{hash(subject)}',
                'message_id': f'msg_{hash(subject)}@company.com'
            }
        
        @staticmethod
        def create_job_listing(subject="Software Engineer Position", sender="recruiter@company.com"):
            return {
                'subject': subject,
                'body': f"We have an exciting opportunity for a {subject}. Apply now!",
                'sender': sender,
                'sender_name': 'Technical Recruiter',
                'received_time': datetime.now().isoformat(),
                'entry_id': f'entry_{hash(subject)}',
                'message_id': f'msg_{hash(subject)}@company.com'
            }
        
        @staticmethod
        def create_email_batch(count=5):
            emails = []
            for i in range(count):
                if i % 3 == 0:
                    emails.append(EmailFactory.create_meeting_request(f"Meeting {i}"))
                elif i % 3 == 1:
                    emails.append(EmailFactory.create_fyi_notice(f"Notice {i}"))
                else:
                    emails.append(EmailFactory.create_job_listing(f"Job {i}"))
            return emails
    
    return EmailFactory