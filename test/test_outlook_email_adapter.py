"""Unit tests for OutlookEmailAdapter.

This test module verifies that the OutlookEmailAdapter correctly wraps
OutlookManager functionality and implements the EmailProvider interface.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adapters.outlook_email_adapter import OutlookEmailAdapter
from core.interfaces import EmailProvider


class TestOutlookEmailAdapter(unittest.TestCase):
    """Test cases for OutlookEmailAdapter."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock OutlookManager
        self.mock_outlook_manager = Mock()
        self.mock_outlook_manager.namespace = Mock()
        self.mock_outlook_manager.inbox = Mock()
        
        # Create adapter with mocked manager
        self.adapter = OutlookEmailAdapter(outlook_manager=self.mock_outlook_manager)
    
    def test_implements_email_provider_interface(self):
        """Test that adapter implements EmailProvider interface."""
        self.assertIsInstance(self.adapter, EmailProvider)
        
        # Check required methods exist
        self.assertTrue(hasattr(self.adapter, 'get_emails'))
        self.assertTrue(hasattr(self.adapter, 'move_email'))
        self.assertTrue(hasattr(self.adapter, 'get_email_body'))
    
    def test_connect_success(self):
        """Test successful connection to Outlook."""
        self.mock_outlook_manager.connect_to_outlook = Mock()
        
        result = self.adapter.connect()
        
        self.assertTrue(result)
        self.assertTrue(self.adapter.connected)
        self.mock_outlook_manager.connect_to_outlook.assert_called_once()
    
    def test_connect_failure(self):
        """Test connection failure handling."""
        self.mock_outlook_manager.connect_to_outlook = Mock(
            side_effect=Exception("Connection failed")
        )
        
        result = self.adapter.connect()
        
        self.assertFalse(result)
        self.assertFalse(self.adapter.connected)
    
    def test_get_emails_requires_connection(self):
        """Test that get_emails raises error when not connected."""
        self.adapter.connected = False
        
        with self.assertRaises(RuntimeError) as context:
            self.adapter.get_emails()
        
        self.assertIn("Not connected", str(context.exception))
    
    def test_get_emails_success(self):
        """Test successful email retrieval."""
        self.adapter.connected = True
        
        # Mock email objects
        mock_email1 = self._create_mock_email(
            entry_id="email1",
            subject="Test Email 1",
            sender="sender1@example.com"
        )
        mock_email2 = self._create_mock_email(
            entry_id="email2",
            subject="Test Email 2",
            sender="sender2@example.com"
        )
        
        self.mock_outlook_manager.get_emails_from_inbox = Mock(
            return_value=[mock_email1, mock_email2]
        )
        
        emails = self.adapter.get_emails(folder_name="Inbox", count=2)
        
        self.assertEqual(len(emails), 2)
        self.assertEqual(emails[0]['id'], "email1")
        self.assertEqual(emails[0]['subject'], "Test Email 1")
        self.assertEqual(emails[1]['id'], "email2")
    
    def test_get_emails_with_pagination(self):
        """Test email retrieval with pagination."""
        self.adapter.connected = True
        
        # Mock 5 emails
        mock_emails = [
            self._create_mock_email(f"email{i}", f"Subject {i}", f"sender{i}@example.com")
            for i in range(5)
        ]
        
        self.mock_outlook_manager.get_emails_from_inbox = Mock(
            return_value=mock_emails
        )
        
        # Get 2 emails starting from offset 2
        emails = self.adapter.get_emails(folder_name="Inbox", count=2, offset=2)
        
        self.assertEqual(len(emails), 2)
        self.assertEqual(emails[0]['id'], "email2")
        self.assertEqual(emails[1]['id'], "email3")
    
    def test_move_email_success(self):
        """Test successful email move."""
        self.adapter.connected = True
        
        mock_email = Mock()
        mock_folder = Mock()
        
        self.mock_outlook_manager.namespace.GetItemFromID = Mock(
            return_value=mock_email
        )
        self.mock_outlook_manager._get_or_create_folder = Mock(
            return_value=mock_folder
        )
        
        result = self.adapter.move_email("email_id", "Archive")
        
        self.assertTrue(result)
        mock_email.Move.assert_called_once_with(mock_folder)
    
    def test_move_email_failure(self):
        """Test email move failure handling."""
        self.adapter.connected = True
        
        self.mock_outlook_manager.namespace.GetItemFromID = Mock(
            side_effect=Exception("Email not found")
        )
        
        result = self.adapter.move_email("bad_id", "Archive")
        
        self.assertFalse(result)
    
    def test_get_email_body_success(self):
        """Test successful email body retrieval."""
        self.adapter.connected = True
        
        mock_email = Mock()
        mock_email.Body = "This is the email body"
        
        self.mock_outlook_manager.namespace.GetItemFromID = Mock(
            return_value=mock_email
        )
        
        body = self.adapter.get_email_body("email_id")
        
        self.assertEqual(body, "This is the email body")
    
    def test_get_email_body_html_fallback(self):
        """Test email body retrieval with HTML fallback."""
        self.adapter.connected = True
        
        mock_email = Mock()
        mock_email.Body = None
        mock_email.HTMLBody = "<html>HTML body</html>"
        
        self.mock_outlook_manager.namespace.GetItemFromID = Mock(
            return_value=mock_email
        )
        
        body = self.adapter.get_email_body("email_id")
        
        self.assertEqual(body, "<html>HTML body</html>")
    
    def test_get_folders_success(self):
        """Test successful folder listing."""
        self.adapter.connected = True
        
        # Mock folder structure
        mock_folder1 = Mock()
        mock_folder1.EntryID = "folder1"
        mock_folder1.Name = "Inbox"
        
        mock_folder2 = Mock()
        mock_folder2.EntryID = "folder2"
        mock_folder2.Name = "Archive"
        
        mock_parent = Mock()
        mock_parent.Folders = [mock_folder1, mock_folder2]
        
        self.mock_outlook_manager.inbox.Parent = mock_parent
        
        folders = self.adapter.get_folders()
        
        self.assertEqual(len(folders), 2)
        self.assertEqual(folders[0]['name'], "Inbox")
        self.assertEqual(folders[1]['name'], "Archive")
    
    def test_mark_as_read_success(self):
        """Test marking email as read."""
        self.adapter.connected = True
        
        mock_email = Mock()
        mock_email.UnRead = True
        
        self.mock_outlook_manager.namespace.GetItemFromID = Mock(
            return_value=mock_email
        )
        
        result = self.adapter.mark_as_read("email_id")
        
        self.assertTrue(result)
        self.assertFalse(mock_email.UnRead)
        mock_email.Save.assert_called_once()
    
    def test_categorize_email_success(self):
        """Test email categorization."""
        self.adapter.connected = True
        
        mock_email = Mock()
        
        self.mock_outlook_manager.namespace.GetItemFromID = Mock(
            return_value=mock_email
        )
        self.mock_outlook_manager.categorize_email = Mock()
        
        result = self.adapter.categorize_email("email_id", "Work")
        
        self.assertTrue(result)
        self.mock_outlook_manager.categorize_email.assert_called_once_with(
            mock_email, "Work"
        )
    
    def _create_mock_email(self, entry_id, subject, sender):
        """Helper to create mock email object."""
        mock_email = Mock()
        mock_email.EntryID = entry_id
        mock_email.Subject = subject
        mock_email.SenderEmailAddress = sender
        mock_email.Body = f"Body of {subject}"
        mock_email.ReceivedTime = datetime.now()
        mock_email.UnRead = False
        mock_email.Categories = ""
        mock_email.ConversationID = f"conv_{entry_id}"
        
        # Mock Recipients
        mock_recipient = Mock()
        mock_recipient.Address = "recipient@example.com"
        mock_recipients = Mock()
        mock_recipients.Count = 1
        mock_recipients.Item = Mock(return_value=mock_recipient)
        mock_email.Recipients = mock_recipients
        
        return mock_email


if __name__ == '__main__':
    unittest.main()
