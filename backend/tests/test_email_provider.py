"""Tests for email provider interface and implementations."""

import pytest
from fastapi import HTTPException
from backend.services.email_provider import EmailProvider, MockEmailProvider, get_email_provider_instance


class TestEmailProviderInterface:
    """Test EmailProvider interface compliance."""

    def test_mock_provider_implements_interface(self):
        """Test that MockEmailProvider implements EmailProvider interface."""
        provider = MockEmailProvider()
        assert isinstance(provider, EmailProvider)

    def test_mock_provider_has_required_methods(self):
        """Test that MockEmailProvider has all required methods."""
        provider = MockEmailProvider()

        # Check all abstract methods are implemented
        required_methods = [
            'get_emails', 'get_email_content', 'get_folders', 'mark_as_read',
            'authenticate', 'get_conversation_thread', 'move_email', 'get_email_body'
        ]

        for method_name in required_methods:
            assert hasattr(provider, method_name)
            assert callable(getattr(provider, method_name))


class TestMockEmailProvider:
    """Test MockEmailProvider implementation."""

    @pytest.fixture
    def provider(self):
        """Create mock email provider instance."""
        return MockEmailProvider()

    def test_authentication_required(self, provider):
        """Test that methods require authentication."""
        # Should raise HTTPException when not authenticated
        with pytest.raises(HTTPException, match="Not authenticated"):
            provider.get_emails()

        with pytest.raises(HTTPException, match="Not authenticated"):
            provider.get_email_content("test-id")

        with pytest.raises(HTTPException, match="Not authenticated"):
            provider.get_folders()

        with pytest.raises(HTTPException, match="Not authenticated"):
            provider.mark_as_read("test-id")

    def test_authentication_success(self, provider):
        """Test successful authentication."""
        result = provider.authenticate({"test": "credentials"})
        assert result is True
        assert provider.authenticated is True

    def test_get_emails(self, provider):
        """Test getting emails."""
        # Authenticate first
        provider.authenticate({"test": "credentials"})

        # Get emails
        emails = provider.get_emails()
        assert isinstance(emails, list)
        assert len(emails) == 2

        # Check email structure
        email = emails[0]
        assert "id" in email
        assert "subject" in email
        assert "sender" in email
        assert "body" in email
        assert "received_time" in email
        assert "conversation_id" in email

    def test_get_emails_with_pagination(self, provider):
        """Test getting emails with pagination."""
        provider.authenticate({"test": "credentials"})

        # Get first email
        emails = provider.get_emails(count=1, offset=0)
        assert len(emails) == 1
        assert emails[0]["id"] == "mock-email-1"

        # Get second email
        emails = provider.get_emails(count=1, offset=1)
        assert len(emails) == 1
        assert emails[0]["id"] == "mock-email-2"

    def test_get_email_content(self, provider):
        """Test getting email content by ID."""
        provider.authenticate({"test": "credentials"})

        # Get existing email
        email = provider.get_email_content("mock-email-1")
        assert email is not None
        assert email["id"] == "mock-email-1"
        assert email["subject"] == "Test Email 1"

        # Get non-existing email
        email = provider.get_email_content("non-existing")
        assert email is None

    def test_get_folders(self, provider):
        """Test getting folders."""
        provider.authenticate({"test": "credentials"})

        folders = provider.get_folders()
        assert isinstance(folders, list)
        assert len(folders) == 3

        # Check folder structure
        folder = folders[0]
        assert "id" in folder
        assert "name" in folder
        assert "type" in folder

    def test_mark_as_read(self, provider):
        """Test marking email as read."""
        provider.authenticate({"test": "credentials"})

        # Initially email should be unread
        email = provider.get_email_content("mock-email-1")
        assert email["is_read"] is False

        # Mark as read
        result = provider.mark_as_read("mock-email-1")
        assert result is True

        # Check if marked as read
        email = provider.get_email_content("mock-email-1")
        assert email["is_read"] is True

        # Try marking non-existing email
        result = provider.mark_as_read("non-existing")
        assert result is False

    def test_move_email(self, provider):
        """Test moving email to folder."""
        provider.authenticate({"test": "credentials"})

        # Initially email should be in Inbox
        email = provider.get_email_content("mock-email-1")
        assert email["folder"] == "Inbox"

        # Move to Sent
        result = provider.move_email("mock-email-1", "Sent")
        assert result is True

        # Check if moved
        email = provider.get_email_content("mock-email-1")
        assert email["folder"] == "Sent"

        # Try moving non-existing email
        result = provider.move_email("non-existing", "Drafts")
        assert result is False

    def test_get_conversation_thread(self, provider):
        """Test getting conversation thread."""
        provider.authenticate({"test": "credentials"})

        # Get conversation thread
        emails = provider.get_conversation_thread("conv-1")
        assert isinstance(emails, list)
        assert len(emails) == 1
        assert emails[0]["conversation_id"] == "conv-1"

        # Get empty conversation
        emails = provider.get_conversation_thread("non-existing")
        assert isinstance(emails, list)
        assert len(emails) == 0

    def test_get_email_body_compatibility(self, provider):
        """Test get_email_body compatibility method."""
        provider.authenticate({"test": "credentials"})

        # Get email body
        body = provider.get_email_body("mock-email-1")
        assert isinstance(body, str)
        assert "test email body" in body.lower()

        # Non-existing email should return empty string
        body = provider.get_email_body("non-existing")
        assert body == ""


class TestEmailProviderFactory:
    """Test email provider factory functions."""

    @pytest.fixture(autouse=True)
    def reset_provider(self):
        """Reset global provider before each test."""
        import backend.services.email_provider as ep
        ep._email_provider = None
        yield
        ep._email_provider = None

    def test_get_email_provider_raises_without_config(self):
        """Test that factory raises error when no provider is configured."""
        with pytest.raises(RuntimeError, match="No email provider configured"):
            get_email_provider_instance()

    def test_singleton_behavior_with_mock_settings(self, monkeypatch):
        """Test that factory returns same instance."""
        # Mock settings to enable COM provider
        mock_provider = MockEmailProvider()

        # Patch the global provider
        import backend.services.email_provider as ep
        ep._email_provider = mock_provider

        provider1 = get_email_provider_instance()
        provider2 = get_email_provider_instance()
        assert provider1 is provider2
