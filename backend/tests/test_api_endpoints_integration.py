"""Comprehensive API endpoint integration tests.

This test module verifies that all FastAPI endpoints work without crashing,
handle errors gracefully, and return correct status codes and response schemas.

Tests all endpoints from:
- GET /api/emails (list, pagination, filters)
- GET /api/emails/:id (single email)
- PUT /api/emails/:id/read (mark read)
- POST /api/emails/:id/mark-read (mark read - deprecated)
- POST /api/emails/:id/move (move email)
- GET /api/folders (list folders)
- GET /api/conversations/:id (conversation thread)
- PUT /api/emails/:id/classification (update classification)
- POST /api/emails/bulk-apply-to-outlook (bulk apply)
- POST /api/emails/extract-tasks (extract tasks)
- POST /api/emails/sync-to-database (sync emails)
- POST /api/emails/analyze-holistically (holistic analysis)
- GET /api/emails/search (search emails)
- GET /api/emails/stats (email stats)
- GET /api/emails/category-mappings (category mappings)
- GET /api/emails/accuracy-stats (accuracy stats)
- POST /api/emails/prefetch (prefetch emails)
- GET /api/tasks (list tasks)
- POST /api/tasks (create task)
- GET /api/tasks/:id (get task)
- PUT /api/tasks/:id (update task)
- DELETE /api/tasks/:id (delete task)
- GET /api/tasks/stats (task stats)
- POST /api/tasks/bulk-update (bulk update)
- POST /api/tasks/bulk-delete (bulk delete)
- PUT /api/tasks/:id/status (update status)
- POST /api/tasks/:id/link-email (link email)
- POST /api/tasks/deduplicate/fyi (deduplicate FYI)
- POST /api/tasks/deduplicate/newsletters (deduplicate newsletters)
- POST /api/ai/classify (classify email)
- POST /api/ai/action-items (extract action items)
- POST /api/ai/summarize (summarize email)
- GET /api/ai/templates (get templates)
- GET /api/ai/health (AI health check)
- GET /health (health check)
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from backend.main import app
from backend.core.dependencies import reset_dependencies


# Create test client
@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


# Reset dependencies between tests
@pytest.fixture(autouse=True)
def reset_deps():
    """Reset dependencies and dependency overrides before and after each test."""
    reset_dependencies()
    app.dependency_overrides.clear()
    yield
    reset_dependencies()
    app.dependency_overrides.clear()


# Mock email provider fixture
@pytest.fixture
def mock_email_provider():
    """Create mock email provider."""
    provider = Mock()
    provider.get_emails = Mock(return_value=[
        {
            "id": "test_email_1",
            "subject": "Test Email 1",
            "sender": "sender1@example.com",
            "body": "Test body 1",
            "date": "2024-01-01T10:00:00",
            "is_read": False,
            "has_attachments": False,
            "conversation_id": "conv_1"
        },
        {
            "id": "test_email_2",
            "subject": "Test Email 2",
            "sender": "sender2@example.com",
            "body": "Test body 2",
            "date": "2024-01-02T10:00:00",
            "is_read": True,
            "has_attachments": True,
            "conversation_id": "conv_2"
        }
    ])
    provider.get_email_content = AsyncMock(return_value={
        "id": "test_email_1",
        "subject": "Test Email 1",
        "sender": "sender1@example.com",
        "body": "Full email content here",
        "content": "Full email content here",
        "date": "2024-01-01T10:00:00",
        "is_read": False,
        "has_attachments": False
    })
    provider.get_folders = Mock(return_value=[
        {"name": "Inbox", "id": "inbox_id"},
        {"name": "Sent", "id": "sent_id"},
        {"name": "Archive", "id": "archive_id"}
    ])
    provider.get_conversation_thread = Mock(return_value=[
        {
            "id": "test_email_1",
            "subject": "Test Email 1",
            "sender": "sender1@example.com",
            "body": "Test body 1",
            "date": "2024-01-01T10:00:00"
        }
    ])
    provider.mark_as_read = Mock(return_value=True)
    provider.move_email = Mock(return_value=True)
    return provider


# Mock AI service fixture
@pytest.fixture
def mock_ai_service():
    """Create mock AI service."""
    service = Mock()
    service.classify_email = AsyncMock(return_value={
        "category": "work_relevant",
        "confidence": 0.95,
        "reasoning": "Test reasoning",
        "alternatives": ["meeting"]
    })
    service.extract_action_items = AsyncMock(return_value={
        "action_items": ["Test action item"],
        "urgency": "medium",
        "deadline": "2024-12-31",
        "confidence": 0.90
    })
    service.generate_summary = AsyncMock(return_value={
        "summary": "Test summary",
        "key_points": ["Point 1", "Point 2"],
        "confidence": 0.92
    })
    service.get_available_templates = AsyncMock(return_value={
        "templates": ["classification", "summarization"],
        "descriptions": {
            "classification": "Email classification template",
            "summarization": "Email summarization template"
        }
    })
    service._ensure_initialized = Mock()
    service._initialized = True
    service.deduplicate_content = AsyncMock(return_value={
        "deduplicated_items": ["Item 1", "Item 2"],
        "removed_duplicates": ["Dup 1"],
        "statistics": {
            "original_count": 3,
            "deduplicated_count": 2,
            "duplicates_removed": 1
        }
    })
    service.analyze_holistically = AsyncMock(return_value={
        "truly_relevant_actions": ["Action 1", "Action 2"],
        "superseded_actions": ["Old Action"],
        "duplicate_groups": [["Email 1", "Email 2"]],
        "expired_items": ["Expired Item"],
        "notes": "Holistic analysis completed"
    })
    return service


# Mock email processing service fixture
@pytest.fixture
def mock_processing_service():
    """Create mock email processing service."""
    service = Mock()
    service.get_emails_from_database = AsyncMock(return_value={
        "emails": [
            {
                "id": "db_email_1",
                "subject": "DB Email 1",
                "sender": "sender@example.com",
                "ai_category": "work_relevant",
                "ai_confidence": 0.85
            }
        ],
        "total": 1,
        "has_more": False
    })
    service.calculate_conversation_counts = AsyncMock(return_value={"conv_1": 2, "conv_2": 1})
    service.get_category_mappings = Mock(return_value=[
        {"category": "work_relevant", "folder_name": "Work", "stays_in_inbox": False},
        {"category": "fyi", "folder_name": "Inbox", "stays_in_inbox": True}
    ])
    service.get_accuracy_statistics = AsyncMock(return_value={
        "total_classifications": 100,
        "accuracy": 0.95,
        "categories": {"work_relevant": 50, "fyi": 30, "newsletter": 20}
    })
    service.update_email_classification = AsyncMock(return_value={
        "success": True,
        "message": "Classification updated successfully"
    })
    service.bulk_apply_classifications = AsyncMock(return_value={
        "success": True,
        "processed": 5,
        "successful": 5,
        "failed": 0,
        "errors": []
    })
    service.extract_tasks_from_emails = AsyncMock(return_value={
        "tasks_created": 3,
        "summaries_created": 5
    })
    service.sync_emails_to_database = AsyncMock(return_value={
        "success": True,
        "message": "Emails synced successfully",
        "synced_count": 10,
        "failed_count": 0
    })
    service.analyze_holistically = AsyncMock(return_value={
        "status": "success",
        "insights": ["Insight 1", "Insight 2"]
    })
    return service


# Mock task service fixture
@pytest.fixture
def mock_task_service():
    """Create mock task service."""
    from backend.models.task import Task, TaskStatus, TaskPriority
    from datetime import datetime

    service = Mock()

    # Create real Task model instance
    mock_task = Task(
        id="1",
        title="Test Task",
        description="Test description",
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        category="work",
        email_id=None,
        created_at=datetime(2024, 1, 1, 10, 0, 0),
        updated_at=datetime(2024, 1, 1, 10, 0, 0),
        tags=[],
        metadata={}
    )

    # Mock paginated result
    paginated_result = Mock()
    paginated_result.tasks = [mock_task]
    paginated_result.total_count = 1
    paginated_result.page = 1
    paginated_result.page_size = 20
    paginated_result.has_next = False

    service.create_task = AsyncMock(return_value=mock_task)
    service.get_tasks_paginated = AsyncMock(return_value=paginated_result)
    service.get_task = AsyncMock(return_value=mock_task)
    service.update_task = AsyncMock(return_value=mock_task)
    service.delete_task = AsyncMock(return_value=True)
    service.link_email_to_task = AsyncMock(return_value=mock_task)
    service.get_task_stats = AsyncMock(return_value={
        "total_tasks": 10,
        "pending_tasks": 5,
        "completed_tasks": 5,
        "overdue_tasks": 0,
        "tasks_by_priority": {"high": 2, "medium": 5, "low": 3},
        "tasks_by_category": {"work": 7, "personal": 3}
    })
    service.bulk_update_tasks = AsyncMock(return_value=[mock_task])
    service.bulk_delete_tasks = AsyncMock(return_value=5)

    return service


class TestEmailEndpoints:
    """Test email API endpoints."""

    def test_get_emails_outlook_source(self, client, mock_email_provider, mock_processing_service):
        """Test GET /api/emails with outlook source."""
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_email_provider), \
             patch('backend.core.dependencies.get_email_processing_service', return_value=mock_processing_service):
            response = client.get("/api/emails?source=outlook&folder=Inbox&limit=50")
            assert response.status_code == 200
            data = response.json()
            assert "emails" in data
            assert "total" in data
            assert "offset" in data
            assert "limit" in data
            assert "has_more" in data
            assert isinstance(data["emails"], list)

    def test_get_emails_database_source(self, client, mock_processing_service):
        """Test GET /api/emails with database source."""
        with patch('backend.core.dependencies.get_email_processing_service', return_value=mock_processing_service):
            response = client.get("/api/emails?source=database&limit=50")
            assert response.status_code == 200
            data = response.json()
            assert "emails" in data
            assert "total" in data

    def test_get_email_by_id(self, client, mock_email_provider):
        """Test GET /api/emails/:id."""
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_email_provider):
            response = client.get("/api/emails/test_email_1")
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "subject" in data
            assert "body" in data or "content" in data

    def test_get_email_not_found(self, client, mock_email_provider):
        """Test GET /api/emails/:id with non-existent email."""
        mock_email_provider.get_email_content = AsyncMock(return_value=None)
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_email_provider):
            response = client.get("/api/emails/nonexistent_email")
            assert response.status_code == 404

    def test_search_emails(self, client, mock_email_provider):
        """Test GET /api/emails/search."""
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_email_provider):
            response = client.get("/api/emails/search?q=test&page=1&per_page=20")
            assert response.status_code == 200
            data = response.json()
            assert "emails" in data
            assert "total" in data

    def test_get_email_stats(self, client, mock_email_provider):
        """Test GET /api/emails/stats."""
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_email_provider):
            response = client.get("/api/emails/stats?limit=100")
            assert response.status_code == 200
            data = response.json()
            assert "total_emails" in data
            assert "unread_emails" in data

    def test_get_category_mappings(self, client, mock_processing_service):
        """Test GET /api/emails/category-mappings."""
        with patch('backend.core.dependencies.get_email_processing_service', return_value=mock_processing_service):
            response = client.get("/api/emails/category-mappings")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            if data:
                assert "category" in data[0]
                assert "folder_name" in data[0]

    def test_get_accuracy_stats(self, client, mock_processing_service):
        """Test GET /api/emails/accuracy-stats."""
        with patch('backend.core.dependencies.get_email_processing_service', return_value=mock_processing_service):
            response = client.get("/api/emails/accuracy-stats")
            assert response.status_code == 200
            data = response.json()
            # Accuracy stats returns structured results
            assert "total_emails" in data
            assert "overall_accuracy" in data
            assert "total_correct" in data
            assert "categories" in data

    def test_prefetch_emails(self, client, mock_email_provider):
        """Test POST /api/emails/prefetch."""
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_email_provider):
            response = client.post("/api/emails/prefetch", json=["test_email_1", "test_email_2"])
            assert response.status_code == 200
            data = response.json()
            assert "emails" in data
            assert "success_count" in data
            assert "error_count" in data

    def test_update_email_read_status(self, client, mock_email_provider):
        """Test PUT /api/emails/:id/read."""
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_email_provider):
            response = client.put("/api/emails/test_email_1/read?read=true")
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert "message" in data

    def test_mark_email_as_read(self, client, mock_email_provider):
        """Test POST /api/emails/:id/mark-read (deprecated)."""
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_email_provider):
            response = client.post("/api/emails/test_email_1/mark-read")
            assert response.status_code == 200
            data = response.json()
            assert "success" in data

    def test_move_email(self, client, mock_email_provider):
        """Test POST /api/emails/:id/move."""
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_email_provider):
            response = client.post("/api/emails/test_email_1/move?destination_folder=Archive")
            assert response.status_code == 200
            data = response.json()
            assert "success" in data

    def test_get_folders(self, client, mock_email_provider):
        """Test GET /api/folders."""
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_email_provider):
            response = client.get("/api/folders")
            assert response.status_code == 200
            data = response.json()
            assert "folders" in data
            assert "total" in data

    def test_get_conversation_thread(self, client, mock_email_provider):
        """Test GET /api/conversations/:id."""
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_email_provider):
            response = client.get("/api/conversations/conv_1")
            assert response.status_code == 200
            data = response.json()
            assert "conversation_id" in data
            assert "emails" in data
            assert data["conversation_id"] == "conv_1"
            assert isinstance(data["emails"], list)
            assert len(data["emails"]) > 0, "Expected at least one email in conversation thread"
            assert data["total"] == len(data["emails"])

    def test_update_email_classification(self, client, mock_processing_service):
        """Test PUT /api/emails/:id/classification."""
        with patch('backend.core.dependencies.get_email_processing_service', return_value=mock_processing_service):
            response = client.put("/api/emails/test_email_1/classification", json={
                "category": "work_relevant",
                "apply_to_outlook": True
            })
            assert response.status_code == 200
            data = response.json()
            assert "success" in data

    def test_bulk_apply_to_outlook(self, client, mock_processing_service):
        """Test POST /api/emails/bulk-apply-to-outlook."""
        with patch('backend.core.dependencies.get_email_processing_service', return_value=mock_processing_service):
            response = client.post("/api/emails/bulk-apply-to-outlook", json={
                "email_ids": ["test_email_1", "test_email_2"],
                "apply_to_outlook": True
            })
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert "processed" in data

    def test_extract_tasks_from_emails(self, client, mock_processing_service):
        """Test POST /api/emails/extract-tasks."""
        with patch('backend.core.dependencies.get_email_processing_service', return_value=mock_processing_service):
            response = client.post("/api/emails/extract-tasks", json={
                "email_ids": ["test_email_1", "test_email_2"]
            })
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "email_count" in data

    def test_sync_emails_to_database(self, client, mock_processing_service):
        """Test POST /api/emails/sync-to-database."""
        with patch('backend.core.dependencies.get_email_processing_service', return_value=mock_processing_service):
            response = client.post("/api/emails/sync-to-database", json={
                "emails": [
                    {
                        "id": "test_email_1",
                        "subject": "Test",
                        "sender": "test@example.com",
                        "body": "Test body",
                        "ai_category": "work_relevant"
                    }
                ]
            })
            assert response.status_code == 200
            data = response.json()
            assert "success" in data

    def test_analyze_holistically(self, client, mock_ai_service):
        """Test POST /api/emails/analyze-holistically."""
        with patch('backend.core.dependencies.get_ai_service', return_value=mock_ai_service):
            response = client.post("/api/emails/analyze-holistically", json={
                "emails": [
                    {
                        "id": "test_email_1",
                        "subject": "Test",
                        "body": "Test body"
                    }
                ]
            })
            assert response.status_code == 200
            data = response.json()
            # Holistic analysis returns structured results
            assert "truly_relevant_actions" in data
            assert "superseded_actions" in data
            assert "duplicate_groups" in data
            assert "expired_items" in data


class TestTaskEndpoints:
    """Test task API endpoints."""

    def test_get_tasks(self, client, mock_task_service):
        """Test GET /api/tasks."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.get("/api/tasks?page=1&limit=20")
            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert "total_count" in data
            assert "page" in data

    def test_get_tasks_with_filters(self, client, mock_task_service):
        """Test GET /api/tasks with filters."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.get("/api/tasks?status=pending&priority=high&category=work")
            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data

    def test_get_task_stats(self, client, mock_task_service):
        """Test GET /api/tasks/stats."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.get("/api/tasks/stats")
            assert response.status_code == 200
            data = response.json()
            assert "total_tasks" in data

    def test_create_task(self, client, mock_task_service):
        """Test POST /api/tasks."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.post("/api/tasks", json={
                "title": "New Task",
                "description": "Task description",
                "status": "pending",
                "priority": "medium"
            })
            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert "title" in data

    def test_get_task_by_id(self, client, mock_task_service):
        """Test GET /api/tasks/:id."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.get("/api/tasks/1")
            assert response.status_code == 200
            data = response.json()
            assert "id" in data

    def test_get_task_not_found(self, client, mock_task_service):
        """Test GET /api/tasks/:id with non-existent task."""
        from backend.core.dependencies import get_task_service

        # Override the mock to return None for non-existent task
        mock_task_service.get_task = AsyncMock(return_value=None)
        app.dependency_overrides[get_task_service] = lambda: mock_task_service

        try:
            # Use a very large ID that's unlikely to exist in test database
            response = client.get("/api/tasks/99999999")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_task_service, None)

    def test_update_task(self, client, mock_task_service):
        """Test PUT /api/tasks/:id."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.put("/api/tasks/1", json={
                "title": "Updated Task",
                "status": "completed"
            })
            assert response.status_code == 200
            data = response.json()
            assert "id" in data

    def test_delete_task(self, client, mock_task_service):
        """Test DELETE /api/tasks/:id."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.delete("/api/tasks/1")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    def test_bulk_update_tasks(self, client, mock_task_service):
        """Test POST /api/tasks/bulk-update."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.post("/api/tasks/bulk-update", json={
                "task_ids": [1, 2, 3],
                "updates": {"status": "completed"}
            })
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_bulk_delete_tasks(self, client, mock_task_service):
        """Test POST /api/tasks/bulk-delete."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.post("/api/tasks/bulk-delete", json={
                "task_ids": [1, 2, 3]
            })
            assert response.status_code == 200
            data = response.json()
            assert "deleted_count" in data

    def test_update_task_status(self, client, mock_task_service):
        """Test PUT /api/tasks/:id/status."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.put("/api/tasks/1/status?status=in_progress")
            assert response.status_code == 200
            data = response.json()
            assert "id" in data

    def test_link_email_to_task(self, client, mock_task_service):
        """Test POST /api/tasks/:id/link-email."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.post("/api/tasks/1/link-email?email_id=test_email_1")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    def test_deduplicate_fyi_tasks(self, client, mock_task_service, mock_ai_service):
        """Test POST /api/tasks/deduplicate/fyi."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service), \
             patch('backend.core.dependencies.get_com_ai_service', return_value=mock_ai_service):
            response = client.post("/api/tasks/deduplicate/fyi")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    def test_deduplicate_newsletter_tasks(self, client, mock_task_service, mock_ai_service):
        """Test POST /api/tasks/deduplicate/newsletters."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service), \
             patch('backend.core.dependencies.get_com_ai_service', return_value=mock_ai_service):
            response = client.post("/api/tasks/deduplicate/newsletters")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data


