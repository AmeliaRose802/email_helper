"""Integration tests for COM Outlook adapter.

Tests the COMEmailProvider integration with the OutlookEmailAdapter,
verifying real workflow patterns including email retrieval, folder operations,
and error handling with proper mocking of COM dependencies.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from fastapi import HTTPException


@pytest.fixture
def mock_outlook_adapter():
    """Create a mock OutlookEmailAdapter for testing."""
    adapter = MagicMock()
    adapter.connect = Mock(return_value=True)
    adapter.get_emails = Mock(return_value=[])
    adapter.get_email_body = Mock(return_value="Test email body")
    adapter.get_folders = Mock(return_value=[])
    adapter.mark_as_read = Mock(return_value=True)
    adapter.move_email = Mock(return_value=True)
    adapter.get_conversation_emails = Mock(return_value=[])
    return adapter


@pytest.fixture
def com_email_provider(mock_outlook_adapter):
    """Create COMEmailProvider with mocked adapter."""
    with patch('backend.services.com_email_provider.OutlookEmailAdapter', return_value=mock_outlook_adapter):
        with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
            from backend.services.com_email_provider import COMEmailProvider
            provider = COMEmailProvider()
            provider.adapter = mock_outlook_adapter
            return provider


@pytest.mark.integration
class TestCOMOutlookIntegration:
    """Integration tests for COM Outlook email operations."""
    
    def test_email_retrieval_workflow(self, com_email_provider, mock_outlook_adapter):
        """Test complete email retrieval workflow from authentication to fetching."""
        # Setup mock emails
        mock_emails = [
            {
                'id': 'email-1',
                'subject': 'Test Email 1',
                'sender': 'sender1@example.com',
                'recipient': 'user@example.com',
                'body': 'Email body 1',
                'received_time': '2024-01-01T10:00:00Z',
                'is_read': False,
                'categories': [],
                'conversation_id': 'conv-1'
            },
            {
                'id': 'email-2',
                'subject': 'Test Email 2',
                'sender': 'sender2@example.com',
                'recipient': 'user@example.com',
                'body': 'Email body 2',
                'received_time': '2024-01-01T11:00:00Z',
                'is_read': True,
                'categories': ['Important'],
                'conversation_id': 'conv-2'
            }
        ]
        mock_outlook_adapter.get_emails.return_value = mock_emails
        
        # Authenticate
        result = com_email_provider.authenticate({})
        assert result is True
        assert com_email_provider.authenticated
        mock_outlook_adapter.connect.assert_called_once()
        
        # Retrieve emails
        emails = com_email_provider.get_emails("Inbox", count=5)
        assert len(emails) == 2
        assert emails[0]['subject'] == 'Test Email 1'
        assert emails[1]['subject'] == 'Test Email 2'
        mock_outlook_adapter.get_emails.assert_called_once_with(
            folder_name="Inbox",
            count=5,
            offset=0
        )
    
    def test_email_retrieval_with_pagination(self, com_email_provider, mock_outlook_adapter):
        """Test email retrieval with pagination support."""
        # Setup paginated emails
        page1_emails = [
            {'id': f'email-{i}', 'subject': f'Email {i}', 'sender': f'sender{i}@example.com'}
            for i in range(1, 11)
        ]
        page2_emails = [
            {'id': f'email-{i}', 'subject': f'Email {i}', 'sender': f'sender{i}@example.com'}
            for i in range(11, 21)
        ]
        
        # Mock adapter to return different pages
        mock_outlook_adapter.get_emails.side_effect = [page1_emails, page2_emails]
        
        # Authenticate
        com_email_provider.authenticate({})
        
        # Get first page
        emails_page1 = com_email_provider.get_emails("Inbox", count=10, offset=0)
        assert len(emails_page1) == 10
        assert emails_page1[0]['id'] == 'email-1'
        
        # Get second page
        emails_page2 = com_email_provider.get_emails("Inbox", count=10, offset=10)
        assert len(emails_page2) == 10
        assert emails_page2[0]['id'] == 'email-11'
        
        # Verify pagination calls
        assert mock_outlook_adapter.get_emails.call_count == 2
        calls = mock_outlook_adapter.get_emails.call_args_list
        assert calls[0] == call(folder_name="Inbox", count=10, offset=0)
        assert calls[1] == call(folder_name="Inbox", count=10, offset=10)
    
    def test_folder_operations_workflow(self, com_email_provider, mock_outlook_adapter):
        """Test folder listing and navigation workflow."""
        mock_folders = [
            {'id': 'inbox', 'name': 'Inbox', 'item_count': 25},
            {'id': 'sent', 'name': 'Sent Items', 'item_count': 10},
            {'id': 'drafts', 'name': 'Drafts', 'item_count': 3},
            {'id': 'deleted', 'name': 'Deleted Items', 'item_count': 5}
        ]
        mock_outlook_adapter.get_folders.return_value = mock_folders
        
        # Authenticate
        com_email_provider.authenticate({})
        
        # Get folders
        folders = com_email_provider.get_folders()
        assert len(folders) == 4
        assert folders[0]['name'] == 'Inbox'
        assert folders[0]['item_count'] == 25
        mock_outlook_adapter.get_folders.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_email_content_retrieval(self, com_email_provider, mock_outlook_adapter):
        """Test detailed email content retrieval."""
        mock_outlook_adapter.get_email_by_id.return_value = {
            'id': 'email-123',
            'subject': 'Test Email',
            'sender': 'test@example.com',
            'body': 'Initial body',
            'importance': 'Normal'
        }
        mock_outlook_adapter.get_email_body.return_value = "Full email body with details"
        
        # Authenticate
        com_email_provider.authenticate({})
        
        # Get email content
        content = await com_email_provider.get_email_content('email-123')
        assert content['id'] == 'email-123'
        assert 'Full email body' in content['body']
        mock_outlook_adapter.get_email_body.assert_called_once_with('email-123')
    
    def test_mark_as_read_workflow(self, com_email_provider, mock_outlook_adapter):
        """Test marking emails as read."""
        mock_outlook_adapter.mark_as_read.return_value = True
        
        # Authenticate
        com_email_provider.authenticate({})
        
        # Mark email as read
        result = com_email_provider.mark_as_read('email-456')
        assert result is True
        mock_outlook_adapter.mark_as_read.assert_called_once_with('email-456')
    
    def test_move_email_workflow(self, com_email_provider, mock_outlook_adapter):
        """Test moving emails between folders."""
        mock_outlook_adapter.move_email.return_value = True
        
        # Authenticate
        com_email_provider.authenticate({})
        
        # Move email
        result = com_email_provider.move_email('email-789', 'Archive')
        assert result is True
        mock_outlook_adapter.move_email.assert_called_once_with('email-789', 'Archive')
    
    def test_conversation_thread_retrieval(self, com_email_provider, mock_outlook_adapter):
        """Test retrieving email conversation threads."""
        # Mock emails with conversation IDs
        all_emails = [
            {'id': 'email-1', 'subject': 'Re: Meeting', 'sender': 'alice@example.com', 'conversation_id': 'conv-meeting-123'},
            {'id': 'email-2', 'subject': 'Re: Meeting', 'sender': 'bob@example.com', 'conversation_id': 'conv-meeting-123'},
            {'id': 'email-3', 'subject': 'Re: Meeting', 'sender': 'alice@example.com', 'conversation_id': 'conv-meeting-123'},
            {'id': 'email-4', 'subject': 'Other', 'sender': 'other@example.com', 'conversation_id': 'conv-other'}
        ]
        mock_outlook_adapter.get_emails.return_value = all_emails
        
        # Authenticate
        com_email_provider.authenticate({})
        
        # Get conversation thread
        thread = com_email_provider.get_conversation_thread('conv-meeting-123')
        assert len(thread) == 3
        assert all(email['conversation_id'] == 'conv-meeting-123' for email in thread)


@pytest.mark.integration
class TestCOMOutlookErrorHandling:
    """Integration tests for COM Outlook error handling."""
    
    def test_authentication_failure(self, mock_outlook_adapter):
        """Test handling of authentication failures."""
        mock_outlook_adapter.connect.return_value = False
        
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', return_value=mock_outlook_adapter):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                from fastapi import HTTPException
                
                provider = COMEmailProvider()
                provider.adapter = mock_outlook_adapter
                
                # Should raise HTTPException with 503 status
                with pytest.raises(HTTPException) as exc_info:
                    provider.authenticate({})
                
                assert exc_info.value.status_code == 503
                assert not provider.authenticated
    
    def test_connection_failure_during_operation(self, com_email_provider, mock_outlook_adapter):
        """Test handling of connection failures during operations."""
        # Authenticate first
        com_email_provider.authenticate({})
        
        # Simulate connection failure
        mock_outlook_adapter.get_emails.side_effect = RuntimeError("Outlook connection lost")
        
        # Should raise HTTPException with 401 status
        with pytest.raises(HTTPException) as exc_info:
            com_email_provider.get_emails("Inbox")
        
        assert exc_info.value.status_code == 401
        assert "Outlook connection lost" in str(exc_info.value.detail)
        # Provider should mark itself as not authenticated
        assert not com_email_provider.authenticated
    
    def test_not_authenticated_error(self, com_email_provider, mock_outlook_adapter):
        """Test operations without authentication."""
        # Don't authenticate
        com_email_provider.authenticated = False
        
        # Simulate connection failure
        mock_outlook_adapter.connect.return_value = False
        
        # Try to get emails without authenticating (connection will fail)
        with pytest.raises(HTTPException) as exc_info:
            com_email_provider.get_emails("Inbox")
        
        assert exc_info.value.status_code == 401
        assert "Failed to connect" in str(exc_info.value.detail)
    
    def test_folder_not_found_error(self, com_email_provider, mock_outlook_adapter):
        """Test handling of non-existent folder access."""
        com_email_provider.authenticate({})
        
        # Simulate folder not found
        mock_outlook_adapter.get_emails.side_effect = ValueError("Folder 'NonExistent' not found")
        
        # Should raise HTTPException with 500 status (generic error)
        with pytest.raises(HTTPException) as exc_info:
            com_email_provider.get_emails("NonExistent")
        
        assert exc_info.value.status_code == 500
        assert "Folder 'NonExistent' not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_email_not_found_error(self, com_email_provider, mock_outlook_adapter):
        """Test handling of non-existent email access."""
        com_email_provider.authenticate({})
        
        # Simulate email not found
        mock_outlook_adapter.get_email_by_id.return_value = None
        
        # Should raise HTTPException with 404 status
        with pytest.raises(HTTPException) as exc_info:
            await com_email_provider.get_email_content("nonexistent-email")
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()
    
    def test_com_exception_handling(self, com_email_provider, mock_outlook_adapter):
        """Test handling of general COM exceptions."""
        com_email_provider.authenticate({})
        
        # Simulate COM exception
        mock_outlook_adapter.get_emails.side_effect = Exception("COM Error: Access denied")
        
        with pytest.raises(HTTPException) as exc_info:
            com_email_provider.get_emails("Inbox")
        
        assert exc_info.value.status_code == 500
        assert "COM Error" in str(exc_info.value.detail)
    
    def test_mark_as_read_failure(self, com_email_provider, mock_outlook_adapter):
        """Test handling of mark as read failures."""
        com_email_provider.authenticate({})
        
        # Simulate failure
        mock_outlook_adapter.mark_as_read.return_value = False
        
        result = com_email_provider.mark_as_read('email-fail')
        assert result is False
    
    def test_move_email_failure(self, com_email_provider, mock_outlook_adapter):
        """Test handling of move email failures."""
        com_email_provider.authenticate({})
        
        # Simulate failure
        mock_outlook_adapter.move_email.return_value = False
        
        result = com_email_provider.move_email('email-fail', 'Archive')
        assert result is False


@pytest.mark.integration
class TestCOMOutlookConcurrency:
    """Integration tests for concurrent COM operations."""
    
    def test_multiple_folder_access(self, com_email_provider, mock_outlook_adapter):
        """Test accessing multiple folders in sequence."""
        # Setup different folders with different emails
        inbox_emails = [{'id': 'inbox-1', 'subject': 'Inbox Email'}]
        sent_emails = [{'id': 'sent-1', 'subject': 'Sent Email'}]
        
        def get_emails_side_effect(folder_name, count, offset):
            if folder_name == "Inbox":
                return inbox_emails
            elif folder_name == "Sent Items":
                return sent_emails
            return []
        
        mock_outlook_adapter.get_emails.side_effect = get_emails_side_effect
        
        # Authenticate
        com_email_provider.authenticate({})
        
        # Access multiple folders
        inbox = com_email_provider.get_emails("Inbox", count=10)
        sent = com_email_provider.get_emails("Sent Items", count=10)
        
        assert len(inbox) == 1
        assert inbox[0]['subject'] == 'Inbox Email'
        assert len(sent) == 1
        assert sent[0]['subject'] == 'Sent Email'
    
    def test_batch_email_operations(self, com_email_provider, mock_outlook_adapter):
        """Test performing multiple operations on different emails."""
        com_email_provider.authenticate({})
        
        # Mark multiple emails as read
        email_ids = ['email-1', 'email-2', 'email-3']
        results = []
        
        for email_id in email_ids:
            result = com_email_provider.mark_as_read(email_id)
            results.append(result)
        
        assert all(results)
        assert mock_outlook_adapter.mark_as_read.call_count == 3
