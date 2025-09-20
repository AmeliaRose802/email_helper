#!/usr/bin/env python3
"""
Quick UI Integration Tests
Fast automated tests for key UI functionality
"""

import sys
import os
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import threading
import time

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

class QuickUITests:
    """Quick automated UI tests that run fast"""
    
    def __init__(self):
        self.root = None
        self.gui = None
        
    def setup_mocks(self):
        """Setup mocked dependencies"""
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
        
    def test_gui_creation(self):
        """Test GUI can be created without crashing"""
        print("🧪 Testing GUI Creation...")
        
        try:
            # Mock all dependencies
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
                
                # Verify basic components exist
                assert hasattr(self.gui, 'notebook'), "Main notebook missing"
                assert hasattr(self.gui, 'root'), "Root window missing"
                assert hasattr(self.gui, 'email_tree'), "Email tree missing"
                assert hasattr(self.gui, 'summary_text'), "Summary text missing"
                
                print("   ✅ GUI created successfully")
                print("   ✅ All main components present")
                return True
                
        except Exception as e:
            print(f"   ❌ GUI creation failed: {e}")
            return False
    
    def test_summary_rendering(self):
        """Test summary can be rendered without errors"""
        print("\n🧪 Testing Summary Rendering...")
        
        if not self.gui:
            print("   ❌ GUI not available")
            return False
            
        try:
            # Create test email suggestions data in the actual format
            self.gui.email_suggestions = [
                {
                    'email_data': {
                        'subject': 'Test Task',
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
            
            # Test refreshing the email tree (the actual display method)
            self.gui.refresh_email_tree()
            
            # Verify tree was populated
            children = self.gui.email_tree.get_children()
            assert len(children) > 0, "No emails displayed in tree"
            
            print("   ✅ Email data rendered in tree view")
            print("   ✅ Tree populated correctly")
            return True
            
        except Exception as e:
            print(f"   ❌ Summary rendering failed: {e}")
            return False
    
    def test_due_date_handling(self):
        """Test that due_date fields are handled safely"""
        print("\n🧪 Testing Due Date Handling...")
        
        if not self.gui:
            print("   ❌ GUI not available")
            return False
            
        try:
            # Test email data without due_date fields (realistic scenario)
            self.gui.email_suggestions = [
                {
                    'email_data': {
                        'subject': 'Task Without Due Date',
                        'sender': 'test@example.com',
                        'sender_name': 'Test User',
                        'received_time': '2025-01-11',
                        'body': 'Test email without due date'
                        # Note: no 'due_date' field
                    },
                    'ai_suggestion': 'required_action',
                    'initial_classification': 'required_action',
                    'ai_summary': 'Test action without due date',
                    'processing_notes': [],
                    'thread_data': {'thread_count': 1}
                }
            ]
            
            # This should NOT crash with KeyError when refreshing tree
            self.gui.refresh_email_tree()
            
            # Verify tree was populated despite missing due_date
            children = self.gui.email_tree.get_children()
            assert len(children) > 0, "No emails with missing due_date"
            
            # Test selecting an email (which triggers detail display)
            if children:
                # Simulate selecting first email
                self.gui.email_tree.selection_set(children[0])
                self.gui.display_email_details(0)
            
            print("   ✅ Missing due_date handled gracefully")
            print("   ✅ Email display works without due_date")
            return True
            
        except Exception as e:
            print(f"   ❌ Due date handling failed: {e}")
            return False
    
    def test_widget_responsiveness(self):
        """Test that widgets respond to basic operations"""
        print("\n🧪 Testing Widget Responsiveness...")
        
        if not self.gui:
            print("   ❌ GUI not available")
            return False
            
        try:
            # Clear any existing tree items first
            for item in self.gui.email_tree.get_children():
                self.gui.email_tree.delete(item)
            
            # Test text widget operations - enable editing first
            self.gui.summary_text.config(state=tk.NORMAL)
            self.gui.summary_text.insert(tk.END, "Test content")
            content = self.gui.summary_text.get("1.0", tk.END)
            assert "Test content" in content, "Text insertion failed"
            
            self.gui.summary_text.delete("1.0", tk.END)
            content = self.gui.summary_text.get("1.0", tk.END)
            assert len(content.strip()) == 0, "Text deletion failed"
            
            # Test tree widget operations
            test_item = self.gui.email_tree.insert('', 'end', values=(
                'Test Email', 'test@example.com', 'test_category', 'Test summary', '2025-09-15'
            ))
            children = self.gui.email_tree.get_children()
            assert len(children) > 0, "Tree insertion failed"
            
            self.gui.email_tree.delete(test_item)
            children = self.gui.email_tree.get_children()
            assert len(children) == 0, "Tree deletion failed"
            
            print("   ✅ Text widget operations work")
            print("   ✅ Tree widget operations work")
            return True
            
        except Exception as e:
            print(f"   ❌ Widget responsiveness test failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up test resources"""
        if self.gui and hasattr(self.gui, 'root'):
            try:
                self.gui.root.destroy()
            except:
                pass
        elif self.root:
            try:
                self.root.destroy()
            except:
                pass
    
    def run_quick_tests(self):
        """Run all quick UI tests"""
        print("⚡ RUNNING QUICK UI TESTS")
        print("=" * 50)
        
        self.setup_mocks()
        
        tests = [
            self.test_gui_creation,
            self.test_summary_rendering,
            self.test_due_date_handling,
            self.test_widget_responsiveness
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"   ❌ Test crashed: {e}")
        
        self.cleanup()
        
        print(f"\n📊 QUICK TEST RESULTS: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 ALL QUICK TESTS PASSED!")
            print("✅ UI is working correctly")
            return True
        else:
            print(f"⚠️  {total - passed} tests failed")
            return False

def main():
    """Run quick UI tests"""
    tester = QuickUITests()
    success = tester.run_quick_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()