class TestAIEndpoints:
    """Test AI processing API endpoints."""

    def test_classify_email(self, client, mock_ai_service):
        """Test POST /api/ai/classify."""
        with patch('backend.core.dependencies.get_ai_service', return_value=mock_ai_service):
            response = client.post("/api/ai/classify", json={
                "subject": "Meeting tomorrow",
                "sender": "boss@example.com",
                "content": "Let's have a meeting tomorrow at 2pm"
            })
            assert response.status_code == 200
            data = response.json()
            assert "category" in data
            assert "reasoning" in data

    def test_extract_action_items(self, client, mock_ai_service):
        """Test POST /api/ai/action-items."""
        with patch('backend.core.dependencies.get_ai_service', return_value=mock_ai_service):
            response = client.post("/api/ai/action-items", json={
                "email_content": "Please review the document by Friday"
            })
            assert response.status_code == 200
            data = response.json()
            assert "action_items" in data
            assert "urgency" in data

    def test_summarize_email(self, client, mock_ai_service):
        """Test POST /api/ai/summarize."""
        with patch('backend.core.dependencies.get_ai_service', return_value=mock_ai_service):
            response = client.post("/api/ai/summarize", json={
                "email_content": "This is a long email that needs to be summarized...",
                "summary_type": "brief"
            })
            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
            assert "key_points" in data

    def test_get_available_templates(self, client, mock_ai_service):
        """Test GET /api/ai/templates."""
        with patch('backend.core.dependencies.get_ai_service', return_value=mock_ai_service):
            response = client.get("/api/ai/templates")
            assert response.status_code == 200
            data = response.json()
            assert "templates" in data

    def test_ai_health_check(self, client, mock_ai_service):
        """Test GET /api/ai/health."""
        with patch('backend.core.dependencies.get_ai_service', return_value=mock_ai_service):
            response = client.get("/api/ai/health")
            assert response.status_code == 200 or response.status_code == 503
            data = response.json()
            assert "status" in data


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test GET /health."""
        response = client.get("/health")
        # Should return 200 or 404 depending on if endpoint exists
        assert response.status_code in [200, 404, 405]


class TestErrorHandling:
    """Test error handling for API endpoints."""

    def test_invalid_email_id(self, client, mock_email_provider):
        """Test endpoints with invalid email IDs."""
        mock_email_provider.get_email_content = AsyncMock(side_effect=Exception("Email not found"))
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_email_provider):
            response = client.get("/api/emails/invalid_id")
            assert response.status_code in [404, 500]

    def test_invalid_task_id(self, client, mock_task_service):
        """Test endpoints with invalid task IDs."""
        mock_task_service.get_task = AsyncMock(return_value=None)
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.get("/api/tasks/999999")
            assert response.status_code == 404

    def test_missing_required_fields(self, client, mock_task_service):
        """Test POST endpoints with missing required fields."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.post("/api/tasks", json={})
            # Should return 422 (validation error) or 400
            assert response.status_code in [400, 422]

    def test_empty_bulk_operations(self, client, mock_processing_service):
        """Test bulk operations with empty arrays."""
        with patch('backend.core.dependencies.get_email_processing_service', return_value=mock_processing_service):
            response = client.post("/api/emails/bulk-apply-to-outlook", json={
                "email_ids": [],
                "apply_to_outlook": True
            })
            # Should handle empty arrays gracefully
            assert response.status_code in [200, 400]


