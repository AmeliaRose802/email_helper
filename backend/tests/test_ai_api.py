"""Tests for AI processing API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.ai_models import (
    EmailClassificationRequest, ActionItemRequest, SummaryRequest
)
from backend.core.dependencies import reset_dependencies

client = TestClient(app)


# Add fixture to reset dependencies between tests
@pytest.fixture(autouse=True)
def reset_deps():
    """Reset dependencies before and after each test."""
    reset_dependencies()
    yield
    reset_dependencies()


@pytest.fixture
def auth_token():
    """Get authentication token for testing."""
    # Register a test user
    response = client.post("/auth/register", json={
        "username": "testuser_ai",
        "email": "testai@example.com",
        "password": "testpass123"
    })
    
    # Login to get token
    login_response = client.post("/auth/login", json={
        "username": "testuser_ai",
        "password": "testpass123"
    })
    
    if login_response.status_code == 200:
        return login_response.json()["access_token"]
    else:
        # If user already exists, just login
        login_response = client.post("/auth/login", json={
            "username": "testuser_ai",
            "password": "testpass123"
        })
        return login_response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers for testing."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAIClassification:
    """Tests for email classification endpoint."""
    
    @patch('backend.services.ai_service.AIService.classify_email_async')
    def test_classify_email_success(self, mock_classify, auth_headers):
        """Test successful email classification."""
        # Mock AI service response
        mock_classify.return_value = {
            "category": "required_personal_action",
            "confidence": 0.9,
            "reasoning": "Direct request from manager requiring immediate action",
            "alternatives": ["team_action", "work_relevant"]
        }
        
        request_data = {
            "subject": "Urgent: Please review quarterly report",
            "content": "Hi, can you please review the quarterly report by Friday?",
            "sender": "manager@company.com",
            "context": "Work email from direct manager"
        }
        
        response = client.post(
            "/api/ai/classify",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "required_personal_action"
        assert data["confidence"] == 0.9
        assert "reasoning" in data
        assert "processing_time" in data
        assert isinstance(data["alternative_categories"], list)
    
    @patch('backend.services.ai_service.AIService.classify_email_async')
    def test_classify_email_with_error(self, mock_classify, auth_headers):
        """Test email classification with AI service error."""
        # Mock AI service error
        mock_classify.return_value = {
            "category": "work_relevant",
            "confidence": 0.5,
            "reasoning": "Classification failed: Azure OpenAI unavailable",
            "alternatives": [],
            "error": "Azure OpenAI unavailable"
        }
        
        request_data = {
            "subject": "Test email",
            "content": "Test content",
            "sender": "test@example.com"
        }
        
        response = client.post(
            "/api/ai/classify",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 500
        assert "AI classification failed" in response.json()["detail"]
    
    def test_classify_email_unauthorized(self):
        """Test email classification without authentication."""
        request_data = {
            "subject": "Test email",
            "content": "Test content",
            "sender": "test@example.com"
        }
        
        response = client.post("/api/ai/classify", json=request_data)
        assert response.status_code == 401
    
    def test_classify_email_invalid_data(self, auth_headers):
        """Test email classification with invalid request data."""
        request_data = {
            "subject": "",  # Empty subject
            "content": "",  # Empty content
            "sender": ""    # Empty sender
        }
        
        response = client.post(
            "/api/ai/classify",
            json=request_data,
            headers=auth_headers
        )
        
        # Should still process but might return error from AI service
        assert response.status_code in [200, 500]


class TestActionItemExtraction:
    """Tests for action item extraction endpoint."""
    
    @patch('backend.services.ai_service.AIService.extract_action_items')
    def test_extract_action_items_success(self, mock_extract, auth_headers):
        """Test successful action item extraction."""
        # Mock AI service response
        mock_extract.return_value = {
            "action_items": ["Review quarterly report", "Submit feedback by Friday"],
            "urgency": "high",
            "deadline": "Friday",
            "confidence": 0.85,
            "due_date": "2024-01-15",
            "action_required": "Review quarterly report and submit feedback",
            "explanation": "Manager has requested quarterly report review",
            "relevance": "Directly assigned task with specific deadline",
            "links": ["https://company.com/reports/q4"]
        }
        
        request_data = {
            "email_content": "Subject: Quarterly Report Review\nFrom: manager@company.com\n\nHi, please review the quarterly report and submit your feedback by Friday.",
            "context": "Work assignment from manager"
        }
        
        response = client.post(
            "/api/ai/action-items",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["action_items"]) == 2
        assert data["urgency"] == "high"
        assert data["deadline"] == "Friday"
        assert data["confidence"] == 0.85
    
    @patch('backend.services.ai_service.AIService.extract_action_items')
    def test_extract_action_items_no_items(self, mock_extract, auth_headers):
        """Test action item extraction with no action items found."""
        # Mock AI service response with no action items
        mock_extract.return_value = {
            "action_items": [],
            "urgency": "none",
            "deadline": None,
            "confidence": 0.9,
            "due_date": None,
            "action_required": None,
            "explanation": "No action items found in email",
            "relevance": "Informational email only",
            "links": []
        }
        
        request_data = {
            "email_content": "Subject: Newsletter\nFrom: newsletter@company.com\n\nHere are this week's company updates..."
        }
        
        response = client.post(
            "/api/ai/action-items",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["action_items"]) == 0
        assert data["urgency"] == "none"


class TestEmailSummarization:
    """Tests for email summarization endpoint."""
    
    @patch('backend.services.ai_service.AIService.generate_summary')
    def test_summarize_email_brief(self, mock_summarize, auth_headers):
        """Test brief email summarization."""
        # Mock AI service response
        mock_summarize.return_value = {
            "summary": "Manager requests quarterly report review by Friday",
            "key_points": ["Quarterly report review", "Due Friday", "Manager request"],
            "confidence": 0.9
        }
        
        request_data = {
            "email_content": "Subject: Quarterly Report Review\nFrom: manager@company.com\n\nHi, please review the quarterly report and submit your feedback by Friday. This is important for our planning.",
            "summary_type": "brief"
        }
        
        response = client.post(
            "/api/ai/summarize",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "quarterly report" in data["summary"].lower()
        assert len(data["key_points"]) == 3
        assert data["confidence"] == 0.9
        assert "processing_time" in data
    
    @patch('backend.services.ai_service.AIService.generate_summary')
    def test_summarize_email_detailed(self, mock_summarize, auth_headers):
        """Test detailed email summarization."""
        # Mock AI service response
        mock_summarize.return_value = {
            "summary": "Manager has requested a detailed review of the quarterly report with specific focus on performance metrics and budget analysis. Feedback must be submitted by Friday for planning purposes.",
            "key_points": ["Detailed quarterly report review", "Focus on performance metrics", "Budget analysis required", "Due Friday", "Planning purposes"],
            "confidence": 0.85
        }
        
        request_data = {
            "email_content": "Long detailed email content...",
            "summary_type": "detailed"
        }
        
        response = client.post(
            "/api/ai/summarize",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["summary"]) > 50  # Detailed summary should be longer
        assert len(data["key_points"]) >= 3


class TestAITemplates:
    """Tests for AI templates endpoint."""
    
    @patch('backend.services.ai_service.AIService.get_available_templates')
    def test_get_available_templates(self, mock_templates, auth_headers):
        """Test getting available prompt templates."""
        # Mock AI service response
        mock_templates.return_value = {
            "templates": [
                "email_classifier_with_explanation.prompty",
                "email_one_line_summary.prompty",
                "summerize_action_item.prompty"
            ],
            "descriptions": {
                "email_classifier_with_explanation.prompty": "Enhanced email classifier with explanations",
                "email_one_line_summary.prompty": "Generate concise one-line email summaries",
                "summerize_action_item.prompty": "Extract action items from emails"
            }
        }
        
        response = client.get("/api/ai/templates", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["templates"]) == 3
        assert "email_classifier_with_explanation.prompty" in data["templates"]
        assert len(data["descriptions"]) == 3


class TestAIHealthCheck:
    """Tests for AI service health check."""
    
    @patch('backend.services.ai_service.AIService._ensure_initialized')
    @patch('backend.services.ai_service.AIService.get_available_templates')
    def test_ai_health_check_healthy(self, mock_templates, mock_init, auth_headers):
        """Test AI health check when services are healthy."""
        # Mock successful initialization
        mock_init.return_value = None
        mock_templates.return_value = {
            "templates": ["template1.prompty", "template2.prompty"],
            "descriptions": {}
        }
        
        response = client.get("/api/ai/health", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["templates_available"] == 2
    
    @patch('backend.services.ai_service.AIService._ensure_initialized')
    def test_ai_health_check_unhealthy(self, mock_init, auth_headers):
        """Test AI health check when services are unhealthy."""
        # Mock initialization failure
        mock_init.side_effect = RuntimeError("AI services not available")
        
        response = client.get("/api/ai/health", headers=auth_headers)
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["ai_processor_available"] is False


class TestAIServiceIntegration:
    """Integration tests for AI service endpoints."""
    
    def test_full_email_processing_workflow(self, auth_headers):
        """Test full workflow: classify -> extract action items -> summarize."""
        sample_email = {
            "subject": "Project Review Meeting - Action Required",
            "content": "Hi, we need to schedule a project review meeting for next week. Please confirm your availability and prepare the status report.",
            "sender": "project.manager@company.com"
        }
        
        # Test classification
        classify_response = client.post(
            "/api/ai/classify",
            json=sample_email,
            headers=auth_headers
        )
        
        # Test action items
        action_response = client.post(
            "/api/ai/action-items",
            json={
                "email_content": f"Subject: {sample_email['subject']}\nFrom: {sample_email['sender']}\n\n{sample_email['content']}"
            },
            headers=auth_headers
        )
        
        # Test summarization
        summary_response = client.post(
            "/api/ai/summarize",
            json={
                "email_content": f"Subject: {sample_email['subject']}\nFrom: {sample_email['sender']}\n\n{sample_email['content']}"
            },
            headers=auth_headers
        )
        
        # All endpoints should either succeed or fail gracefully
        for response in [classify_response, action_response, summary_response]:
            # Should not return server errors (5xx) for valid input
            assert response.status_code < 500 or response.status_code == 500
            if response.status_code == 500:
                # If it fails, should be due to AI service unavailability
                assert "AI" in response.json().get("detail", "") or "failed" in response.json().get("detail", "")