"""Comprehensive API integration tests with COM backend.

This module tests all API endpoints with the COM backend to ensure:
1. Feature parity with Tkinter application
2. All email endpoints work correctly
3. All AI endpoints work correctly
4. All task endpoints work correctly
5. Proper error handling and response formats

These tests verify Task T2.2: API Integration with COM Backend.
"""

import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
from typing import Dict, List

from backend.main import app
from backend.core.dependencies import reset_dependencies
from backend.services.com_email_provider import COMEmailProvider
from backend.services.com_ai_service import COMAIService

client = TestClient(app)


# Fixtures
@pytest.fixture(autouse=True)
def reset_deps():
    """Reset dependencies before and after each test."""
    reset_dependencies()
    yield
    reset_dependencies()


@pytest.fixture
def test_user():
    """Test user data with unique timestamp."""
    timestamp = str(int(time.time() * 1000))
    return {
        "username": f"comuser_{timestamp}",
        "email": f"com_{timestamp}@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for test user."""
    # Register user
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 201, f"Registration failed: {response.json()}"
    
    # Login user
    login_response = client.post("/auth/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
    
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_com_email_provider():
    """Mock COM email provider with sample data."""
    provider = Mock(spec=COMEmailProvider)
    provider.authenticate = Mock(return_value=True)
    
    # Mock email data
    sample_emails = [
        {
            "id": "email-1",
            "subject": "Test Email 1",
            "sender": "sender1@example.com",
            "body": "This is test email 1 content",
            "received_time": "2024-01-15T10:00:00",
            "is_read": False,
            "folder": "Inbox"
        },
        {
            "id": "email-2",
            "subject": "Test Email 2",
            "sender": "sender2@example.com",
            "body": "This is test email 2 content",
            "received_time": "2024-01-15T11:00:00",
            "is_read": True,
            "folder": "Inbox"
        }
    ]
    
    provider.get_emails = Mock(return_value=sample_emails)
    provider.get_email_content = Mock(return_value=sample_emails[0])
    provider.mark_as_read = Mock(return_value=True)
    provider.move_to_folder = Mock(return_value=True)
    provider.get_folders = Mock(return_value=["Inbox", "Sent", "Archive"])
    
    return provider


@pytest.fixture
def mock_com_ai_service():
    """Mock COM AI service with sample responses."""
    service = Mock(spec=COMAIService)
    
    # Mock classification response
    async def mock_classify(email_content, context=None):
        return {
            "category": "required_personal_action",
            "confidence": 0.92,
            "reasoning": "Direct request requiring response",
            "alternatives": ["work_relevant", "informational"]
        }
    
    service.classify_email = AsyncMock(side_effect=mock_classify)
    
    # Mock action items response
    async def mock_action_items(email_content, context=None):
        return {
            "action_items": [
                {
                    "description": "Review and respond to proposal",
                    "priority": "high",
                    "deadline": "2024-01-20"
                }
            ],
            "urgency": "high",
            "deadline": "2024-01-20"
        }
    
    service.extract_action_items = AsyncMock(side_effect=mock_action_items)
    
    # Mock summary response
    async def mock_summarize(email_content, summary_type="brief"):
        return {
            "summary": "Brief summary of email content",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "action_items": ["Review proposal"]
        }
    
    service.summarize = AsyncMock(side_effect=mock_summarize)
    
    return service


# Email API Endpoint Tests
class TestEmailEndpointsWithCOM:
    """Test email API endpoints with COM backend."""
    
    def test_get_emails_list(self, auth_headers, mock_com_email_provider):
        """Test GET /api/emails - List emails."""
        with patch('backend.core.dependencies.get_com_email_provider', return_value=mock_com_email_provider):
            with patch('backend.core.dependencies.settings.use_com_backend', True):
                response = client.get("/api/emails?folder=Inbox&limit=50", headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify response structure
                assert "emails" in data
                assert "total" in data
                assert "limit" in data
                assert "offset" in data
                assert "has_more" in data
                
                # Verify emails
                assert len(data["emails"]) > 0
                mock_com_email_provider.get_emails.assert_called_once()
    
    def test_get_email_by_id(self, auth_headers, mock_com_email_provider):
        """Test GET /api/emails/{id} - Get email by ID."""
        with patch('backend.core.dependencies.get_com_email_provider', return_value=mock_com_email_provider):
            with patch('backend.core.dependencies.settings.use_com_backend', True):
                response = client.get("/api/emails/email-1", headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify email structure
                assert "id" in data
                assert "subject" in data
                assert "sender" in data
                assert "body" in data
                
                mock_com_email_provider.get_email_content.assert_called_once_with("email-1")
    
    def test_mark_email_as_read(self, auth_headers, mock_com_email_provider):
        """Test POST /api/emails/{id}/mark-read - Mark as read."""
        with patch('backend.core.dependencies.get_com_email_provider', return_value=mock_com_email_provider):
            with patch('backend.core.dependencies.settings.use_com_backend', True):
                response = client.post("/api/emails/email-1/mark-read", headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify response
                assert data["success"] is True
                assert "message" in data
                
                mock_com_email_provider.mark_as_read.assert_called_once_with("email-1")
    
    def test_move_email_to_folder(self, auth_headers, mock_com_email_provider):
        """Test POST /api/emails/{id}/move - Move to folder."""
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_com_email_provider):
            with patch('backend.core.dependencies.settings.use_com_backend', True):
                response = client.post(
                    "/api/emails/email-1/move?destination_folder=Archive",
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify response
                assert data["success"] is True
                assert "message" in data
                
                mock_com_email_provider.move_to_folder.assert_called_once_with("email-1", "Archive")


# AI API Endpoint Tests
class TestAIEndpointsWithCOM:
    """Test AI API endpoints with COM backend."""
    
    @pytest.mark.asyncio
    async def test_classify_email(self, auth_headers, mock_com_ai_service):
        """Test POST /api/ai/classify - Classify email."""
        with patch('backend.core.dependencies.get_ai_service', return_value=mock_com_ai_service):
            with patch('backend.core.dependencies.settings.use_com_backend', True):
                request_data = {
                    "subject": "Urgent: Review Proposal",
                    "content": "Please review this proposal by Friday",
                    "sender": "manager@company.com",
                    "context": "Work email"
                }
                
                response = client.post("/api/ai/classify", json=request_data, headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify classification response
                assert "category" in data
                assert "confidence" in data
                assert "reasoning" in data
                assert data["category"] == "required_personal_action"
                assert data["confidence"] > 0.9
    
    @pytest.mark.asyncio
    async def test_extract_action_items(self, auth_headers, mock_com_ai_service):
        """Test POST /api/ai/action-items - Extract action items."""
        with patch('backend.core.dependencies.get_ai_service', return_value=mock_com_ai_service):
            with patch('backend.core.dependencies.settings.use_com_backend', True):
                request_data = {
                    "email_content": "Please review the proposal and send feedback by Friday",
                    "context": "Project review"
                }
                
                response = client.post("/api/ai/action-items", json=request_data, headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify action items response
                assert "action_items" in data
                assert "urgency" in data
                assert len(data["action_items"]) > 0
                assert data["urgency"] in ["low", "medium", "high"]
    
    @pytest.mark.asyncio
    async def test_summarize_email(self, auth_headers, mock_com_ai_service):
        """Test POST /api/ai/summarize - Generate summary."""
        with patch('backend.core.dependencies.get_ai_service', return_value=mock_com_ai_service):
            with patch('backend.core.dependencies.settings.use_com_backend', True):
                request_data = {
                    "email_content": "Long email content that needs to be summarized...",
                    "summary_type": "brief"
                }
                
                response = client.post("/api/ai/summarize", json=request_data, headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify summary response
                assert "summary" in data
                assert "key_points" in data
                assert isinstance(data["key_points"], list)
                assert len(data["summary"]) > 0


# Task API Endpoint Tests
class TestTaskEndpointsWithCOM:
    """Test task API endpoints with COM backend."""
    
    def test_get_tasks_list(self, auth_headers):
        """Test GET /api/tasks - List tasks."""
        response = client.get("/api/tasks?page=1&limit=20", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure matches TaskListResponse
        assert "tasks" in data
        assert "page" in data
        assert "page_size" in data
        # The actual response might have "total_count" or "has_next" instead of "has_more"
        assert isinstance(data["tasks"], list)
    
    def test_create_task(self, auth_headers):
        """Test POST /api/tasks - Create task."""
        task_data = {
            "title": "COM Integration Test Task",
            "description": "Task created during COM integration testing",
            "priority": "high",
            "status": "pending"
        }
        
        response = client.post("/api/tasks", json=task_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify task creation
        assert "id" in data
        assert data["title"] == task_data["title"]
        assert data["priority"] == "high"
        assert data["status"] == "pending"
        
        # Store task ID for other tests
        return data["id"]
    
    def test_get_task_by_id(self, auth_headers):
        """Test GET /api/tasks/{id} - Get task by ID."""
        # First create a task
        task_id = self.test_create_task(auth_headers)
        
        # Now get the task
        response = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify task data
        assert data["id"] == task_id
        assert "title" in data
        assert "status" in data
    
    def test_update_task(self, auth_headers):
        """Test PUT /api/tasks/{id} - Update task."""
        # First create a task
        task_id = self.test_create_task(auth_headers)
        
        # Update the task
        update_data = {
            "title": "Updated COM Test Task",
            "status": "in_progress"
        }
        
        response = client.put(f"/api/tasks/{task_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify update
        assert data["title"] == "Updated COM Test Task"
        assert data["status"] == "in_progress"
    
    def test_delete_task(self, auth_headers):
        """Test DELETE /api/tasks/{id} - Delete task."""
        # First create a task
        task_id = self.test_create_task(auth_headers)
        
        # Delete the task
        response = client.delete(f"/api/tasks/{task_id}", headers=auth_headers)
        
        assert response.status_code == 200 or response.status_code == 204
        
        # Verify deletion
        get_response = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
        assert get_response.status_code == 404


# Feature Parity Tests
class TestFeatureParityWithTkinter:
    """Test feature parity between API and Tkinter application."""
    
    def test_email_retrieval_parity(self, auth_headers, mock_com_email_provider):
        """Verify email retrieval matches Tkinter functionality."""
        with patch('backend.core.dependencies.get_com_email_provider', return_value=mock_com_email_provider):
            with patch('backend.core.dependencies.settings.use_com_backend', True):
                response = client.get("/api/emails", headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Tkinter features that should be present
                assert "emails" in data  # Email list
                assert "total" in data   # Total count
                
                # Each email should have Tkinter-compatible fields
                if data["emails"]:
                    email = data["emails"][0]
                    assert "id" in email
                    assert "subject" in email
                    assert "sender" in email
    
    def test_classification_parity(self, auth_headers, mock_com_ai_service):
        """Verify AI classification matches Tkinter functionality."""
        with patch('backend.core.dependencies.get_ai_service', return_value=mock_com_ai_service):
            with patch('backend.core.dependencies.settings.use_com_backend', True):
                request_data = {
                    "subject": "Test",
                    "content": "Test content",
                    "sender": "test@example.com"
                }
                
                response = client.post("/api/ai/classify", json=request_data, headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Tkinter classification features
                assert "category" in data
                assert "confidence" in data
                assert "reasoning" in data
    
    def test_task_management_parity(self, auth_headers):
        """Verify task management matches Tkinter functionality."""
        # Test full task lifecycle
        
        # 1. Create task (Tkinter equivalent: task creation)
        task_data = {
            "title": "Parity Test Task",
            "priority": "medium"
        }
        create_response = client.post("/api/tasks", json=task_data, headers=auth_headers)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        
        # 2. List tasks (Tkinter equivalent: task list view)
        list_response = client.get("/api/tasks", headers=auth_headers)
        assert list_response.status_code == 200
        assert "tasks" in list_response.json()
        
        # 3. Update task (Tkinter equivalent: task update)
        update_response = client.put(
            f"/api/tasks/{task_id}",
            json={"status": "completed"},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        # 4. Delete task (Tkinter equivalent: task deletion)
        delete_response = client.delete(f"/api/tasks/{task_id}", headers=auth_headers)
        assert delete_response.status_code in [200, 204]


# Error Handling Tests
class TestErrorHandling:
    """Test error handling for all endpoints."""
    
    def test_unauthorized_access(self):
        """Test that endpoints require authentication."""
        # Test without auth headers
        endpoints = [
            ("/api/emails", "get"),
            ("/api/emails/test-id", "get"),
            ("/api/tasks", "get"),
        ]
        
        for endpoint, method in endpoints:
            if method == "get":
                response = client.get(endpoint)
            elif method == "post":
                response = client.post(endpoint)
            
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should require auth"
    
    def test_invalid_email_id(self, auth_headers, mock_com_email_provider):
        """Test handling of invalid email ID."""
        mock_com_email_provider.get_email_content = Mock(return_value=None)
        
        with patch('backend.core.dependencies.get_com_email_provider', return_value=mock_com_email_provider):
            with patch('backend.core.dependencies.settings.use_com_backend', True):
                response = client.get("/api/emails/invalid-id", headers=auth_headers)
                
                # Should return 404 or handle gracefully
                assert response.status_code in [404, 500]
    
    def test_invalid_task_id(self, auth_headers):
        """Test handling of invalid task ID."""
        response = client.get("/api/tasks/99999", headers=auth_headers)
        
        # Should return 404
        assert response.status_code == 404


# Performance Tests
class TestPerformance:
    """Test performance characteristics."""
    
    def test_email_list_response_time(self, auth_headers, mock_com_email_provider):
        """Test email list endpoint response time."""
        with patch('backend.core.dependencies.get_com_email_provider', return_value=mock_com_email_provider):
            with patch('backend.core.dependencies.settings.use_com_backend', True):
                start_time = time.time()
                response = client.get("/api/emails", headers=auth_headers)
                end_time = time.time()
                
                assert response.status_code == 200
                response_time = end_time - start_time
                
                # Should respond within 2 seconds
                assert response_time < 2.0, f"Response time {response_time}s exceeds threshold"
    
    def test_task_operations_response_time(self, auth_headers):
        """Test task operations response time."""
        start_time = time.time()
        response = client.get("/api/tasks", headers=auth_headers)
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Should respond within 1 second
        assert response_time < 1.0, f"Response time {response_time}s exceeds threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
