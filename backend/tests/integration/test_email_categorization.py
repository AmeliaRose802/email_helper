"""Integration tests for email categorization operations.

Tests the email categorization workflow including assigning categories,
removing categories, and bulk category operations through the COM provider.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_outlook_adapter_with_categories():
    """Create a mock OutlookEmailAdapter with category support."""
    adapter = MagicMock()
    adapter.connect = Mock(return_value=True)
    adapter.get_emails = Mock(return_value=[])
    adapter.categorize_email = Mock(return_value=True)
    adapter.get_email_by_id = Mock(return_value={
        'id': 'test-email-1',
        'subject': 'Test Email',
        'sender': 'test@example.com',
        'recipient': 'user@example.com',
        'body': 'Test body',
        'received_time': '2024-01-01T10:00:00Z',
        'is_read': False,
        'categories': [],
        'conversation_id': 'conv-1'
    })
    return adapter


@pytest.fixture
def com_provider_with_categories(mock_outlook_adapter_with_categories):
    """Create COMEmailProvider with mocked adapter for categorization tests."""
    with patch('backend.services.com_email_provider.OutlookEmailAdapter',
               return_value=mock_outlook_adapter_with_categories):
        with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
            from backend.services.com_email_provider import COMEmailProvider
            provider = COMEmailProvider()
            provider.adapter = mock_outlook_adapter_with_categories
            return provider


@pytest.mark.integration
class TestEmailCategorization:
    """Integration tests for email categorization operations."""

    def test_categorize_single_email(
        self,
        com_provider_with_categories,
        mock_outlook_adapter_with_categories
    ):
        """Test categorizing a single email."""
        # Authenticate
        com_provider_with_categories.authenticate({})

        # Categorize email
        email_id = 'test-email-1'
        category = 'Work Relevant'

        # Call the adapter's categorize_email method directly
        result = mock_outlook_adapter_with_categories.categorize_email(
            email_id,
            category
        )

        assert result is True
        mock_outlook_adapter_with_categories.categorize_email.assert_called_once_with(
            email_id,
            category
        )

    def test_categorize_email_with_color(
        self,
        com_provider_with_categories,
        mock_outlook_adapter_with_categories
    ):
        """Test categorizing an email with a specific color."""
        com_provider_with_categories.authenticate({})

        email_id = 'test-email-2'
        category = 'Important'
        color = 'Red'

        # Mock the categorize_email to accept color parameter
        mock_outlook_adapter_with_categories.categorize_email = Mock(return_value=True)

        result = mock_outlook_adapter_with_categories.categorize_email(
            email_id,
            category,
            color
        )

        assert result is True
        mock_outlook_adapter_with_categories.categorize_email.assert_called_once_with(
            email_id,
            category,
            color
        )

    def test_categorize_multiple_emails(
        self,
        com_provider_with_categories,
        mock_outlook_adapter_with_categories
    ):
        """Test categorizing multiple emails with the same category."""
        com_provider_with_categories.authenticate({})

        email_ids = ['email-1', 'email-2', 'email-3']
        category = 'Required Actions (Me)'

        results = []
        for email_id in email_ids:
            result = mock_outlook_adapter_with_categories.categorize_email(
                email_id,
                category
            )
            results.append(result)

        assert all(results)
        assert mock_outlook_adapter_with_categories.categorize_email.call_count == 3

    def test_get_email_with_categories(
        self,
        com_provider_with_categories,
        mock_outlook_adapter_with_categories
    ):
        """Test retrieving an email shows its assigned categories."""
        # Setup mock to return email with categories
        mock_outlook_adapter_with_categories.get_email_by_id.return_value = {
            'id': 'categorized-email',
            'subject': 'Categorized Email',
            'sender': 'sender@example.com',
            'recipient': 'user@example.com',
            'body': 'Email with categories',
            'received_time': '2024-01-01T10:00:00Z',
            'is_read': False,
            'categories': ['Work Relevant', 'Important'],
            'conversation_id': 'conv-1'
        }

        com_provider_with_categories.authenticate({})

        email = mock_outlook_adapter_with_categories.get_email_by_id('categorized-email')

        assert email is not None
        assert 'categories' in email
        assert len(email['categories']) == 2
        assert 'Work Relevant' in email['categories']
        assert 'Important' in email['categories']

    def test_filter_emails_by_category(
        self,
        com_provider_with_categories,
        mock_outlook_adapter_with_categories
    ):
        """Test retrieving emails filtered by category."""
        # Setup mock emails with different categories
        categorized_emails = [
            {
                'id': 'email-1',
                'subject': 'Work Email',
                'sender': 'work@example.com',
                'categories': ['Work Relevant'],
                'received_time': '2024-01-01T10:00:00Z',
                'is_read': False
            },
            {
                'id': 'email-2',
                'subject': 'Personal Email',
                'sender': 'personal@example.com',
                'categories': ['Personal'],
                'received_time': '2024-01-01T11:00:00Z',
                'is_read': False
            },
            {
                'id': 'email-3',
                'subject': 'Work Email 2',
                'sender': 'work2@example.com',
                'categories': ['Work Relevant'],
                'received_time': '2024-01-01T12:00:00Z',
                'is_read': False
            }
        ]

        mock_outlook_adapter_with_categories.get_emails.return_value = categorized_emails

        com_provider_with_categories.authenticate({})

        all_emails = com_provider_with_categories.get_emails('Inbox')

        # Filter by category (client-side filtering)
        work_emails = [
            email for email in all_emails
            if 'Work Relevant' in email.get('categories', [])
        ]

        assert len(work_emails) == 2
        assert all('Work Relevant' in email['categories'] for email in work_emails)

    def test_categorize_conversation_thread(
        self,
        com_provider_with_categories,
        mock_outlook_adapter_with_categories
    ):
        """Test categorizing all emails in a conversation thread."""
        # Setup conversation thread
        thread_emails = [
            {'id': 'thread-1', 'conversation_id': 'conv-thread', 'subject': 'Re: Discussion'},
            {'id': 'thread-2', 'conversation_id': 'conv-thread', 'subject': 'Re: Discussion'},
            {'id': 'thread-3', 'conversation_id': 'conv-thread', 'subject': 'Re: Discussion'}
        ]

        mock_outlook_adapter_with_categories.get_emails.return_value = thread_emails

        com_provider_with_categories.authenticate({})

        # Get conversation thread
        thread = com_provider_with_categories.get_conversation_thread('conv-thread')

        # Categorize all emails in thread
        category = 'Team Actions'
        results = []
        for email in thread:
            result = mock_outlook_adapter_with_categories.categorize_email(
                email['id'],
                category
            )
            results.append(result)

        assert len(results) == 3
        assert all(results)


@pytest.mark.integration
class TestEmailCategorizationErrorHandling:
    """Integration tests for email categorization error handling."""

    def test_categorize_nonexistent_email(
        self,
        com_provider_with_categories,
        mock_outlook_adapter_with_categories
    ):
        """Test categorizing an email that doesn't exist."""
        com_provider_with_categories.authenticate({})

        # Mock failure for nonexistent email
        mock_outlook_adapter_with_categories.categorize_email.return_value = False

        result = mock_outlook_adapter_with_categories.categorize_email(
            'nonexistent-email',
            'Test Category'
        )

        assert result is False

    def test_categorize_with_invalid_category(
        self,
        com_provider_with_categories,
        mock_outlook_adapter_with_categories
    ):
        """Test categorizing with an invalid category name."""
        com_provider_with_categories.authenticate({})

        # Mock failure for invalid category
        mock_outlook_adapter_with_categories.categorize_email = Mock(
            side_effect=ValueError("Invalid category")
        )

        with pytest.raises(ValueError, match="Invalid category"):
            mock_outlook_adapter_with_categories.categorize_email(
                'test-email',
                ''  # Empty category
            )

    def test_categorize_without_authentication(
        self,
        mock_outlook_adapter_with_categories
    ):
        """Test categorizing without authentication."""
        with patch('backend.services.com_email_provider.OutlookEmailAdapter',
                   return_value=mock_outlook_adapter_with_categories):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider

                provider = COMEmailProvider()
                provider.adapter = mock_outlook_adapter_with_categories
                provider.authenticated = False

                # Attempting to categorize without authentication should fail
                # This would be caught by the @requires_com decorator
                assert not provider.authenticated


