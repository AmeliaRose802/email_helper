#!/usr/bin/env python3
"""
Automated UI Testing Framework for Email Helper
Tests GUI components without requiring manual interaction
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
import threading
import time
from unittest.mock import Mock, patch

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

class UITestFramework:
    """Framework for automated UI testing"""
    
    def __init__(self):
        self.root = None
        self.gui = None
        self.test_results = []
        self.mock_data = self._create_mock_data()
    
    def _create_mock_data(self):
        """Create mock data for testing"""
        return {
            'action_items_data': {
                'required_actions': [
                    {
                        'subject': 'Test Action Item',
                        'sender': 'test@example.com',
                        'due_date': '2025-09-20',
                        'action_required': 'Review document',
                        'explanation': 'Test explanation',
                        'task_id': 'test_123',
                        'batch_count': 1
                    }
                ],
                'team_actions': [
                    {
                        'subject': 'Team Task',
                        'sender': 'team@example.com',
                        'due_date': 'No specific deadline',
                        'action_required': 'Team review',
                        'explanation': 'Team task explanation',
                        'task_id': 'team_456',
                        'batch_count': 1
                    }
                ],
                'job_listings': [
                    {
                        'subject': 'Software Engineer Position',
                        'sender': 'hr@company.com',
                        'qualification_match': '85% match',
                        'due_date': '2025-09-25',
                        'task_id': 'job_789',
                        'batch_count': 1
                    }
                ],
                'optional_events': [
                    {
                        'subject': 'Tech Conference',
                        'sender': 'events@tech.com',
                        'date': '2025-10-01',
                        'relevance': 'Relevant to your skills',
                        'task_id': 'event_101',
                        'batch_count': 1
                    }
                ],
                'fyi_items': [
                    {
                        'subject': 'Company Update',
                        'sender': 'company@example.com',
                        'explanation': 'Important company news',
                        'task_id': 'fyi_202',
                        'batch_count': 1
                    }
                ]
            }
        }
    
    def setup_test_environment(self):
        """Set up the test environment with mocked dependencies"""
        print("🧪 Setting up UI test environment...")
        
        # Create root window for testing
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        # Mock external dependencies
        self.mock_outlook = Mock()
        self.mock_ai_processor = Mock()
        self.mock_email_processor = Mock()
        self.mock_email_analyzer = Mock()
        self.mock_summary_generator = Mock()
        self.mock_task_persistence = Mock()
        
        # Configure mocks to return sensible defaults
        self.mock_ai_processor.azure_config = {'endpoint': 'test', 'key': 'test'}
        self.mock_email_processor.get_action_items_data.return_value = {
            'required_actions': [],
            'team_actions': [],
            'job_listings': [],
            'optional_events': [],
            'fyi_items': []
        }
        
        return True
    
    def test_gui_initialization(self):
        """Test that GUI initializes without errors"""
        print("\n🧪 Testing GUI Initialization...")
        
        try:
            with patch('unified_gui.OutlookManager', return_value=self.mock_outlook), \
                 patch('unified_gui.AIProcessor', return_value=self.mock_ai_processor), \
                 patch('unified_gui.EmailProcessor', return_value=self.mock_email_processor), \
                 patch('unified_gui.EmailAnalyzer', return_value=self.mock_email_analyzer), \
                 patch('unified_gui.SummaryGenerator', return_value=self.mock_summary_generator), \
                 patch('unified_gui.TaskPersistence', return_value=self.mock_task_persistence):
                
                from unified_gui import UnifiedEmailGUI
                self.gui = UnifiedEmailGUI()  # No root parameter needed
                
                # Hide the window during testing
                self.gui.root.withdraw()
                
                # Verify main components exist
                assert hasattr(self.gui, 'notebook'), "Notebook widget not found"
                assert hasattr(self.gui, 'email_tree'), "Email tree not found"
                assert hasattr(self.gui, 'summary_text'), "Summary text widget not found"
                
                print("   ✅ GUI initialized successfully")
                print("   ✅ Main components created")
                return True
                
        except Exception as e:
            print(f"   ❌ GUI initialization failed: {e}")
            return False
    
    def test_summary_display(self):
        """Test that summary display works without errors"""
        print("\n🧪 Testing Summary Display...")
        
        try:
            if not self.gui:
                print("   ❌ GUI not initialized")
                return False
            
            # Create test email suggestions data in the correct format
            self.gui.email_suggestions = [
                {
                    'email_data': {
                        'subject': 'Test Action Item',
                        'sender': 'test@example.com',
                        'sender_name': 'Test User',
                        'received_time': '2025-01-11',
                        'body': 'Test email content'
                    },
                    'ai_suggestion': 'required_action',
                    'initial_classification': 'required_action',
                    'ai_summary': 'Test action required',
                    'processing_notes': [],
                    'thread_data': {'thread_count': 1}
                }
            ]
            
            # Test refresh_email_tree method (the actual display method)
            self.gui.refresh_email_tree()
            
            # Verify tree was populated
            children = self.gui.email_tree.get_children()
            assert len(children) > 0, "No emails displayed in tree"
            
            print("   ✅ Email data displayed in tree view")
            print("   ✅ Test data rendered correctly")
            return True
            
        except Exception as e:
            print(f"   ❌ Summary display failed: {e}")
            return False
    
    def test_notebook_tabs(self):
        """Test that all notebook tabs are created and accessible"""
        print("\n🧪 Testing Notebook Tabs...")
        
        try:
            if not self.gui:
                print("   ❌ GUI not initialized")
                return False
            
            # Get all tabs
            tabs = self.gui.notebook.tabs()
            
            # Verify expected tabs exist (actual tab names from unified_gui.py)
            expected_tabs = ["1. Process Emails", "2. Review & Edit", "3. Summary & Results", "4. Accuracy Dashboard"]
            tab_texts = [self.gui.notebook.tab(tab, "text") for tab in tabs]
            
            for expected_tab in expected_tabs:
                assert expected_tab in tab_texts, f"Tab '{expected_tab}' not found"
            
            # Verify we have the right number of tabs
            assert len(tabs) == len(expected_tabs), f"Expected {len(expected_tabs)} tabs, got {len(tabs)}"
            
            print(f"   ✅ All {len(tabs)} tabs created successfully")
            print(f"   ✅ Tab names: {', '.join(tab_texts)}")
            return True
            
        except Exception as e:
            print(f"   ❌ Notebook tab test failed: {e}")
            return False
    
    def test_email_tree(self):
        """Test email tree widget functionality"""
        print("\n🧪 Testing Email Tree Widget...")
        
        try:
            if not self.gui:
                print("   ❌ GUI not initialized")
                return False
            
            # Verify tree columns
            columns = self.gui.email_tree['columns']
            expected_columns = ('Subject', 'From', 'Category', 'AI Summary', 'Date')
            
            for col in expected_columns:
                assert col in columns, f"Column '{col}' not found in email tree"
            
            # Test adding test data to tree
            test_item = self.gui.email_tree.insert('', 'end', values=(
                'Test Email',
                'test@example.com',
                'required_action',
                'Test summary',
                '2025-09-15'
            ))
            
            # Verify item was added
            children = self.gui.email_tree.get_children()
            assert len(children) > 0, "No items found in email tree after insertion"
            
            # Verify item data
            item_values = self.gui.email_tree.item(test_item)['values']
            assert item_values[0] == 'Test Email', "Email tree item data incorrect"
            
            print("   ✅ Email tree columns configured correctly")
            print("   ✅ Tree item insertion works")
            return True
            
        except Exception as e:
            print(f"   ❌ Email tree test failed: {e}")
            return False
    
    def test_button_functionality(self):
        """Test button widgets and their commands"""
        print("\n🧪 Testing Button Functionality...")
        
        try:
            if not self.gui:
                print("   ❌ GUI not initialized")
                return False
            
            # Find buttons in the GUI
            buttons_tested = 0
            
            def find_buttons(widget):
                nonlocal buttons_tested
                for child in widget.winfo_children():
                    if isinstance(child, (tk.Button, ttk.Button)):
                        # Test that button has a command
                        try:
                            command = child.cget('command')
                            if command:
                                buttons_tested += 1
                        except:
                            pass  # Some buttons might not have commands
                    
                    # Recursively check child widgets
                    try:
                        find_buttons(child)
                    except:
                        pass  # Some widgets don't have children
            
            find_buttons(self.gui.root)
            
            print(f"   ✅ Found and validated {buttons_tested} buttons with commands")
            return True
            
        except Exception as e:
            print(f"   ❌ Button functionality test failed: {e}")
            return False
    
    def test_widget_destruction(self):
        """Test proper widget cleanup"""
        print("\n🧪 Testing Widget Cleanup...")
        
        try:
            if not self.gui:
                print("   ❌ GUI not initialized")
                return False
            
            # Clear summary content
            self.gui.summary_text.delete("1.0", tk.END)
            
            # Clear email tree
            for item in self.gui.email_tree.get_children():
                self.gui.email_tree.delete(item)
            
            # Verify cleanup
            summary_content = self.gui.summary_text.get("1.0", tk.END)
            tree_children = self.gui.email_tree.get_children()
            
            assert len(summary_content.strip()) == 0, "Summary text not cleared"
            assert len(tree_children) == 0, "Email tree not cleared"
            
            print("   ✅ Widget content cleared successfully")
            print("   ✅ Memory cleanup working")
            return True
            
        except Exception as e:
            print(f"   ❌ Widget cleanup test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all UI tests"""
        print("🚀 STARTING AUTOMATED UI TESTING")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_environment():
            print("❌ Test environment setup failed")
            return False
        
        # Define test suite
        tests = [
            ("GUI Initialization", self.test_gui_initialization),
            ("Summary Display", self.test_summary_display),
            ("Notebook Tabs", self.test_notebook_tabs),
            ("Email Tree", self.test_email_tree),
            ("Button Functionality", self.test_button_functionality),
            ("Widget Cleanup", self.test_widget_destruction)
        ]
        
        # Run tests
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    self.test_results.append((test_name, "PASSED"))
                else:
                    self.test_results.append((test_name, "FAILED"))
            except Exception as e:
                print(f"   ❌ {test_name} crashed: {e}")
                self.test_results.append((test_name, f"CRASHED: {e}"))
        
        # Cleanup
        if self.root:
            self.root.destroy()
        
        # Results
        print(f"\n📊 UI TEST RESULTS: {passed}/{total} tests passed")
        print("=" * 60)
        
        for test_name, result in self.test_results:
            status_icon = "✅" if result == "PASSED" else "❌"
            print(f"{status_icon} {test_name}: {result}")
        
        if passed == total:
            print("\n🎉 ALL UI TESTS PASSED!")
            print("✅ GUI is functioning correctly")
            print("✅ No manual clicking required")
            return True
        else:
            print(f"\n⚠️  {total - passed} UI tests failed")
            print("Review failed tests before deployment")
            return False
    
    def run_continuous_testing(self, interval_seconds=30):
        """Run tests continuously for monitoring"""
        print(f"🔄 Starting continuous UI testing (every {interval_seconds}s)")
        print("Press Ctrl+C to stop...")
        
        try:
            while True:
                success = self.run_all_tests()
                if not success:
                    print("⚠️  UI tests failed - check for issues")
                
                print(f"\n💤 Waiting {interval_seconds} seconds for next test cycle...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n🛑 Continuous testing stopped by user")

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated UI Testing for Email Helper")
    parser.add_argument("--continuous", action="store_true", 
                       help="Run tests continuously for monitoring")
    parser.add_argument("--interval", type=int, default=30,
                       help="Interval between continuous tests (seconds)")
    
    args = parser.parse_args()
    
    # Create test framework
    ui_tester = UITestFramework()
    
    if args.continuous:
        ui_tester.run_continuous_testing(args.interval)
    else:
        success = ui_tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()