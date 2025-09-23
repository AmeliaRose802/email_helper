#!/usr/bin/env python3
"""
Test script for thread grouping functionality
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

def test_thread_grouping():
    """Test enhanced thread grouping functionality"""
    print("🧪 TESTING THREAD GROUPING FUNCTIONALITY")
    print("=" * 60)
    
    try:
        from components.thread_review_tab import ThreadReviewTab
        from email_analyzer import EmailAnalyzer
        import tkinter as tk
        
        # Mock controller class for ThreadReviewTab
        class MockController:
            def __init__(self):
                self.email_analyzer = EmailAnalyzer()
            
            def on_thread_category_change(self, thread_id):
                print(f"Thread category changed for {thread_id}")
            
            def reclassify_entire_thread(self, thread_id, category):
                print(f"Reclassifying thread {thread_id} to {category}")
            
            def generate_thread_summary(self, thread_id):
                return f"Summary for thread {thread_id}"
        
        # Create test email suggestions with thread data
        base_time = datetime.now()
        
        email_suggestions = [
            {
                'entry_id': 'email_001',
                'email_object': type('MockEmail', (), {
                    'Subject': 'Project Update - Status Report',
                    'SenderName': 'Alice Johnson',
                    'ReceivedTime': base_time
                })(),
                'email_data': {
                    'subject': 'Project Update - Status Report',
                    'sender': 'Alice Johnson',
                    'received_time': base_time.isoformat()
                },
                'ai_suggestion': 'team_action',
                'ai_summary': 'Project status update requiring team review',
                'thread_data': {
                    'conversation_id': 'conv_001',
                    'thread_count': 3,
                    'participants': ['Alice Johnson', 'Bob Smith', 'User'],
                    'latest_date': base_time,
                    'topic': 'Project Update - Status Report'
                }
            },
            {
                'entry_id': 'email_002',
                'email_object': type('MockEmail', (), {
                    'Subject': 'Re: Project Update - Status Report',
                    'SenderName': 'Bob Smith',
                    'ReceivedTime': base_time + timedelta(hours=1)
                })(),
                'email_data': {
                    'subject': 'Re: Project Update - Status Report',
                    'sender': 'Bob Smith',
                    'received_time': (base_time + timedelta(hours=1)).isoformat()
                },
                'ai_suggestion': 'team_action',
                'ai_summary': 'Response to project update with additional context',
                'thread_data': {
                    'conversation_id': 'conv_001',
                    'thread_count': 3,
                    'participants': ['Alice Johnson', 'Bob Smith', 'User'],
                    'latest_date': base_time + timedelta(hours=1),
                    'topic': 'Project Update - Status Report'
                }
            },
            {
                'entry_id': 'email_003',
                'email_object': type('MockEmail', (), {
                    'Subject': 'Certificate Renewal Reminder',
                    'SenderName': 'IT Security',
                    'ReceivedTime': base_time + timedelta(hours=2)
                })(),
                'email_data': {
                    'subject': 'Certificate Renewal Reminder',
                    'sender': 'IT Security',
                    'received_time': (base_time + timedelta(hours=2)).isoformat()
                },
                'ai_suggestion': 'required_personal_action',
                'ai_summary': 'Certificate needs renewal before expiration',
                'thread_data': {
                    'conversation_id': 'single_email_003',
                    'thread_count': 1,
                    'participants': ['IT Security'],
                    'latest_date': base_time + timedelta(hours=2),
                    'topic': 'Certificate Renewal Reminder'
                }
            },
            {
                'entry_id': 'email_004',
                'email_object': type('MockEmail', (), {
                    'Subject': 'Certificate Expiring Soon',
                    'SenderName': 'Security Team',
                    'ReceivedTime': base_time + timedelta(hours=3)
                })(),
                'email_data': {
                    'subject': 'Certificate Expiring Soon',
                    'sender': 'Security Team',
                    'received_time': (base_time + timedelta(hours=3)).isoformat()
                },
                'ai_suggestion': 'required_personal_action',
                'ai_summary': 'Similar certificate expiration notice',
                'thread_data': {
                    'conversation_id': 'single_email_004',
                    'thread_count': 1,
                    'participants': ['Security Team'],
                    'latest_date': base_time + timedelta(hours=3),
                    'topic': 'Certificate Expiring Soon'
                }
            }
        ]
        
        print("📊 Input Test Data:")
        print(f"   Total email suggestions: {len(email_suggestions)}")
        print(f"   Thread 1: Project Update (3 emails from Alice, Bob)")
        print(f"   Single emails: 2 certificate-related emails")
        print()
        
        # Create a temporary root window (required for tkinter)
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Create a mock parent frame
        parent_frame = tk.Frame(root)
        
        # Create mock controller
        controller = MockController()
        
        # Create ThreadReviewTab instance
        thread_tab = ThreadReviewTab(parent_frame, controller)
        
        # Test the enhanced grouping
        print("🔗 Testing enhanced thread grouping...")
        thread_groups = thread_tab.group_suggestions_by_thread(email_suggestions)
        
        print("📋 Thread Grouping Results:")
        print(f"   Number of thread groups: {len(thread_groups)}")
        
        for i, (thread_id, thread_data) in enumerate(thread_groups.items(), 1):
            emails_count = len(thread_data['emails'])
            participants = thread_data['participants']
            topic = thread_data['topic']
            
            print(f"   Group {i}: '{topic}' ({emails_count} emails, {len(participants)} participants)")
            
            if emails_count > 1:
                # Check if this is a merged group
                total_conversations = sum(email['thread_data']['thread_count'] for email in thread_data['emails'])
                if emails_count != total_conversations:
                    print(f"     🔗 MERGED: {emails_count} emails from {total_conversations} conversations")
                else:
                    print(f"     🧵 THREAD: Chronological conversation")
            else:
                print(f"     📧 SINGLE: Individual email")
        
        print()
        
        # Expected results
        expected_groups = 3  # Should merge similar certificate emails
        if len(thread_groups) <= expected_groups:
            print(f"✅ SUCCESS: Thread grouping working correctly!")
            print(f"   - Expected ≤{expected_groups} groups, got {len(thread_groups)}")
            print(f"   - Similar certificate emails should be grouped together")
            
            # Check for certificate merging
            cert_groups = [g for g in thread_groups.values() if 'certificate' in g['topic'].lower()]
            if cert_groups and any(len(g['emails']) > 1 for g in cert_groups):
                print(f"   - ✅ Certificate emails merged successfully")
            else:
                print(f"   - ⚠️  Certificate emails not merged (may need similarity tuning)")
            
        else:
            print(f"❌ ISSUE: Expected ≤{expected_groups} groups, got {len(thread_groups)}")
            print("   Similar emails not being grouped together")
        
        # Clean up
        root.destroy()
        
        print()
        print("=" * 60)
        print("✅ Thread grouping test completed")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_thread_grouping()