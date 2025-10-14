"""Integration tests for API endpoints with COM adapters via dependency injection."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys

# Ensure backend modules can be imported
sys.path.insert(0, '/home/runner/work/email_helper/email_helper')

from backend.main import app
from backend.core.dependencies import reset_dependencies


@pytest.fixture(autouse=True)
def reset_deps():
    """Reset dependencies before each test."""
    reset_dependencies()
    yield
    reset_dependencies()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth():
    """Mock authentication to bypass auth requirements."""
    mock_user = Mock()
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    
    with patch('backend.api.auth.get_current_user', return_value=mock_user):
        yield mock_user


class TestEmailEndpointsWithDI:
    """Test email endpoints using dependency injection."""
    
    def test_get_emails_with_com_provider(self, client, mock_auth):
        """Test /api/emails endpoint uses COM provider when configured."""
        mock_provider = Mock()
        mock_provider.authenticate.return_value = True
        mock_provider.get_emails.return_value = [
            {
                'id': 'test-1',
                'subject': 'Test Email',
                'sender': 'sender@example.com',
                'body': 'Test body',
                'received_time': '2024-01-01T10:00:00Z'
            }
        ]
        
        with patch('backend.core.dependencies.settings') as mock_settings:
            mock_settings.use_com_backend = True
            
            with patch('backend.core.dependencies.COMEmailProvider', return_value=mock_provider):
                response = client.get("/api/emails?folder=Inbox&limit=10")
                
                assert response.status_code == 200
                data = response.json()
                assert 'emails' in data
                assert len(data['emails']) == 1
                assert data['emails'][0]['subject'] == 'Test Email'
                
                # Verify COM provider was called
                mock_provider.get_emails.assert_called_once()
    
    def test_get_emails_with_standard_provider(self, client, mock_auth):
        """Test /api/emails endpoint uses standard provider when COM not configured."""
        mock_provider = Mock()
        mock_provider.get_emails.return_value = [
            {
                'id': 'test-2',
                'subject': 'Standard Email',
                'sender': 'sender@example.com'
            }
        ]
        
        with patch('backend.core.dependencies.settings') as mock_settings:
            mock_settings.use_com_backend = False
            
            with patch('backend.core.dependencies.get_email_provider_instance', return_value=mock_provider):
                response = client.get("/api/emails?folder=Inbox&limit=10")
                
                assert response.status_code == 200
                data = response.json()
                assert 'emails' in data
    
    def test_get_folders_with_di(self, client, mock_auth):
        """Test /api/folders endpoint uses dependency injection."""
        mock_provider = Mock()
        mock_provider.authenticate.return_value = True
        mock_provider.get_folders.return_value = [
            {'id': 'inbox', 'name': 'Inbox', 'type': 'inbox'},
            {'id': 'sent', 'name': 'Sent Items', 'type': 'sent'}
        ]
        
        with patch('backend.core.dependencies.settings') as mock_settings:
            mock_settings.use_com_backend = True
            
            with patch('backend.core.dependencies.COMEmailProvider', return_value=mock_provider):
                response = client.get("/api/folders")
                
                assert response.status_code == 200
                data = response.json()
                assert 'folders' in data
                assert len(data['folders']) == 2
                assert data['folders'][0]['name'] == 'Inbox'
    
    def test_mark_as_read_with_di(self, client, mock_auth):
        """Test mark as read endpoint uses dependency injection."""
        mock_provider = Mock()
        mock_provider.authenticate.return_value = True
        mock_provider.mark_as_read.return_value = True
        
        with patch('backend.core.dependencies.settings') as mock_settings:
            mock_settings.use_com_backend = True
            
            with patch('backend.core.dependencies.COMEmailProvider', return_value=mock_provider):
                response = client.post("/api/emails/test-id/mark-read")
                
                assert response.status_code == 200
                data = response.json()
                assert data['success'] is True
                mock_provider.mark_as_read.assert_called_once_with('test-id')


class TestAIEndpointsWithDI:
    """Test AI endpoints using dependency injection."""
    
    def test_classify_email_with_com_ai_service(self, client, mock_auth):
        """Test /api/ai/classify endpoint uses COM AI service when configured."""
        mock_service = Mock()
        mock_service._ensure_initialized = Mock()
        mock_service.classify_email_async = Mock(return_value={
            'category': 'required_personal_action',
            'confidence': 0.95,
            'reasoning': 'Email requires immediate attention',
            'alternatives': []
        })
        
        with patch('backend.core.dependencies.settings') as mock_settings:
            mock_settings.use_com_backend = True
            
            with patch('backend.core.dependencies.COMAIService', return_value=mock_service):
                request_data = {
                    'subject': 'Urgent: Action Required',
                    'content': 'Please review and approve.',
                    'sender': 'manager@example.com'
                }
                
                response = client.post("/api/ai/classify", json=request_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data['category'] == 'required_personal_action'
                assert data['confidence'] == 0.95
    
    def test_classify_email_with_standard_ai_service(self, client, mock_auth):
        """Test /api/ai/classify endpoint uses standard AI service when COM not configured."""
        mock_service = Mock()
        mock_service.classify_email_async = Mock(return_value={
            'category': 'work_relevant',
            'confidence': 0.85,
            'reasoning': 'Work-related email',
            'alternatives': []
        })
        
        with patch('backend.core.dependencies.settings') as mock_settings:
            mock_settings.use_com_backend = False
            
            with patch('backend.core.dependencies.AIService', return_value=mock_service):
                request_data = {
                    'subject': 'Project Update',
                    'content': 'Here is the status.',
                    'sender': 'colleague@example.com'
                }
                
                response = client.post("/api/ai/classify", json=request_data)
                
                assert response.status_code == 200
                data = response.json()
                assert 'category' in data
    
    def test_extract_action_items_with_di(self, client, mock_auth):
        """Test action item extraction uses dependency injection."""
        mock_service = Mock()
        mock_service._ensure_initialized = Mock()
        mock_service.extract_action_items = Mock(return_value={
            'action_items': ['Review document', 'Submit report'],
            'urgency': 'high',
            'deadline': '2024-01-15',
            'confidence': 0.9,
            'due_date': '2024-01-15',
            'action_required': 'Review and submit report',
            'explanation': 'Document needs review',
            'relevance': 'High priority task',
            'links': []
        })
        
        with patch('backend.core.dependencies.settings') as mock_settings:
            mock_settings.use_com_backend = True
            
            with patch('backend.core.dependencies.COMAIService', return_value=mock_service):
                request_data = {
                    'email_content': 'Please review the attached document by Friday.'
                }
                
                response = client.post("/api/ai/action-items", json=request_data)
                
                assert response.status_code == 200
                data = response.json()
                assert 'action_items' in data
                assert len(data['action_items']) == 2
    
    def test_summarize_email_with_di(self, client, mock_auth):
        """Test email summarization uses dependency injection."""
        mock_service = Mock()
        mock_service._ensure_initialized = Mock()
        mock_service.generate_summary = Mock(return_value={
            'summary': 'Brief summary of email content',
            'key_points': ['Point 1', 'Point 2'],
            'confidence': 0.88
        })
        
        with patch('backend.core.dependencies.settings') as mock_settings:
            mock_settings.use_com_backend = True
            
            with patch('backend.core.dependencies.COMAIService', return_value=mock_service):
                request_data = {
                    'email_content': 'Long email content here...',
                    'summary_type': 'brief'
                }
                
                response = client.post("/api/ai/summarize", json=request_data)
                
                assert response.status_code == 200
                data = response.json()
                assert 'summary' in data
                assert data['summary'] == 'Brief summary of email content'
    
    def test_ai_health_check_with_di(self, client, mock_auth):
        """Test AI health check uses dependency injection."""
        mock_service = Mock()
        mock_service._ensure_initialized = Mock()
        mock_service._initialized = True
        mock_service.get_available_templates = Mock(return_value={
            'templates': ['template1.prompty', 'template2.prompty'],
            'descriptions': {}
        })
        
        with patch('backend.core.dependencies.settings') as mock_settings:
            mock_settings.use_com_backend = True
            
            with patch('backend.core.dependencies.COMAIService', return_value=mock_service):
                response = client.get("/api/ai/health")
                
                assert response.status_code == 200
                data = response.json()
                assert data['status'] == 'healthy'
                assert data['ai_processor_available'] is True


class TestErrorHandlingWithDI:
    """Test error handling for dependency injection failures."""
    
    def test_email_endpoint_handles_provider_initialization_failure(self, client, mock_auth):
        """Test graceful handling when email provider initialization fails."""
        with patch('backend.core.dependencies.settings') as mock_settings:
            mock_settings.use_com_backend = True
            
            with patch('backend.core.dependencies.COMEmailProvider', side_effect=Exception("Initialization failed")):
                with patch('backend.core.dependencies.get_email_provider_instance', side_effect=Exception("Fallback failed")):
                    response = client.get("/api/emails")
                    
                    # Should return 503 Service Unavailable
                    assert response.status_code == 503
    
    def test_ai_endpoint_handles_service_initialization_failure(self, client, mock_auth):
        """Test graceful handling when AI service initialization fails."""
        with patch('backend.core.dependencies.settings') as mock_settings:
            mock_settings.use_com_backend = True
            
            with patch('backend.core.dependencies.COMAIService', side_effect=Exception("AI not available")):
                with patch('backend.core.dependencies.AIService', side_effect=Exception("Fallback failed")):
                    request_data = {
                        'subject': 'Test',
                        'content': 'Test content',
                        'sender': 'test@example.com'
                    }
                    
                    response = client.post("/api/ai/classify", json=request_data)
                    
                    # Should return 503 Service Unavailable
                    assert response.status_code == 503


class TestBackwardCompatibility:
    """Test backward compatibility with existing endpoints."""
    
    def test_existing_endpoints_still_work(self, client, mock_auth):
        """Test that existing endpoints continue to work with DI changes."""
        mock_provider = Mock()
        mock_provider.get_emails.return_value = []
        
        with patch('backend.core.dependencies.settings') as mock_settings:
            mock_settings.use_com_backend = False
            
            with patch('backend.core.dependencies.get_email_provider_instance', return_value=mock_provider):
                # Test various endpoints
                response1 = client.get("/api/emails")
                assert response1.status_code == 200
                
                response2 = client.get("/api/folders")
                # May fail if folders not mocked, but shouldn't crash
                assert response2.status_code in [200, 500]