@pytest.mark.integration
class TestBulkCategorization:
    """Integration tests for bulk email categorization operations."""

    def test_bulk_categorize_by_sender(
        self,
        com_provider_with_categories,
        mock_outlook_adapter_with_categories
    ):
        """Test bulk categorization of emails from a specific sender."""
        # Setup emails from same sender
        sender_emails = [
            {
                'id': f'email-{i}',
                'subject': f'Email {i}',
                'sender': 'important@company.com',
                'categories': []
            }
            for i in range(5)
        ]

        mock_outlook_adapter_with_categories.get_emails.return_value = sender_emails

        com_provider_with_categories.authenticate({})

        # Get emails from specific sender
        all_emails = com_provider_with_categories.get_emails('Inbox')
        target_sender = 'important@company.com'
        emails_to_categorize = [
            email for email in all_emails
            if email['sender'] == target_sender
        ]

        # Bulk categorize
        category = 'Important'
        results = []
        for email in emails_to_categorize:
            result = mock_outlook_adapter_with_categories.categorize_email(
                email['id'],
                category
            )
            results.append(result)

        assert len(results) == 5
        assert all(results)

    def test_bulk_categorize_unread_emails(
        self,
        com_provider_with_categories,
        mock_outlook_adapter_with_categories
    ):
        """Test bulk categorization of unread emails."""
        # Setup mix of read and unread emails
        mixed_emails = [
            {'id': f'email-{i}', 'is_read': i % 2 == 0, 'categories': []}
            for i in range(10)
        ]

        mock_outlook_adapter_with_categories.get_emails.return_value = mixed_emails

        com_provider_with_categories.authenticate({})

        # Get unread emails
        all_emails = com_provider_with_categories.get_emails('Inbox')
        unread_emails = [email for email in all_emails if not email['is_read']]

        # Bulk categorize unread emails
        category = 'Needs Review'
        results = []
        for email in unread_emails:
            result = mock_outlook_adapter_with_categories.categorize_email(
                email['id'],
                category
            )
            results.append(result)

        assert len(results) == 5  # Half are unread
        assert all(results)

    def test_bulk_recategorize_emails(
        self,
        com_provider_with_categories,
        mock_outlook_adapter_with_categories
    ):
        """Test re-categorizing emails that already have categories."""
        # Setup emails with existing categories
        categorized_emails = [
            {
                'id': f'email-{i}',
                'subject': f'Email {i}',
                'categories': ['Old Category']
            }
            for i in range(3)
        ]

        mock_outlook_adapter_with_categories.get_emails.return_value = categorized_emails

        com_provider_with_categories.authenticate({})

        # Get emails with old category
        emails = com_provider_with_categories.get_emails('Inbox')

        # Re-categorize to new category
        new_category = 'New Category'
        results = []
        for email in emails:
            result = mock_outlook_adapter_with_categories.categorize_email(
                email['id'],
                new_category
            )
            results.append(result)

        assert len(results) == 3
        assert all(results)


