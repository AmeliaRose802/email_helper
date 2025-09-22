#!/usr/bin/env python3
"""
Test the UI dismiss functionality to ensure items are properly removed after dismissal
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from task_persistence import TaskPersistence
from unified_gui import UnifiedEmailGUI

class TestUIDismissFunctionality(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.test_storage_dir = os.path.join(os.path.dirname(__file__), 'test_data', 'dismiss_test')
        os.makedirs(self.test_storage_dir, exist_ok=True)
        
        # Create test task persistence with isolated storage
        self.task_persistence = TaskPersistence(self.test_storage_dir)
        
        # Create test data
        self.test_summary_sections = {
            'required_actions': [
                {'task_id': 'req1', 'subject': 'Test Required Action', 'sender': 'test@example.com'}
            ],
            'optional_actions': [
                {'task_id': 'opt1', 'subject': 'Test Optional Action', 'sender': 'test@example.com'}
            ],
            'fyi_notices': [
                {'task_id': 'fyi1', 'subject': 'Test FYI Notice', 'sender': 'test@example.com'},
                {'task_id': 'fyi2', 'subject': 'Another FYI Notice', 'sender': 'test2@example.com'}
            ],
            'newsletters': [
                {'task_id': 'news1', 'subject': 'Test Newsletter', 'sender': 'newsletter@example.com'}
            ]
        }
        
        # Save test data
        self.task_persistence.save_outstanding_tasks(self.test_summary_sections, '2025-01-01 12:00:00')
    
    def tearDown(self):
        """Clean up test data"""
        import shutil
        if os.path.exists(self.test_storage_dir):
            shutil.rmtree(self.test_storage_dir)
    
    def test_task_persistence_clear_fyi_items(self):
        """Test that FYI items are properly cleared from persistent storage"""
        # Verify FYI items exist initially
        outstanding = self.task_persistence.load_outstanding_tasks()
        self.assertEqual(len(outstanding['fyi_notices']), 2)
        
        # Clear FYI items
        cleared_count = self.task_persistence.clear_fyi_items()
        self.assertEqual(cleared_count, 2)
        
        # Verify FYI items are removed
        outstanding_after = self.task_persistence.load_outstanding_tasks()
        self.assertEqual(len(outstanding_after['fyi_notices']), 0)
        
        # Verify other items are not affected
        self.assertEqual(len(outstanding_after['required_actions']), 1)
        self.assertEqual(len(outstanding_after['optional_actions']), 1)
        self.assertEqual(len(outstanding_after['newsletters']), 1)
    
    def test_task_persistence_clear_newsletter_items(self):
        """Test that newsletter items are properly cleared from persistent storage"""
        # Verify newsletter items exist initially
        outstanding = self.task_persistence.load_outstanding_tasks()
        self.assertEqual(len(outstanding['newsletters']), 1)
        
        # Clear newsletter items
        cleared_count = self.task_persistence.clear_newsletter_items()
        self.assertEqual(cleared_count, 1)
        
        # Verify newsletter items are removed
        outstanding_after = self.task_persistence.load_outstanding_tasks()
        self.assertEqual(len(outstanding_after['newsletters']), 0)
        
        # Verify other items are not affected
        self.assertEqual(len(outstanding_after['required_actions']), 1)
        self.assertEqual(len(outstanding_after['optional_actions']), 1)
        self.assertEqual(len(outstanding_after['fyi_notices']), 2)
    
    def test_task_completion_removes_from_outstanding(self):
        """Test that marking tasks as complete removes them from outstanding tasks"""
        # Create a fresh test storage directory
        import shutil
        import uuid
        
        test_id = str(uuid.uuid4())[:8]
        completion_test_dir = os.path.join(os.path.dirname(__file__), 'test_data', f'completion_test_{test_id}')
        os.makedirs(completion_test_dir, exist_ok=True)
        
        # Create separate task persistence for this test
        completion_tp = TaskPersistence(completion_test_dir)
        
        # Create test data with explicit task ID
        test_data = {
            'optional_actions': [
                {'task_id': 'opt1', 'subject': 'Test Optional Action', 'sender': 'test@example.com'}
            ]
        }
        
        # Save test data
        completion_tp.save_outstanding_tasks(test_data, '2025-01-01 12:00:00')
        
        # Verify task exists initially
        outstanding = completion_tp.load_outstanding_tasks()
        self.assertEqual(len(outstanding['optional_actions']), 1)
        self.assertEqual(outstanding['optional_actions'][0]['task_id'], 'opt1')
        
        # Mark task as complete
        completion_tp.mark_tasks_completed(['opt1'])
        
        # Verify task is removed from outstanding
        outstanding_after = completion_tp.load_outstanding_tasks()
        self.assertEqual(len(outstanding_after['optional_actions']), 0)
        
        # Clean up
        shutil.rmtree(completion_test_dir)
    
    @patch('src.unified_gui.OutlookManager')
    @patch('src.unified_gui.AIProcessor')
    @patch('src.unified_gui.EmailAnalyzer')
    @patch('src.unified_gui.SummaryGenerator')
    @patch('src.unified_gui.EmailProcessor')
    @patch('tkinter.Tk')
    def test_ui_refresh_method_logic(self, mock_tk, mock_email_processor, mock_summary_gen, 
                                   mock_email_analyzer, mock_ai_processor, mock_outlook):
        """Test the refresh logic in GUI methods"""
        # Create GUI instance with mocked dependencies
        gui = UnifiedEmailGUI()
        
        # Replace task persistence with our test instance
        gui.task_persistence = self.task_persistence
        
        # Mock GUI methods
        gui.generate_summary = Mock()
        gui.view_outstanding_tasks_only = Mock()
        
        # Test refresh with no current data (should call view_outstanding_tasks_only)
        gui.action_items_data = {}
        gui._refresh_summary_after_dismiss()
        gui.view_outstanding_tasks_only.assert_called_once()
        gui.generate_summary.assert_not_called()
        
        # Reset mocks
        gui.generate_summary.reset_mock()
        gui.view_outstanding_tasks_only.reset_mock()
        
        # Test refresh with current data (should call generate_summary)
        gui.action_items_data = {'some': 'data'}
        gui._refresh_summary_after_dismiss()
        gui.generate_summary.assert_called_once()
        gui.view_outstanding_tasks_only.assert_not_called()

if __name__ == '__main__':
    unittest.main()