"""
Comprehensive tests for OutlookManager class.
Tests Outlook integration, email retrieval, and folder management with mocking.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Mock win32com before importing OutlookManager
with patch.dict('sys.modules', {'win32com': MagicMock(), 'win32com.client': MagicMock()}):
    from src.outlook_manager import OutlookManager, INBOX_CATEGORIES, NON_INBOX_CATEGORIES, CATEGORY_COLORS

class TestOutlookManager:
    """Comprehensive tests for OutlookManager class."""
    
    @pytest.fixture
    def mock_outlook_app(self):
        """Mock Outlook Application object."""
        mock_app = Mock()
        mock_namespace = Mock()
        mock_inbox = Mock()
        
        # Set up the mock chain
        mock_app.GetNamespace.return_value = mock_namespace
        mock_namespace.GetDefaultFolder.return_value = mock_inbox
        
        return mock_app, mock_namespace, mock_inbox
    
    @pytest.fixture
    def outlook_manager(self):
        """Create OutlookManager instance for testing."""
        return OutlookManager()
    
    @pytest.fixture
    def mock_email(self):
        """Create a mock email object."""
        email = Mock()
        email.Subject = "Test Email Subject"
        email.Body = "This is a test email body with some content."
        email.SenderName = "Test Sender"
        email.SenderEmailAddress = "sender@example.com"
        email.ReceivedTime = datetime.now()
        email.EntryID = "test_entry_123"
        email.Categories = ""
        email.UnRead = True
        email.Size = 1024
        return email
    
    def test_init(self, outlook_manager):
        """Test OutlookManager initialization."""
        assert outlook_manager.outlook is None
        assert outlook_manager.namespace is None
        assert outlook_manager.inbox is None
        assert outlook_manager.folders == {}
    
    @patch('src.outlook_manager.win32com.client.Dispatch')
    def test_connect_to_outlook_success(self, mock_dispatch, outlook_manager, mock_outlook_app):
        """Test successful connection to Outlook."""
        mock_app, mock_namespace, mock_inbox = mock_outlook_app
        mock_dispatch.return_value = mock_app
        
        result = outlook_manager.connect_to_outlook()
        
        assert result is True
        assert outlook_manager.outlook == mock_app
        assert outlook_manager.namespace == mock_namespace
        assert outlook_manager.inbox == mock_inbox
        
        mock_dispatch.assert_called_once_with("Outlook.Application")
        mock_app.GetNamespace.assert_called_once_with("MAPI")
    
    @patch('src.outlook_manager.win32com.client.Dispatch')
    def test_connect_to_outlook_failure(self, mock_dispatch, outlook_manager):
        """Test failed connection to Outlook."""
        mock_dispatch.side_effect = Exception("Outlook not available")
        
        result = outlook_manager.connect_to_outlook()
        
        assert result is False
        assert outlook_manager.outlook is None
    
    def test_is_connected_true(self, outlook_manager):
        """Test connection status when connected."""
        outlook_manager.outlook = Mock()
        outlook_manager.namespace = Mock()
        outlook_manager.inbox = Mock()
        
        assert outlook_manager.is_connected() is True
    
    def test_is_connected_false(self, outlook_manager):
        """Test connection status when not connected."""
        assert outlook_manager.is_connected() is False
    
    def test_get_or_create_folder_existing(self, outlook_manager):
        """Test getting existing folder."""
        mock_inbox = Mock()
        mock_folder = Mock()
        mock_folder.Name = "Test Folder"
        mock_inbox.Folders = [mock_folder]
        
        outlook_manager.inbox = mock_inbox
        
        result = outlook_manager.get_or_create_folder("Test Folder")
        
        assert result == mock_folder
    
    def test_get_or_create_folder_create_new(self, outlook_manager):
        """Test creating new folder when it doesn't exist."""
        mock_inbox = Mock()
        mock_existing_folder = Mock()
        mock_existing_folder.Name = "Other Folder"
        mock_inbox.Folders = [mock_existing_folder]
        
        mock_new_folder = Mock()
        mock_new_folder.Name = "New Folder"
        mock_inbox.Folders.Add.return_value = mock_new_folder
        
        outlook_manager.inbox = mock_inbox
        
        result = outlook_manager.get_or_create_folder("New Folder")
        
        assert result == mock_new_folder
        mock_inbox.Folders.Add.assert_called_once_with("New Folder")
    
    def test_get_or_create_folder_not_connected(self, outlook_manager):
        """Test folder creation when not connected."""
        result = outlook_manager.get_or_create_folder("Test Folder")
        assert result is None
    
    def test_categorize_email_success(self, outlook_manager, mock_email):
        """Test successful email categorization."""
        outlook_manager.outlook = Mock()
        
        result = outlook_manager.categorize_email(mock_email, "required_personal_action")
        
        assert result is True
        assert mock_email.Categories == CATEGORY_COLORS["required_personal_action"]
        mock_email.Save.assert_called_once()
    
    def test_categorize_email_failure(self, outlook_manager, mock_email):
        """Test email categorization failure."""
        outlook_manager.outlook = Mock()
        mock_email.Save.side_effect = Exception("Save failed")
        
        result = outlook_manager.categorize_email(mock_email, "required_personal_action")
        
        assert result is False
    
    def test_categorize_email_not_connected(self, outlook_manager, mock_email):
        """Test email categorization when not connected."""
        result = outlook_manager.categorize_email(mock_email, "required_personal_action")
        assert result is False
    
    def test_move_email_to_folder_success(self, outlook_manager, mock_email):
        """Test successful email moving."""
        mock_folder = Mock()
        outlook_manager.outlook = Mock()
        
        with patch.object(outlook_manager, 'get_or_create_folder', return_value=mock_folder):
            result = outlook_manager.move_email_to_folder(mock_email, "Test Folder")
        
        assert result is True
        mock_email.Move.assert_called_once_with(mock_folder)
    
    def test_move_email_to_folder_failure(self, outlook_manager, mock_email):
        """Test email moving failure."""
        mock_folder = Mock()
        outlook_manager.outlook = Mock()
        mock_email.Move.side_effect = Exception("Move failed")
        
        with patch.object(outlook_manager, 'get_or_create_folder', return_value=mock_folder):
            result = outlook_manager.move_email_to_folder(mock_email, "Test Folder")
        
        assert result is False
    
    def test_move_email_to_folder_no_folder(self, outlook_manager, mock_email):
        """Test email moving when folder creation fails."""
        outlook_manager.outlook = Mock()
        
        with patch.object(outlook_manager, 'get_or_create_folder', return_value=None):
            result = outlook_manager.move_email_to_folder(mock_email, "Test Folder")
        
        assert result is False
    
    def test_get_emails_from_folder_success(self, outlook_manager):
        """Test getting emails from folder."""
        mock_folder = Mock()
        mock_email1 = Mock()
        mock_email1.Subject = "Email 1"
        mock_email1.ReceivedTime = datetime.now()
        mock_email2 = Mock()
        mock_email2.Subject = "Email 2"
        mock_email2.ReceivedTime = datetime.now() - timedelta(hours=1)
        
        mock_folder.Items = [mock_email1, mock_email2]
        outlook_manager.outlook = Mock()
        
        with patch.object(outlook_manager, 'get_or_create_folder', return_value=mock_folder):
            emails = outlook_manager.get_emails_from_folder("Test Folder", limit=10)
        
        assert len(emails) == 2
        assert emails[0] == mock_email1  # Should be sorted by ReceivedTime
        assert emails[1] == mock_email2
    
    def test_get_emails_from_folder_with_limit(self, outlook_manager):
        """Test getting emails from folder with limit."""
        mock_folder = Mock()
        mock_emails = []
        for i in range(5):
            email = Mock()
            email.Subject = f"Email {i}"
            email.ReceivedTime = datetime.now() - timedelta(hours=i)
            mock_emails.append(email)
        
        mock_folder.Items = mock_emails
        outlook_manager.outlook = Mock()
        
        with patch.object(outlook_manager, 'get_or_create_folder', return_value=mock_folder):
            emails = outlook_manager.get_emails_from_folder("Test Folder", limit=3)
        
        assert len(emails) == 3
    
    def test_get_emails_from_folder_no_folder(self, outlook_manager):
        """Test getting emails when folder doesn't exist."""
        outlook_manager.outlook = Mock()
        
        with patch.object(outlook_manager, 'get_or_create_folder', return_value=None):
            emails = outlook_manager.get_emails_from_folder("Nonexistent Folder")
        
        assert emails == []
    
    def test_get_inbox_emails(self, outlook_manager):
        """Test getting emails from inbox."""
        mock_email = Mock()
        mock_email.Subject = "Inbox Email"
        mock_email.ReceivedTime = datetime.now()
        
        mock_inbox = Mock()
        mock_inbox.Items = [mock_email]
        outlook_manager.inbox = mock_inbox
        outlook_manager.outlook = Mock()
        
        emails = outlook_manager.get_inbox_emails(limit=10)
        
        assert len(emails) == 1
        assert emails[0] == mock_email
    
    def test_get_inbox_emails_not_connected(self, outlook_manager):
        """Test getting inbox emails when not connected."""
        emails = outlook_manager.get_inbox_emails()
        assert emails == []
    
    def test_mark_email_as_read(self, outlook_manager, mock_email):
        """Test marking email as read."""
        outlook_manager.outlook = Mock()
        mock_email.UnRead = True
        
        result = outlook_manager.mark_email_as_read(mock_email)
        
        assert result is True
        assert mock_email.UnRead is False
        mock_email.Save.assert_called_once()
    
    def test_mark_email_as_read_failure(self, outlook_manager, mock_email):
        """Test marking email as read failure."""
        outlook_manager.outlook = Mock()
        mock_email.Save.side_effect = Exception("Save failed")
        
        result = outlook_manager.mark_email_as_read(mock_email)
        assert result is False
    
    def test_search_emails_by_subject(self, outlook_manager):
        """Test searching emails by subject."""
        mock_email1 = Mock()
        mock_email1.Subject = "Meeting Request"
        mock_email1.ReceivedTime = datetime.now()
        mock_email2 = Mock()
        mock_email2.Subject = "Project Update"
        mock_email2.ReceivedTime = datetime.now()
        mock_email3 = Mock()
        mock_email3.Subject = "Another Meeting"
        mock_email3.ReceivedTime = datetime.now()
        
        mock_inbox = Mock()
        mock_inbox.Items = [mock_email1, mock_email2, mock_email3]
        outlook_manager.inbox = mock_inbox
        outlook_manager.outlook = Mock()
        
        results = outlook_manager.search_emails_by_subject("Meeting")
        
        assert len(results) == 2
        subjects = [email.Subject for email in results]
        assert "Meeting Request" in subjects
        assert "Another Meeting" in subjects
        assert "Project Update" not in subjects
    
    def test_search_emails_by_sender(self, outlook_manager):
        """Test searching emails by sender."""
        mock_email1 = Mock()
        mock_email1.SenderEmailAddress = "manager@company.com"
        mock_email1.ReceivedTime = datetime.now()
        mock_email2 = Mock()
        mock_email2.SenderEmailAddress = "colleague@company.com"
        mock_email2.ReceivedTime = datetime.now()
        mock_email3 = Mock()
        mock_email3.SenderEmailAddress = "manager@company.com"
        mock_email3.ReceivedTime = datetime.now()
        
        mock_inbox = Mock()
        mock_inbox.Items = [mock_email1, mock_email2, mock_email3]
        outlook_manager.inbox = mock_inbox
        outlook_manager.outlook = Mock()
        
        results = outlook_manager.search_emails_by_sender("manager@company.com")
        
        assert len(results) == 2
        assert all(email.SenderEmailAddress == "manager@company.com" for email in results)
    
    def test_get_recent_emails(self, outlook_manager):
        """Test getting recent emails within date range."""
        now = datetime.now()
        mock_email1 = Mock()
        mock_email1.ReceivedTime = now  # Recent
        mock_email2 = Mock()
        mock_email2.ReceivedTime = now - timedelta(days=5)  # Too old
        mock_email3 = Mock()
        mock_email3.ReceivedTime = now - timedelta(hours=12)  # Recent
        
        mock_inbox = Mock()
        mock_inbox.Items = [mock_email1, mock_email2, mock_email3]
        outlook_manager.inbox = mock_inbox
        outlook_manager.outlook = Mock()
        
        results = outlook_manager.get_recent_emails(days=3)
        
        assert len(results) == 2
        # Should not include the 5-day-old email
        received_times = [email.ReceivedTime for email in results]
        assert mock_email2.ReceivedTime not in received_times
    
    def test_get_unread_emails(self, outlook_manager):
        """Test getting unread emails."""
        mock_email1 = Mock()
        mock_email1.UnRead = True
        mock_email1.ReceivedTime = datetime.now()
        mock_email2 = Mock()
        mock_email2.UnRead = False
        mock_email2.ReceivedTime = datetime.now()
        mock_email3 = Mock()
        mock_email3.UnRead = True
        mock_email3.ReceivedTime = datetime.now()
        
        mock_inbox = Mock()
        mock_inbox.Items = [mock_email1, mock_email2, mock_email3]
        outlook_manager.inbox = mock_inbox
        outlook_manager.outlook = Mock()
        
        results = outlook_manager.get_unread_emails()
        
        assert len(results) == 2
        assert all(email.UnRead is True for email in results)
    
    def test_delete_email_success(self, outlook_manager, mock_email):
        """Test successful email deletion."""
        outlook_manager.outlook = Mock()
        
        result = outlook_manager.delete_email(mock_email)
        
        assert result is True
        mock_email.Delete.assert_called_once()
    
    def test_delete_email_failure(self, outlook_manager, mock_email):
        """Test email deletion failure."""
        outlook_manager.outlook = Mock()
        mock_email.Delete.side_effect = Exception("Delete failed")
        
        result = outlook_manager.delete_email(mock_email)
        assert result is False
    
    def test_get_email_attachments(self, outlook_manager, mock_email):
        """Test getting email attachments."""
        mock_attachment1 = Mock()
        mock_attachment1.FileName = "document.pdf"
        mock_attachment1.Size = 1024
        mock_attachment2 = Mock()
        mock_attachment2.FileName = "image.jpg"
        mock_attachment2.Size = 2048
        
        mock_email.Attachments = [mock_attachment1, mock_attachment2]
        outlook_manager.outlook = Mock()
        
        attachments = outlook_manager.get_email_attachments(mock_email)
        
        assert len(attachments) == 2
        assert attachments[0].FileName == "document.pdf"
        assert attachments[1].FileName == "image.jpg"
    
    def test_get_email_attachments_none(self, outlook_manager, mock_email):
        """Test getting attachments when email has none."""
        mock_email.Attachments = []
        outlook_manager.outlook = Mock()
        
        attachments = outlook_manager.get_email_attachments(mock_email)
        assert attachments == []
    
    def test_create_email_draft(self, outlook_manager):
        """Test creating email draft."""
        mock_mail_item = Mock()
        mock_outlook = Mock()
        mock_outlook.CreateItem.return_value = mock_mail_item
        outlook_manager.outlook = mock_outlook
        
        result = outlook_manager.create_email_draft(
            to="recipient@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        assert result == mock_mail_item
        assert mock_mail_item.To == "recipient@example.com"
        assert mock_mail_item.Subject == "Test Subject"
        assert mock_mail_item.Body == "Test Body"
        mock_outlook.CreateItem.assert_called_once()
    
    def test_create_email_draft_not_connected(self, outlook_manager):
        """Test creating email draft when not connected."""
        result = outlook_manager.create_email_draft(
            to="recipient@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        assert result is None
    
    def test_get_folder_statistics(self, outlook_manager):
        """Test getting folder statistics."""
        mock_folder = Mock()
        mock_email1 = Mock()
        mock_email1.UnRead = True
        mock_email1.Size = 1024
        mock_email2 = Mock()
        mock_email2.UnRead = False
        mock_email2.Size = 2048
        mock_email3 = Mock()
        mock_email3.UnRead = True
        mock_email3.Size = 512
        
        mock_folder.Items = [mock_email1, mock_email2, mock_email3]
        outlook_manager.outlook = Mock()
        
        with patch.object(outlook_manager, 'get_or_create_folder', return_value=mock_folder):
            stats = outlook_manager.get_folder_statistics("Test Folder")
        
        assert stats['total_count'] == 3
        assert stats['unread_count'] == 2
        assert stats['total_size'] == 3584  # 1024 + 2048 + 512
    
    def test_batch_process_emails(self, outlook_manager):
        """Test batch processing of emails."""
        mock_emails = []
        for i in range(5):
            email = Mock()
            email.Subject = f"Email {i}"
            email.UnRead = True
            mock_emails.append(email)
        
        outlook_manager.outlook = Mock()
        
        def mark_read_func(email):
            email.UnRead = False
            return True
        
        results = outlook_manager.batch_process_emails(mock_emails, mark_read_func)
        
        assert len(results) == 5
        assert all(result is True for result in results)
        assert all(email.UnRead is False for email in mock_emails)
    
    def test_reconnect_after_failure(self, outlook_manager):
        """Test reconnection after connection failure."""
        # Simulate initial connection failure
        with patch('src.outlook_manager.win32com.client.Dispatch', side_effect=Exception("Connection failed")):
            result1 = outlook_manager.connect_to_outlook()
            assert result1 is False
        
        # Simulate successful reconnection
        mock_app = Mock()
        mock_namespace = Mock()
        mock_inbox = Mock()
        mock_app.GetNamespace.return_value = mock_namespace
        mock_namespace.GetDefaultFolder.return_value = mock_inbox
        
        with patch('src.outlook_manager.win32com.client.Dispatch', return_value=mock_app):
            result2 = outlook_manager.connect_to_outlook()
            assert result2 is True
            assert outlook_manager.outlook == mock_app
    
    def test_error_handling_with_corrupted_email(self, outlook_manager):
        """Test error handling with corrupted email objects."""
        mock_corrupted_email = Mock()
        # Simulate corrupted email by making properties raise exceptions
        mock_corrupted_email.Subject.side_effect = Exception("Corrupted email")
        
        mock_normal_email = Mock()
        mock_normal_email.Subject = "Normal Email"
        mock_normal_email.ReceivedTime = datetime.now()
        
        mock_inbox = Mock()
        mock_inbox.Items = [mock_corrupted_email, mock_normal_email]
        outlook_manager.inbox = mock_inbox
        outlook_manager.outlook = Mock()
        
        # Should handle corrupted email gracefully
        emails = outlook_manager.get_inbox_emails()
        
        # Should still return the normal email
        assert len(emails) >= 1
        valid_emails = [email for email in emails if hasattr(email, 'Subject') and not callable(email.Subject)]
        assert len(valid_emails) >= 1
    
    def test_constants_and_mappings(self):
        """Test that category constants and mappings are properly defined."""
        # Test inbox categories
        assert 'required_personal_action' in INBOX_CATEGORIES
        assert 'optional_action' in INBOX_CATEGORIES
        assert 'job_listing' in INBOX_CATEGORIES
        assert 'work_relevant' in INBOX_CATEGORIES
        
        # Test non-inbox categories
        assert 'team_action' in NON_INBOX_CATEGORIES
        assert 'optional_event' in NON_INBOX_CATEGORIES
        assert 'fyi' in NON_INBOX_CATEGORIES
        assert 'spam_to_delete' in NON_INBOX_CATEGORIES
        
        # Test category colors
        assert 'required_personal_action' in CATEGORY_COLORS
        assert 'team_action' in CATEGORY_COLORS
        assert all(color.endswith('Category') for color in CATEGORY_COLORS.values())