#!/usr/bin/env python3
"""
Test script for core thread grouping logic (no GUI)
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

def test_core_thread_grouping():
    """Test core thread grouping logic without GUI"""
    print("🧪 TESTING CORE THREAD GROUPING LOGIC")
    print("=" * 60)
    
    try:
        from email_processor import EmailProcessor
        from email_analyzer import EmailAnalyzer
        from ai_processor import AIProcessor
        from summary_generator import SummaryGenerator
        from outlook_manager import OutlookManager
        
        # Create components
        outlook_manager = OutlookManager()
        email_analyzer = EmailAnalyzer()
        ai_processor = AIProcessor(email_analyzer)
        email_analyzer.ai_processor = ai_processor
        summary_generator = SummaryGenerator()
        
        email_processor = EmailProcessor(
            outlook_manager, ai_processor, email_analyzer, summary_generator
        )
        
        # Create test email suggestions with thread data
        base_time = datetime.now()
        
        # Create mock email objects
        class MockEmail:
            def __init__(self, entry_id, subject, sender, received_time):
                self.EntryID = entry_id
                self.Subject = subject
                self.SenderName = sender
                self.ReceivedTime = received_time
                self.Body = f"This is the body of {subject}"
        
        email_suggestions = [
            {
                'entry_id': 'email_001',
                'email_object': MockEmail('email_001', 'Project Update - Status Report', 'Alice Johnson', base_time),
                'ai_suggestion': 'team_action',
                'thread_data': {
                    'conversation_id': 'conv_001',
                    'thread_count': 2,
                    'participants': ['Alice Johnson', 'User'],
                    'latest_date': base_time,
                    'topic': 'Project Update - Status Report'
                }
            },
            {
                'entry_id': 'email_002',
                'email_object': MockEmail('email_002', 'Certificate Renewal Reminder', 'IT Security', base_time + timedelta(hours=1)),
                'ai_suggestion': 'required_personal_action',
                'thread_data': {
                    'conversation_id': 'single_email_002',
                    'thread_count': 1,
                    'participants': ['IT Security'],
                    'latest_date': base_time + timedelta(hours=1),
                    'topic': 'Certificate Renewal Reminder'
                }
            },
            {
                'entry_id': 'email_003',
                'email_object': MockEmail('email_003', 'Certificate Expiring Soon', 'Security Team', base_time + timedelta(hours=2)),
                'ai_suggestion': 'required_personal_action',
                'thread_data': {
                    'conversation_id': 'single_email_003',
                    'thread_count': 1,
                    'participants': ['Security Team'],
                    'latest_date': base_time + timedelta(hours=2),
                    'topic': 'Certificate Expiring Soon'
                }
            },
            {
                'entry_id': 'email_004',
                'email_object': MockEmail('email_004', 'Daily Newsletter', 'Company News', base_time + timedelta(hours=3)),
                'ai_suggestion': 'newsletter',
                'thread_data': {
                    'conversation_id': 'single_email_004',
                    'thread_count': 1,
                    'participants': ['Company News'],
                    'latest_date': base_time + timedelta(hours=3),
                    'topic': 'Daily Newsletter'
                }
            }
        ]
        
        print("📊 Input Test Data:")
        print(f"   Total email suggestions: {len(email_suggestions)}")
        print(f"   - 1 team action (Project Update)")
        print(f"   - 2 certificate-related emails (should be grouped)")
        print(f"   - 1 newsletter")
        print()
        
        # Test enhanced thread grouping
        print("🔗 Testing enhanced thread grouping...")
        enhanced_groups = email_processor.group_similar_threads(email_suggestions)
        
        print("📋 Enhanced Thread Grouping Results:")
        print(f"   Number of enhanced thread groups: {len(enhanced_groups)}")
        
        for i, (group_id, group_data) in enumerate(enhanced_groups.items(), 1):
            emails_count = len(group_data['emails'])
            print(f"   Group {i}: {emails_count} emails")
            print(f"     Primary subject: {group_data['primary_subject']}")
            print(f"     Thread keys: {group_data['thread_keys']}")
        
        print()
        
        # Test holistic duplicate removal with processed action items
        print("🔄 Testing holistic duplicate removal...")
        
        # Create action items data that would include the same content
        action_items_data = {
            'required_personal_action': [
                {
                    'email_object': MockEmail('email_002', 'Certificate Renewal Reminder', 'IT Security', base_time + timedelta(hours=1)),
                    'email_subject': 'Certificate Renewal Reminder',
                    'email_sender': 'IT Security',
                    'action_details': {
                        'due_date': '2025-01-15',
                        'action_required': 'Renew security certificate',
                        'explanation': 'Security certificate expires soon'
                    }
                }
            ],
            'fyi': [
                {
                    'email_object': MockEmail('email_005', 'Certificate Renewal Notice', 'Security Admin', base_time + timedelta(hours=4)),
                    'email_subject': 'Certificate Renewal Notice',
                    'email_sender': 'Security Admin',
                    'summary': 'Another certificate renewal notice - should be removed as duplicate'
                }
            ],
            'newsletter': [
                {
                    'email_object': MockEmail('email_004', 'Daily Newsletter', 'Company News', base_time + timedelta(hours=3)),
                    'email_subject': 'Daily Newsletter',
                    'email_sender': 'Company News',
                    'summary': 'Daily company newsletter with updates'
                }
            ]
        }
        
        # Test summary generation with holistic duplicate removal
        summary_sections = summary_generator.build_summary_sections(action_items_data, ai_processor)
        
        print("📋 Summary Sections After Holistic Deduplication:")
        print(f"   Required Actions: {len(summary_sections['required_actions'])} items")
        print(f"   FYI Notices: {len(summary_sections['fyi_notices'])} items")
        print(f"   Newsletters: {len(summary_sections['newsletters'])} items")
        
        # Validation
        success_criteria = []
        
        # Check thread grouping effectiveness
        if len(enhanced_groups) <= 3:  # Should group similar certificate emails
            success_criteria.append("✅ Thread grouping: Similar emails grouped")
            print("   ✅ Thread grouping working - similar content grouped together")
        else:
            success_criteria.append("❌ Thread grouping: Similar emails not grouped")
            print("   ❌ Thread grouping issue - similar emails not grouped")
        
        # Check holistic duplicate removal
        total_final_items = (len(summary_sections['required_actions']) + 
                           len(summary_sections['fyi_notices']) + 
                           len(summary_sections['newsletters']))
        
        if total_final_items < len(action_items_data['required_personal_action']) + len(action_items_data['fyi']) + len(action_items_data['newsletter']):
            success_criteria.append("✅ Holistic deduplication: Cross-section duplicates removed")
            print("   ✅ Holistic deduplication working - cross-section duplicates removed")
        else:
            success_criteria.append("⚠️  Holistic deduplication: No cross-section duplicates detected")
            print("   ⚠️  No cross-section duplicates detected (may be expected)")
        
        print()
        print("📊 Final Results:")
        for criterion in success_criteria:
            print(f"   {criterion}")
        
        all_passed = all("✅" in criterion for criterion in success_criteria)
        if all_passed:
            print("\n🎉 ALL TESTS PASSED: Enhanced grouping and deduplication working correctly!")
        else:
            print("\n⚠️  Some tests need attention - see results above")
        
        print()
        print("=" * 60)
        print("✅ Core thread grouping test completed")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_core_thread_grouping()