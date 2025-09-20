#!/usr/bin/env python3
"""
Test script for accordion view functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import tkinter as tk
from tkinter import ttk
from components.thread_review_tab import ThreadReviewTab
from datetime import datetime

def test_accordion_view():
    """Test the accordion view with mock data"""
    
    # Create test window
    root = tk.Tk()
    root.title("Accordion View Test")
    root.geometry("800x600")
    
    # Create a mock controller
    class MockController:
        def apply_to_outlook(self):
            print("Mock: Apply to Outlook called")
            
        def proceed_to_summary(self):
            print("Mock: Proceed to summary called")
            
        def on_thread_category_change(self, thread_id):
            print(f"Mock: Thread category change called for {thread_id}")
            
        def reclassify_entire_thread(self, thread_id, category):
            print(f"Mock: Reclassify thread {thread_id} to {category}")
            return True
            
        def generate_thread_summary(self, thread_id):
            print(f"Mock: Generate summary for thread {thread_id}")
            return f"Mock summary for thread {thread_id}"
    
    # Create thread review tab
    controller = MockController()
    thread_review_tab = ThreadReviewTab(root, controller)
    
    # Create mock email suggestions data
    mock_suggestions = [
        {
            'ai_suggestion': 'fyi',
            'ai_summary': 'This is a test FYI email about system maintenance.',
            'email_data': {
                'subject': 'System Maintenance Notification',
                'sender_name': 'IT Admin',
                'received_time': datetime.now()
            },
            'thread_data': {
                'conversation_id': 'thread_1',
                'topic': 'System Maintenance Thread',
                'participants': ['IT Admin', 'User'],
                'thread_count': 2,
                'has_complete_thread': True,
                'latest_date': datetime.now()
            }
        },
        {
            'ai_suggestion': 'fyi',
            'ai_summary': 'Follow-up on the system maintenance.',
            'email_data': {
                'subject': 'RE: System Maintenance Notification',
                'sender_name': 'User',
                'received_time': datetime.now()
            },
            'thread_data': {
                'conversation_id': 'thread_1',
                'topic': 'System Maintenance Thread',
                'participants': ['IT Admin', 'User'],
                'thread_count': 2,
                'has_complete_thread': True,
                'latest_date': datetime.now()
            }
        },
        {
            'ai_suggestion': 'team_action',
            'ai_summary': 'Action required for project approval.',
            'email_data': {
                'subject': 'Project Approval Required',
                'sender_name': 'Manager',
                'received_time': datetime.now()
            },
            'thread_data': {
                'conversation_id': 'single_email_1',
                'topic': 'Project Approval Required',
                'participants': ['Manager'],
                'thread_count': 1,
                'has_complete_thread': False,
                'latest_date': datetime.now()
            }
        }
    ]
    
    # Populate threads
    print("Populating threads with mock data...")
    thread_review_tab.populate_threads(mock_suggestions)
    
    print("✅ Accordion view test ready!")
    print("Instructions:")
    print("1. You should see thread headers")
    print("2. Click the ▶ button to expand threads")
    print("3. Check if email content appears when expanded")
    
    # Run the test
    root.mainloop()

if __name__ == "__main__":
    print("🧪 Accordion View Test")
    print("=" * 30)
    
    try:
        test_accordion_view()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
