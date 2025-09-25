#!/usr/bin/env python3
"""
Test Frontend Improvements
Tests for UI bug fixes and usability improvements
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

class TestFrontendImprovements(unittest.TestCase):
    """Test UI improvements and bug fixes"""
    
    def setUp(self):
        """Setup test environment"""
        self.mock_outlook = Mock()
        self.mock_ai_processor = Mock()
        self.mock_email_processor = Mock()
        self.mock_email_analyzer = Mock()
        self.mock_summary_generator = Mock()
        self.mock_task_persistence = Mock()
        
        # Configure mocks
        self.mock_ai_processor.azure_config = {'endpoint': 'test', 'key': 'test'}
        self.mock_email_processor.get_action_items_data.return_value = {}
        self.mock_outlook.get_emails_with_full_conversations.return_value = []
    
    def test_custom_count_validation(self):
        """Test A3: Custom email count auto-selection and validation"""
        with patch('unified_gui.OutlookManager', return_value=self.mock_outlook), \
             patch('unified_gui.AIProcessor', return_value=self.mock_ai_processor), \
             patch('unified_gui.EmailProcessor', return_value=self.mock_email_processor), \
             patch('unified_gui.EmailAnalyzer', return_value=self.mock_email_analyzer), \
             patch('unified_gui.SummaryGenerator', return_value=self.mock_summary_generator), \
             patch('unified_gui.TaskPersistence', return_value=self.mock_task_persistence):
            
            from unified_gui import UnifiedEmailGUI
            gui = UnifiedEmailGUI()
            gui.root.withdraw()  # Hide during testing
            
            # Test valid number auto-selects "other"
            gui.custom_count_entry.insert(0, "75")
            gui._validate_and_select_other()
            self.assertEqual(gui.email_count_var.get(), "other")
            
            # Test invalid number handling
            gui.custom_count_entry.delete(0, 'end')
            gui.custom_count_entry.insert(0, "0")
            gui._validate_and_select_other()
            # Should not change to "other" for invalid numbers
            
            gui.root.destroy()
    
    def test_descriptive_link_text_generation(self):
        """Test A5+A6: Descriptive link labels generation"""
        with patch('unified_gui.OutlookManager', return_value=self.mock_outlook), \
             patch('unified_gui.AIProcessor', return_value=self.mock_ai_processor), \
             patch('unified_gui.EmailProcessor', return_value=self.mock_email_processor), \
             patch('unified_gui.EmailAnalyzer', return_value=self.mock_email_analyzer), \
             patch('unified_gui.SummaryGenerator', return_value=self.mock_summary_generator), \
             patch('unified_gui.TaskPersistence', return_value=self.mock_task_persistence):
            
            from unified_gui import UnifiedEmailGUI
            gui = UnifiedEmailGUI()
            gui.root.withdraw()
            
            # Test job-related links
            job_url = "https://careers.company.com/apply/12345"
            result = gui._create_descriptive_link_text(job_url, 'job')
            self.assertEqual(result, 'Apply Now')
            
            # Test GitHub links
            github_url = "https://github.com/user/repo"
            result = gui._create_descriptive_link_text(github_url, 'general')
            self.assertEqual(result, 'View on GitHub')
            
            # Test Teams meeting links
            teams_url = "https://teams.microsoft.com/l/meetup-join/"
            result = gui._create_descriptive_link_text(teams_url, 'general')
            self.assertEqual(result, 'Join Teams Meeting')
            
            # Test survey links
            survey_url = "https://forms.office.com/r/survey123"
            result = gui._create_descriptive_link_text(survey_url, 'general')
            self.assertEqual(result, 'Complete Survey')
            
            # Test event registration
            event_url = "https://eventbrite.com/register/event123"
            result = gui._create_descriptive_link_text(event_url, 'event')
            self.assertEqual(result, 'Register')
            
            # Test newsletter unsubscribe
            unsub_url = "https://newsletter.com/unsubscribe/token123"
            result = gui._create_descriptive_link_text(unsub_url, 'newsletter')
            self.assertEqual(result, 'Unsubscribe')
            
            gui.root.destroy()
    
    def test_task_date_formatting(self):
        """Test A7: Task date formatting for single and multi-email tasks"""
        with patch('unified_gui.OutlookManager', return_value=self.mock_outlook), \
             patch('unified_gui.AIProcessor', return_value=self.mock_ai_processor), \
             patch('unified_gui.EmailProcessor', return_value=self.mock_email_processor), \
             patch('unified_gui.EmailAnalyzer', return_value=self.mock_email_analyzer), \
             patch('unified_gui.SummaryGenerator', return_value=self.mock_summary_generator), \
             patch('unified_gui.TaskPersistence', return_value=self.mock_task_persistence):
            
            from unified_gui import UnifiedEmailGUI
            gui = UnifiedEmailGUI()
            gui.root.withdraw()
            
            # Test single email task
            single_task = {
                'received_time': datetime(2025, 1, 15, 10, 30),
                'thread_data': {'thread_count': 1}
            }
            result = gui._format_task_dates(single_task)
            self.assertIn('January 15, 2025', result)
            self.assertIn('10:30', result)
            
            # Test multi-email task with same day
            multi_task_same_day = {
                'thread_data': {
                    'thread_count': 3,
                    'all_emails_data': [
                        {'received_time': datetime(2025, 1, 15, 9, 0)},
                        {'received_time': datetime(2025, 1, 15, 11, 0)},
                        {'received_time': datetime(2025, 1, 15, 14, 0)}
                    ]
                }
            }
            result = gui._format_task_dates(multi_task_same_day)
            self.assertEqual(result, 'Jan 15, 2025')
            
            # Test multi-email task with date range
            multi_task_range = {
                'thread_data': {
                    'thread_count': 2,
                    'all_emails_data': [
                        {'received_time': datetime(2025, 1, 10, 9, 0)},
                        {'received_time': datetime(2025, 1, 15, 11, 0)}
                    ]
                }
            }
            result = gui._format_task_dates(multi_task_range)
            self.assertEqual(result, 'Jan 10–15, 2025')
            
            gui.root.destroy()
    
    def test_outlook_email_opening(self):
        """Test A1: Email opening in Outlook functionality"""
        with patch('unified_gui.OutlookManager', return_value=self.mock_outlook), \
             patch('unified_gui.AIProcessor', return_value=self.mock_ai_processor), \
             patch('unified_gui.EmailProcessor', return_value=self.mock_email_processor), \
             patch('unified_gui.EmailAnalyzer', return_value=self.mock_email_analyzer), \
             patch('unified_gui.SummaryGenerator', return_value=self.mock_summary_generator), \
             patch('unified_gui.TaskPersistence', return_value=self.mock_task_persistence):
            
            from unified_gui import UnifiedEmailGUI
            gui = UnifiedEmailGUI()
            gui.root.withdraw()
            
            # Mock Outlook manager
            gui.outlook_manager.outlook = Mock()
            gui.outlook_manager.namespace = Mock()
            
            # Test email data
            test_email_data = {
                'entry_id': 'test_entry_123',
                'subject': 'Test Email Subject',
                'sender': 'test@example.com'
            }
            
            # Mock the GetItemFromID method
            mock_email_item = Mock()
            gui.outlook_manager.namespace.GetItemFromID.return_value = mock_email_item
            
            # Test opening email in Outlook
            gui.open_email_in_browser(test_email_data)
            
            # Verify Outlook was called
            gui.outlook_manager.namespace.GetItemFromID.assert_called_with('test_entry_123')
            mock_email_item.Display.assert_called_once()
            
            gui.root.destroy()
    
    def test_email_processing_with_other_option(self):
        """Test A3: Email processing handles 'other' option correctly"""
        with patch('unified_gui.OutlookManager', return_value=self.mock_outlook), \
             patch('unified_gui.AIProcessor', return_value=self.mock_ai_processor), \
             patch('unified_gui.EmailProcessor', return_value=self.mock_email_processor), \
             patch('unified_gui.EmailAnalyzer', return_value=self.mock_email_analyzer), \
             patch('unified_gui.SummaryGenerator', return_value=self.mock_summary_generator), \
             patch('unified_gui.TaskPersistence', return_value=self.mock_task_persistence):
            
            from unified_gui import UnifiedEmailGUI
            gui = UnifiedEmailGUI()
            gui.root.withdraw()
            
            # Test with "other" selected and valid custom count
            gui.email_count_var.set("other")
            gui.custom_count_entry.insert(0, "150")
            
            # Mock the processing methods to avoid actual email processing
            with patch.object(gui, 'process_emails_background') as mock_process:
                gui.start_email_processing()
                # Should not show warning and should call processing
                self.assertTrue(mock_process.called)
            
            # Test with "other" selected but no custom count
            gui.custom_count_entry.delete(0, 'end')
            with patch('tkinter.messagebox.showwarning') as mock_warning:
                gui.start_email_processing()
                mock_warning.assert_called_once()
            
            gui.root.destroy()

class TestColumnSorting(unittest.TestCase):
    """Test column sorting functionality (A2)"""
    
    def setUp(self):
        """Setup test environment"""
        self.mock_outlook = Mock()
        self.mock_ai_processor = Mock()
        self.mock_email_processor = Mock()
        self.mock_email_analyzer = Mock()
        self.mock_summary_generator = Mock()
        self.mock_task_persistence = Mock()
        
        # Configure mocks
        self.mock_ai_processor.azure_config = {'endpoint': 'test', 'key': 'test'}
        self.mock_email_processor.get_action_items_data.return_value = {}
    
    def test_column_sorting_visual_indicators(self):
        """Test that column sorting shows visual indicators (↑/↓)"""
        with patch('unified_gui.OutlookManager', return_value=self.mock_outlook), \
             patch('unified_gui.AIProcessor', return_value=self.mock_ai_processor), \
             patch('unified_gui.EmailProcessor', return_value=self.mock_email_processor), \
             patch('unified_gui.EmailAnalyzer', return_value=self.mock_email_analyzer), \
             patch('unified_gui.SummaryGenerator', return_value=self.mock_summary_generator), \
             patch('unified_gui.TaskPersistence', return_value=self.mock_task_persistence):
            
            from unified_gui import UnifiedEmailGUI
            gui = UnifiedEmailGUI()
            gui.root.withdraw()
            
            # Add test email suggestions
            gui.email_suggestions = [
                {
                    'email_data': {
                        'subject': 'Test Email A',
                        'sender_name': 'Alice',
                        'received_time': datetime(2025, 1, 10)
                    },
                    'ai_suggestion': 'required_personal_action',
                    'ai_summary': 'Test summary A'
                },
                {
                    'email_data': {
                        'subject': 'Test Email B',
                        'sender_name': 'Bob',
                        'received_time': datetime(2025, 1, 15)
                    },
                    'ai_suggestion': 'fyi',
                    'ai_summary': 'Test summary B'
                }
            ]
            
            # Test sorting by Subject
            gui.sort_by_column('Subject')
            
            # Check that sort direction is indicated in header
            subject_heading = gui.email_tree.heading('Subject')['text']
            self.assertIn('↑', subject_heading)
            
            # Test reverse sorting
            gui.sort_by_column('Subject')  # Click again to reverse
            subject_heading = gui.email_tree.heading('Subject')['text']
            self.assertIn('↓', subject_heading)
            
            # Test sorting different column clears previous indicators
            gui.sort_by_column('From')
            subject_heading = gui.email_tree.heading('Subject')['text']
            self.assertNotIn('↑', subject_heading)
            self.assertNotIn('↓', subject_heading)
            
            from_heading = gui.email_tree.heading('From')['text']
            self.assertIn('↑', from_heading)
            
            gui.root.destroy()

def run_tests():
    """Run all frontend improvement tests"""
    print("🧪 Running Frontend Improvement Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestFrontendImprovements))
    suite.addTest(unittest.makeSuite(TestColumnSorting))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n📊 Test Results: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
    
    if result.failures:
        print(f"❌ {len(result.failures)} failures")
        for test, trace in result.failures:
            print(f"  - {test}: {trace.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"💥 {len(result.errors)} errors") 
        for test, trace in result.errors:
            print(f"  - {test}: {trace.split('Exception:')[-1].strip()}")
    
    if result.wasSuccessful():
        print("🎉 All tests passed!")
        return True
    else:
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)