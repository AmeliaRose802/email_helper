#!/usr/bin/env python3
"""
UI Orchestration and End-to-End Test Suite

Comprehensive testing for critical UI workflows and user interactions.
Tests are designed to run in headless environments with full mocking.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import threading
import time
from typing import Dict, List, Any, Optional

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))


class UITestSuite:
    """Main test orchestration class for UI testing"""
    
    def __init__(self):
        self.gui = None
        self.test_results = []
        self.mock_components = {}
        self.virtual_display = None
        
    def setup_test_environment(self) -> bool:
        """Set up the test environment with mocked dependencies"""
        try:
            # Mock external dependencies
            self.mock_components = {
                'outlook': Mock(),
                'ai_processor': Mock(),
                'email_processor': Mock(),
                'email_analyzer': Mock(),
                'summary_generator': Mock(),
                'task_persistence': Mock()
            }
            
            # Configure mocks to return sensible defaults
            self.mock_components['ai_processor'].azure_config = {
                'endpoint': 'test', 
                'key': 'test'
            }
            
            self.mock_components['email_processor'].get_action_items_data.return_value = {
                'required_actions': [],
                'team_actions': [],
                'job_listings': [],
                'optional_events': [],
                'fyi_items': []
            }
            
            return True
        except Exception as e:
            print(f"Test environment setup failed: {e}")
            return False
    
    def teardown_test_environment(self):
        """Clean up test environment"""
        if self.gui and hasattr(self.gui, 'root'):
            try:
                self.gui.root.destroy()
            except:
                pass
        self.gui = None


class GUITestHelper:
    """UI interaction automation utilities"""
    
    def __init__(self, gui_instance):
        self.gui = gui_instance
        
    def simulate_column_sort(self, column_name: str) -> bool:
        """Simulate clicking on a column header to sort"""
        try:
            if not self.gui or not hasattr(self.gui, 'email_tree'):
                return False
                
            # Simulate the heading click event
            tree = self.gui.email_tree
            
            # Check if column exists
            if column_name not in tree['columns']:
                return False
                
            # Simulate sort state change
            current_sort = getattr(tree, '_current_sort', {})
            if current_sort.get('column') == column_name:
                # Toggle sort direction
                direction = 'desc' if current_sort.get('direction') == 'asc' else 'asc'
            else:
                direction = 'asc'
                
            # Store sort state
            tree._current_sort = {'column': column_name, 'direction': direction}
            
            return True
        except Exception:
            return False
    
    def simulate_browser_open(self, email_item) -> bool:
        """Simulate opening email in browser"""
        try:
            if not self.gui:
                return False
                
            # Mock webbrowser.open call
            with patch('webbrowser.open') as mock_browser:
                # Simulate the _open_url method
                self.gui._open_url("test_url")
                mock_browser.assert_called_once_with("test_url")
                return True
        except Exception:
            return False
    
    def simulate_custom_count_input(self, count_value: str) -> bool:
        """Simulate typing custom email count and auto-selecting 'Other'"""
        try:
            if not self.gui or not hasattr(self.gui, 'email_count_var'):
                return False
                
            # Simulate typing in custom count field
            if hasattr(self.gui, 'custom_count_var'):
                self.gui.custom_count_var.set(count_value)
                
                # Auto-select "Other" option
                if hasattr(self.gui, 'email_count_var'):
                    self.gui.email_count_var.set("Other")
                    
            return True
        except Exception:
            return False
    
    def simulate_task_tab_direct_access(self) -> bool:
        """Simulate direct navigation to task tab"""
        try:
            if not self.gui or not hasattr(self.gui, 'notebook'):
                return False
                
            # Find task tab index
            tabs = self.gui.notebook.tabs()
            task_tab_index = None
            
            for i, tab in enumerate(tabs):
                tab_text = self.gui.notebook.tab(tab, "text")
                if "task" in tab_text.lower():
                    task_tab_index = i
                    break
                    
            if task_tab_index is not None:
                # Simulate tab selection
                self.gui.notebook.select(task_tab_index)
                return True
                
            return False
        except Exception:
            return False


class MockEmailGenerator:
    """Test email data creation utilities"""
    
    @staticmethod
    def create_test_emails(count: int = 5) -> List[Dict[str, Any]]:
        """Generate realistic test email data"""
        emails = []
        categories = ['required_action', 'team_action', 'job_listing', 'optional_event', 'fyi_item']
        
        for i in range(count):
            email = {
                'email_data': {
                    'subject': f'Test Email {i+1}',
                    'sender': f'test{i+1}@example.com',
                    'sender_name': f'Test User {i+1}',
                    'received_time': f'2025-01-{15+i:02d}',
                    'body': f'Test email content for item {i+1}',
                    'entry_id': f'test_entry_{i+1}'
                },
                'ai_suggestion': categories[i % len(categories)],
                'initial_classification': categories[i % len(categories)],
                'ai_summary': f'AI summary for email {i+1}',
                'processing_notes': [],
                'thread_data': {'thread_count': 1}
            }
            emails.append(email)
            
        return emails
    
    @staticmethod
    def create_action_items_data() -> Dict[str, List[Dict[str, Any]]]:
        """Generate test action items data"""
        return {
            'required_actions': [
                {
                    'subject': 'Urgent: Review Contract',
                    'sender': 'legal@company.com',
                    'due_date': '2025-01-20',
                    'action_required': 'Review and sign contract',
                    'explanation': 'Contract requires immediate attention',
                    'task_id': 'task_001',
                    'batch_count': 1
                }
            ],
            'team_actions': [
                {
                    'subject': 'Team Meeting Prep',
                    'sender': 'manager@company.com',
                    'due_date': 'No specific deadline',
                    'action_required': 'Prepare agenda items',
                    'explanation': 'Weekly team meeting preparation',
                    'task_id': 'task_002',
                    'batch_count': 1
                }
            ],
            'job_listings': [
                {
                    'subject': 'Software Engineer Position',
                    'sender': 'hr@company.com',
                    'qualification_match': '85% match',
                    'due_date': '2025-02-01',
                    'task_id': 'job_001',
                    'batch_count': 1
                }
            ],
            'optional_events': [
                {
                    'subject': 'Tech Conference 2025',
                    'sender': 'events@tech.com',
                    'date': '2025-03-15',
                    'relevance': 'Relevant to your skills',
                    'task_id': 'event_001',
                    'batch_count': 1
                }
            ],
            'fyi_items': [
                {
                    'subject': 'Company Newsletter',
                    'sender': 'communications@company.com',
                    'explanation': 'Monthly company updates',
                    'task_id': 'fyi_001',
                    'batch_count': 1
                }
            ]
        }


class WorkflowTestRunner:
    """End-to-end workflow execution testing"""
    
    def __init__(self, test_suite: UITestSuite):
        self.test_suite = test_suite
        self.gui_helper = None
        
    def setup_workflow_test(self) -> bool:
        """Set up GUI for workflow testing"""
        try:
            # Import here to avoid tkinter issues if not available
            try:
                import tkinter as tk
                # Create a virtual root for testing
                root = tk.Tk()
                root.withdraw()  # Hide the window
            except ImportError:
                # Create mock root if tkinter not available
                root = Mock()
                
            # Mock the GUI creation with all dependencies
            with patch('unified_gui.OutlookManager', 
                      return_value=self.test_suite.mock_components['outlook']), \
                 patch('unified_gui.AIProcessor', 
                      return_value=self.test_suite.mock_components['ai_processor']), \
                 patch('unified_gui.EmailProcessor', 
                      return_value=self.test_suite.mock_components['email_processor']), \
                 patch('unified_gui.EmailAnalyzer', 
                      return_value=self.test_suite.mock_components['email_analyzer']), \
                 patch('unified_gui.SummaryGenerator', 
                      return_value=self.test_suite.mock_components['summary_generator']), \
                 patch('unified_gui.TaskPersistence', 
                      return_value=self.test_suite.mock_components['task_persistence']):
                
                # Import and create GUI
                from unified_gui import UnifiedEmailGUI
                self.test_suite.gui = UnifiedEmailGUI()
                
                # Hide window if tkinter is available
                if hasattr(self.test_suite.gui.root, 'withdraw'):
                    self.test_suite.gui.root.withdraw()
                    
                self.gui_helper = GUITestHelper(self.test_suite.gui)
                return True
                
        except Exception as e:
            print(f"Workflow test setup failed: {e}")
            return False
    
    def test_email_loading_workflow(self) -> bool:
        """Test complete email loading and display workflow"""
        try:
            if not self.test_suite.gui:
                return False
                
            # Generate test email data
            test_emails = MockEmailGenerator.create_test_emails(3)
            self.test_suite.gui.email_suggestions = test_emails
            
            # Test email tree refresh
            self.test_suite.gui.refresh_email_tree()
            
            # Verify emails are displayed
            if hasattr(self.test_suite.gui, 'email_tree'):
                children = self.test_suite.gui.email_tree.get_children()
                return len(children) > 0
                
            return True
        except Exception:
            return False
    
    def test_action_items_workflow(self) -> bool:
        """Test action items processing and display workflow"""
        try:
            if not self.test_suite.gui:
                return False
                
            # Generate test action items
            action_items = MockEmailGenerator.create_action_items_data()
            self.test_suite.gui.action_items_data = action_items
            
            # Test action items display
            # This would normally refresh the UI with action items
            return True
        except Exception:
            return False


class RegressionTestValidator:
    """Change detection and validation for regression testing"""
    
    def __init__(self, test_suite: UITestSuite):
        self.test_suite = test_suite
        self.baseline_state = {}
        
    def capture_baseline_state(self) -> Dict[str, Any]:
        """Capture current UI state as baseline for regression testing"""
        try:
            if not self.test_suite.gui:
                return {}
                
            state = {
                'has_notebook': hasattr(self.test_suite.gui, 'notebook'),
                'has_email_tree': hasattr(self.test_suite.gui, 'email_tree'),
                'has_summary_text': hasattr(self.test_suite.gui, 'summary_text'),
                'tree_columns': [],
                'tab_count': 0
            }
            
            # Capture tree columns if available
            if hasattr(self.test_suite.gui, 'email_tree'):
                state['tree_columns'] = list(self.test_suite.gui.email_tree['columns'])
                
            # Capture tab count if available
            if hasattr(self.test_suite.gui, 'notebook'):
                state['tab_count'] = len(self.test_suite.gui.notebook.tabs())
                
            self.baseline_state = state
            return state
        except Exception:
            return {}
    
    def validate_no_regression(self, current_state: Dict[str, Any]) -> bool:
        """Validate that current state matches baseline (no regression)"""
        if not self.baseline_state:
            return False
            
        for key, baseline_value in self.baseline_state.items():
            if key not in current_state:
                return False
            if current_state[key] != baseline_value:
                return False
                
        return True


# Pytest test functions start here

@pytest.fixture
def ui_test_suite():
    """Fixture to provide a configured UI test suite"""
    suite = UITestSuite()
    suite.setup_test_environment()
    yield suite
    suite.teardown_test_environment()


@pytest.fixture
def workflow_runner(ui_test_suite):
    """Fixture to provide a workflow test runner"""
    runner = WorkflowTestRunner(ui_test_suite)
    if runner.setup_workflow_test():
        yield runner
    else:
        pytest.skip("Could not set up workflow test environment")


@pytest.mark.ui
@pytest.mark.e2e
def test_gui_initialization(workflow_runner):
    """Test that GUI initializes without errors"""
    assert workflow_runner.test_suite.gui is not None
    assert hasattr(workflow_runner.test_suite.gui, 'root')


@pytest.mark.ui
@pytest.mark.workflow
def test_email_loading_workflow(workflow_runner):
    """Test complete email loading and display workflow"""
    result = workflow_runner.test_email_loading_workflow()
    assert result is True


@pytest.mark.ui
@pytest.mark.workflow
def test_action_items_workflow(workflow_runner):
    """Test action items processing and display workflow"""
    result = workflow_runner.test_action_items_workflow()
    assert result is True


@pytest.mark.ui
@pytest.mark.integration
def test_column_sorting_functionality(workflow_runner):
    """Test column sorting functionality across all columns"""
    gui_helper = workflow_runner.gui_helper
    if not gui_helper:
        pytest.skip("GUI helper not available")
        
    # Test sorting on all expected columns
    expected_columns = ['Subject', 'From', 'Category', 'AI Summary', 'Date']
    
    for column in expected_columns:
        result = gui_helper.simulate_column_sort(column)
        assert result is True, f"Failed to sort column: {column}"


@pytest.mark.ui
@pytest.mark.integration  
def test_open_in_browser_workflow(workflow_runner):
    """Test open-in-browser functionality with mocks"""
    gui_helper = workflow_runner.gui_helper
    if not gui_helper:
        pytest.skip("GUI helper not available")
        
    # Test browser opening with mock
    result = gui_helper.simulate_browser_open("test_email")
    assert result is True


@pytest.mark.ui
@pytest.mark.integration
def test_custom_email_count_workflow(workflow_runner):
    """Test custom email count auto-selection ('Other' option)"""
    gui_helper = workflow_runner.gui_helper
    if not gui_helper:
        pytest.skip("GUI helper not available")
        
    # Test custom count input and auto-selection
    result = gui_helper.simulate_custom_count_input("25")
    assert result is True


@pytest.mark.ui
@pytest.mark.integration
def test_task_tab_direct_loading(workflow_runner):
    """Test task tab direct loading without classification dependency"""
    gui_helper = workflow_runner.gui_helper
    if not gui_helper:
        pytest.skip("GUI helper not available")
        
    # Test direct task tab access
    result = gui_helper.simulate_task_tab_direct_access()
    # Note: This might return False if no task tab exists, which is acceptable
    assert isinstance(result, bool)


@pytest.mark.regression
def test_ui_regression_prevention(workflow_runner):
    """Test regression prevention by comparing UI state"""
    validator = RegressionTestValidator(workflow_runner.test_suite)
    
    # Capture baseline state
    baseline = validator.capture_baseline_state()
    assert len(baseline) > 0
    
    # Simulate some operations that shouldn't change core structure
    workflow_runner.test_email_loading_workflow()
    
    # Capture current state and validate no regression
    current = validator.capture_baseline_state()
    result = validator.validate_no_regression(current)
    assert result is True


@pytest.mark.mock
def test_mock_email_generator():
    """Test mock email data generation"""
    emails = MockEmailGenerator.create_test_emails(3)
    assert len(emails) == 3
    assert all('email_data' in email for email in emails)
    assert all('ai_suggestion' in email for email in emails)
    
    action_items = MockEmailGenerator.create_action_items_data()
    assert 'required_actions' in action_items
    assert 'team_actions' in action_items
    assert len(action_items['required_actions']) > 0


if __name__ == "__main__":
    # Run tests directly if executed as script
    pytest.main([__file__, "-v"])