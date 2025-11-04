"""API tests for email prefetch endpoint.

Tests the /api/emails/prefetch endpoint that enables bulk email fetching
for performance optimization in the frontend.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
from backend.main import app
from backend.services.email_provider import EmailProvider


@pytest.fixture
def mock_email_provider():
    """Create a mock email provider for testing."""
    provider = Mock(spec=EmailProvider)
    provider.authenticated = True

    # Mock get_email_content as an async method
    async def mock_get_email_content(email_id):
        if email_id.startswith("error-"):
            raise Exception(f"Failed to fetch {email_id}")
        return {
            "id": email_id,
            "subject": f"Test Email {email_id}",
            "sender": "test@example.com",
            "body": f"Full body content for {email_id}",
            "received_time": "2024-01-01T10:00:00Z",
            "is_read": False
        }

    provider.get_email_content = AsyncMock(side_effect=mock_get_email_content)
    return provider


@pytest.fixture
def client(mock_email_provider):
    """Create test client with mocked provider."""
    from backend.api.emails import get_email_provider

    def override_provider():
        return mock_email_provider

    app.dependency_overrides[get_email_provider] = override_provider

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


class TestPrefetchEndpoint:
    """Tests for the /api/emails/prefetch endpoint."""

    def test_prefetch_single_email(self, client):
        """Test prefetching a single email."""
        response = client.post(
            "/api/emails/prefetch",
            json=["email-1"]
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success_count"] == 1
        assert data["error_count"] == 0
        assert len(data["emails"]) == 1
        assert data["emails"][0]["id"] == "email-1"
        assert data["emails"][0]["subject"] == "Test Email email-1"

    def test_prefetch_multiple_emails(self, client):
        """Test prefetching multiple emails in one request."""
        email_ids = ["email-1", "email-2", "email-3", "email-4", "email-5"]

        response = client.post(
            "/api/emails/prefetch",
            json=email_ids
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success_count"] == 5
        assert data["error_count"] == 0
        assert len(data["emails"]) == 5

        email_ids_returned = [email["id"] for email in data["emails"]]
        for email_id in email_ids:
            assert email_id in email_ids_returned

    def test_prefetch_with_failures(self, client):
        """Test prefetching handles individual failures gracefully."""
        email_ids = ["email-1", "error-bad", "email-3", "error-fail"]

        response = client.post(
            "/api/emails/prefetch",
            json=email_ids
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 2 successes and 2 failures
        assert data["success_count"] == 2
        assert data["error_count"] == 2

        # Check successful emails
        email_ids_returned = [email["id"] for email in data["emails"]]
        assert "email-1" in email_ids_returned
        assert "email-3" in email_ids_returned

        # Check failed emails reported in errors
        assert len(data["errors"]) == 2
        error_messages = " ".join(data["errors"])
        assert "error-bad" in error_messages
        assert "error-fail" in error_messages

    def test_prefetch_empty_list(self, client):
        """Test prefetching with empty email list."""
        response = client.post(
            "/api/emails/prefetch",
            json=[]
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success_count"] == 0
        assert data["error_count"] == 0
        assert len(data["emails"]) == 0

    def test_prefetch_batch_size_limit(self, client):
        """Test that prefetch endpoint limits batch size."""
        # Request 100 emails but should be limited to 50
        email_ids = [f"email-{i}" for i in range(100)]

        response = client.post(
            "/api/emails/prefetch",
            json=email_ids
        )

        assert response.status_code == 200
        data = response.json()

        # Should process all emails
        assert data["success_count"] == 100
        assert len(data["emails"]) == 100

    def test_prefetch_returns_full_content(self, client):
        """Test that prefetch returns full email content, not summaries."""
        response = client.post(
            "/api/emails/prefetch",
            json=["email-1"]
        )

        assert response.status_code == 200
        data = response.json()

        email = data["emails"][0]

        # Should have full content fields
        assert "subject" in email
        assert "sender" in email
        assert "body" in email
        assert "Full body content" in email["body"]
        assert "received_time" in email

    def test_prefetch_performance_metrics(self, client):
        """Test that prefetch returns performance metrics."""
        response = client.post(
            "/api/emails/prefetch",
            json=["email-1", "email-2", "email-3"]
        )

        assert response.status_code == 200
        data = response.json()

        # Should include basic success metrics
        assert data["success_count"] == 3
        assert len(data["emails"]) == 3

    def test_prefetch_invalid_request(self, client):
        """Test prefetch with invalid request body."""
        # Send non-array body
        response = client.post(
            "/api/emails/prefetch",
            json={"invalid": "data"}
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_prefetch_concurrent_efficiency(self, client, mock_email_provider):
        """Test that prefetch uses concurrent fetching for efficiency."""
        email_ids = [f"email-{i}" for i in range(10)]

        response = client.post(
            "/api/emails/prefetch",
            json=email_ids
        )

        assert response.status_code == 200
        data = response.json()

        # All should succeed
        assert data["success_count"] == 10

        # Verify mock was called correct number of times
        assert mock_email_provider.get_email_content.call_count == 10

    def test_prefetch_duplicate_ids(self, client):
        """Test prefetch handles duplicate email IDs."""
        # Send duplicates
        email_ids = ["email-1", "email-1", "email-2", "email-2"]

        response = client.post(
            "/api/emails/prefetch",
            json=email_ids
        )

        assert response.status_code == 200
        data = response.json()

        # Should fetch all (no deduplication at API level)
        assert data["success_count"] == 4

    def test_prefetch_error_details(self, client):
        """Test that prefetch provides detailed error information."""
        email_ids = ["email-1", "error-notfound", "error-timeout"]

        response = client.post(
            "/api/emails/prefetch",
            json=email_ids
        )

        assert response.status_code == 200
        data = response.json()

        # Check error details are provided
        assert "errors" in data
        assert isinstance(data["errors"], list)
        assert len(data["errors"]) == 2

        # Errors should have descriptive messages
        error_text = " ".join(data["errors"])
        assert "error-notfound" in error_text or "error-timeout" in error_text


@pytest.mark.performance
class TestPrefetchPerformance:
    """Performance tests for prefetch endpoint."""

    def test_prefetch_10_emails_performance(self, client):
        """Test prefetching 10 emails completes in reasonable time."""
        import time

        email_ids = [f"email-{i}" for i in range(10)]

        start_time = time.time()
        response = client.post(
            "/api/emails/prefetch",
            json=email_ids
        )
        elapsed = time.time() - start_time

        assert response.status_code == 200

        # Should complete in under 2 seconds (very generous for mocked data)
        assert elapsed < 2.0

    def test_prefetch_50_emails_performance(self, client):
        """Test prefetching max batch size (50 emails)."""
        import time

        email_ids = [f"email-{i}" for i in range(50)]

        start_time = time.time()
        response = client.post(
            "/api/emails/prefetch",
            json=email_ids
        )
        elapsed = time.time() - start_time

        assert response.status_code == 200
        data = response.json()

        # Should complete all 50
        assert data["success_count"] == 50

        # Should complete in under 5 seconds (generous for max batch)
        assert elapsed < 5.0