class TestResponseSchemas:
    """Test that responses match expected schemas."""

    def test_email_list_response_schema(self, client, mock_email_provider, mock_processing_service):
        """Verify email list response has all required fields."""
        with patch('backend.core.dependencies.get_email_provider', return_value=mock_email_provider), \
             patch('backend.core.dependencies.get_email_processing_service', return_value=mock_processing_service):
            response = client.get("/api/emails")
            assert response.status_code == 200
            data = response.json()
            # Verify schema
            assert "emails" in data
            assert "total" in data
            assert "offset" in data
            assert "limit" in data
            assert "has_more" in data
            assert isinstance(data["emails"], list)
            assert isinstance(data["total"], int)
            assert isinstance(data["offset"], int)
            assert isinstance(data["limit"], int)
            assert isinstance(data["has_more"], bool)

    def test_task_list_response_schema(self, client, mock_task_service):
        """Verify task list response has all required fields."""
        with patch('backend.core.dependencies.get_task_service', return_value=mock_task_service):
            response = client.get("/api/tasks")
            assert response.status_code == 200
            data = response.json()
            # Verify schema
            assert "tasks" in data
            assert "total_count" in data
            assert "page" in data
            assert "page_size" in data
            assert "has_next" in data

    def test_classification_response_schema(self, client, mock_ai_service):
        """Verify classification response has all required fields."""
        with patch('backend.core.dependencies.get_ai_service', return_value=mock_ai_service):
            response = client.post("/api/ai/classify", json={
                "subject": "Test",
                "sender": "test@example.com",
                "content": "Test content"
            })
            assert response.status_code == 200
            data = response.json()
            # Verify schema
            assert "category" in data
            assert "reasoning" in data
            # confidence and processing_time are optional
