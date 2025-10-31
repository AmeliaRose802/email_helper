"""Tests for email API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from backend.main import app
from backend.services.email_provider import MockEmailProvider
from backend.core.dependencies import reset_dependencies

client = TestClient(app)


# Add fixture to reset dependencies between tests
@pytest.fixture(autouse=True)
def reset_deps():
    """Reset dependencies before and after each test."""
    reset_dependencies()
    yield
    reset_dependencies()


class TestEmailAPI:
    """Test email API endpoints."""
    
    @pytest.fixture
    def mock_provider(self):
        """Mock email provider for testing."""
        provider = MockEmailProvider()
        provider.authenticate({"test": "mock"})
        return provider
    
    def test_get_emails_success(self, mock_provider):
        """Test successful email retrieval."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            response = client.get("/api/emails")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "emails" in data
            assert "total" in data
            assert "offset" in data
            assert "limit" in data
            assert "has_more" in data
            
            assert len(data["emails"]) == 2
            assert data["total"] == 2
            assert data["offset"] == 0
            assert data["limit"] == 50
            assert data["has_more"] is False
    
    def test_get_emails_with_pagination(self, mock_provider):
        """Test email retrieval with pagination."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            response = client.get("/api/emails?limit=1&offset=0")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["emails"]) == 1
            assert data["limit"] == 1
            assert data["offset"] == 0
            assert data["has_more"] is True  # Since we requested exactly the limit
    
    def test_get_emails_with_folder(self, mock_provider):
        """Test email retrieval from specific folder."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            response = client.get("/api/emails?folder=Sent")
            
            assert response.status_code == 200
            data = response.json()
            
            # Mock provider returns empty list for non-Inbox folders
            assert len(data["emails"]) == 0
    

    def test_get_email_by_id_success(self, mock_provider):
        """Test successful email retrieval by ID."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            response = client.get("/api/emails/mock-email-1")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["id"] == "mock-email-1"
            assert data["subject"] == "Test Email 1"
            assert data["sender"] == "test1@example.com"
            assert "body" in data
    
    def test_get_email_by_id_not_found(self, mock_provider):
        """Test email retrieval for non-existing ID."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            response = client.get("/api/emails/non-existing")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["message"].lower()
    
    def test_mark_email_as_read_success(self, mock_provider):
        """Test successful marking email as read."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            response = client.post("/api/emails/mock-email-1/mark-read")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["email_id"] == "mock-email-1"
            assert "successfully" in data["message"].lower()
    
    def test_mark_email_as_read_failure(self, mock_provider):
        """Test failed marking email as read."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            response = client.post("/api/emails/non-existing/mark-read")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is False
            assert data["email_id"] == "non-existing"
    
    def test_move_email_success(self, mock_provider):
        """Test successful email move."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            response = client.post("/api/emails/mock-email-1/move?destination_folder=Sent")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["email_id"] == "mock-email-1"
            assert "sent" in data["message"].lower()
    
    def test_move_email_failure(self, mock_provider):
        """Test failed email move."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            response = client.post("/api/emails/non-existing/move?destination_folder=Sent")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is False
            assert data["email_id"] == "non-existing"
    
    def test_get_folders_success(self, mock_provider):
        """Test successful folder retrieval."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            response = client.get("/api/folders")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "folders" in data
            assert "total" in data
            
            assert len(data["folders"]) == 3
            assert data["total"] == 3
            
            # Check folder structure
            folder = data["folders"][0]
            assert "id" in folder
            assert "name" in folder
            assert "type" in folder
    
    def test_get_conversation_thread_success(self, mock_provider):
        """Test successful conversation thread retrieval."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            response = client.get("/api/conversations/conv-1")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["conversation_id"] == "conv-1"
            assert "emails" in data
            assert "total" in data
            
            assert len(data["emails"]) == 1
            assert data["total"] == 1
            assert data["emails"][0]["conversation_id"] == "conv-1"
    
    def test_get_conversation_thread_empty(self, mock_provider):
        """Test conversation thread retrieval for non-existing conversation."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            response = client.get("/api/conversations/non-existing")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["conversation_id"] == "non-existing"
            assert len(data["emails"]) == 0
            assert data["total"] == 0
    
    def test_batch_process_emails_success(self, mock_provider):
        """Test successful batch email processing."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            batch_request = {
                "emails": [
                    {"id": "mock-email-1"},
                    {"id": "mock-email-2"}
                ],
                "context": "test batch processing"
            }
            
            response = client.post("/api/emails/batch-process", json=batch_request)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["processed_count"] == 2
            assert data["successful_count"] == 2
            assert data["failed_count"] == 0
            assert len(data["results"]) == 2
            assert len(data["errors"]) == 0
            
            # Check result structure
            result = data["results"][0]
            assert "category" in result
            assert "confidence" in result
            assert "reasoning" in result
            assert "action_items" in result
            assert "priority" in result
    
    def test_batch_process_emails_with_failures(self, mock_provider):
        """Test batch email processing with some failures."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            mock_get_provider.return_value = mock_provider
            
            batch_request = {
                "emails": [
                    {"id": "mock-email-1"},
                    {"id": "non-existing"},
                    {"invalid": "data"}
                ]
            }
            
            response = client.post("/api/emails/batch-process", json=batch_request)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["processed_count"] == 3
            assert data["successful_count"] == 1  # Only mock-email-1 succeeds
            assert data["failed_count"] > 0
            assert len(data["results"]) == 1
            assert len(data["errors"]) > 0
    
    def test_api_parameter_validation(self):
        """Test API parameter validation."""
        # Test invalid limit values
        response = client.get("/api/emails?limit=0")
        assert response.status_code == 422  # Validation error
        
        response = client.get("/api/emails?limit=101")
        assert response.status_code == 422  # Validation error
        
        # Test invalid offset
        response = client.get("/api/emails?offset=-1")
        assert response.status_code == 422  # Validation error
    
    def test_api_error_handling(self):
        """Test API error handling for provider errors."""
        with patch('backend.services.email_provider.get_email_provider_instance') as mock_get_provider:
            # Mock provider that raises an exception
            mock_provider = Mock()
            mock_provider.get_emails.side_effect = Exception("Test error")
            mock_get_provider.return_value = mock_provider
            
            response = client.get("/api/emails")
            
            assert response.status_code == 500
            data = response.json()
            assert "Failed to retrieve emails" in data["message"]