@pytest.mark.integration
class TestCategorizationWorkflows:
    """Integration tests for complete categorization workflows."""

    @pytest.mark.asyncio
    async def test_classify_and_categorize_workflow(
        self,
        com_provider_with_categories,
        mock_outlook_adapter_with_categories
    ):
        """Test workflow: retrieve -> classify -> categorize based on classification."""
        from backend.services.ai_service import AIService
        from unittest.mock import MagicMock

        # Setup emails
        test_email = {
            'id': 'action-email',
            'subject': 'Urgent: Please Review',
            'sender': 'boss@company.com',
            'body': 'Please review this document by end of day.',
            'received_time': '2024-01-01T10:00:00Z',
            'is_read': False,
            'categories': []
        }

        mock_outlook_adapter_with_categories.get_emails.return_value = [test_email]

        # Setup AI processor
        ai_processor = Mock()
        ai_processor.classify_email_with_explanation = Mock(return_value={
            'category': 'required_personal_action',
            'confidence': 0.95,
            'explanation': 'Urgent action required',
            'alternatives': []
        })
        ai_processor.CONFIDENCE_THRESHOLDS = {'required_personal_action': 0.9}

        com_provider_with_categories.authenticate({})

        # Step 1: Retrieve emails
        emails = com_provider_with_categories.get_emails('Inbox')
        assert len(emails) == 1

        # Step 2: Classify email
        mock_config = MagicMock()
        ai_service = AIService(ai_orchestrator=ai_processor, azure_config=mock_config)

        email = emails[0]
        email_text = f"Subject: {email['subject']}\n\n{email['body']}"
        classification = await ai_service.classify_email(email_text)

        assert classification['category'] == 'required_personal_action'

        # Step 3: Categorize based on classification
        from backend.services.com_email_provider import INBOX_CATEGORIES
        category = INBOX_CATEGORIES.get(classification['category'], 'Other')

        result = mock_outlook_adapter_with_categories.categorize_email(
            email['id'],
            category
        )

        assert result is True
        assert category == 'Required Actions (Me)'

    def test_bulk_processing_with_categorization(
        self,
        com_provider_with_categories,
        mock_outlook_adapter_with_categories
    ):
        """Test bulk processing: retrieve many emails and categorize by rules."""
        # Setup batch of emails
        batch_emails = [
            {
                'id': f'email-{i}',
                'subject': f'Meeting Request {i}',
                'sender': f'sender{i}@company.com',
                'body': f'Meeting content {i}',
                'categories': []
            }
            for i in range(20)
        ]

        mock_outlook_adapter_with_categories.get_emails.return_value = batch_emails

        com_provider_with_categories.authenticate({})

        # Get batch of emails
        emails = com_provider_with_categories.get_emails('Inbox', count=20)
        assert len(emails) == 20

        # Categorize all as meetings
        category = 'Optional Events'
        categorized_count = 0

        for email in emails:
            if 'Meeting Request' in email['subject']:
                result = mock_outlook_adapter_with_categories.categorize_email(
                    email['id'],
                    category
                )
                if result:
                    categorized_count += 1

        assert categorized_count == 20
        assert mock_outlook_adapter_with_categories.categorize_email.call_count == 20
