#!/usr/bin/env python3
"""
Test script to verify duplicate action item elimination
"""

import sys
import os

# Add parent directory to path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

def test_duplicate_detection():
    """Test that duplicate action items are properly filtered"""
    print("🧪 TESTING DUPLICATE ACTION ITEM ELIMINATION")
    print("=" * 60)
    
    try:
        from summary_generator import SummaryGenerator
        
        # Mock email object with EntryID
        class MockEmail:
            def __init__(self, entry_id, subject, sender):
                self.EntryID = entry_id
                self.Subject = subject
                self.SenderName = sender
                self.ReceivedTime = "2025-09-09"
        
        # Create mock data with intentional duplicates
        duplicate_email = MockEmail("email_123", "Important Task", "Manager")
        unique_email = MockEmail("email_456", "Different Task", "Colleague")
        
        action_items_data = {
            'required_personal_action': [
                {
                    'email_object': duplicate_email,
                    'email_subject': 'Important Task',
                    'email_sender': 'Manager',
                    'action_details': {
                        'due_date': '2025-09-10',
                        'action_required': 'Complete report',
                        'explanation': 'Need to finish quarterly report'
                    }
                },
                {
                    'email_object': duplicate_email,  # DUPLICATE - same EntryID
                    'email_subject': 'Important Task',
                    'email_sender': 'Manager', 
                    'action_details': {
                        'due_date': '2025-09-10',
                        'action_required': 'Complete report',
                        'explanation': 'Need to finish quarterly report'
                    }
                },
                {
                    'email_object': unique_email,  # UNIQUE
                    'email_subject': 'Different Task',
                    'email_sender': 'Colleague',
                    'action_details': {
                        'due_date': '2025-09-11',
                        'action_required': 'Review document',
                        'explanation': 'Check the specs document'
                    }
                }
            ],
            'fyi': [
                {
                    'email_object': duplicate_email,  # DUPLICATE - same EntryID as action item
                    'email_subject': 'Important Task',
                    'email_sender': 'Manager',
                    'summary': 'Task notification',
                },
                {
                    'email_object': unique_email,  # UNIQUE
                    'email_subject': 'Different Task',
                    'email_sender': 'Colleague',
                    'summary': 'Different notification',
                }
            ]
        }
        
        print("📊 Input Data:")
        print(f"   Required Actions: {len(action_items_data['required_personal_action'])} items")
        print(f"   FYI Notices: {len(action_items_data['fyi'])} items")
        print(f"   Expected unique emails: 2 (email_123, email_456)")
        print()
        
        # Test deduplication
        from ai_processor import AIProcessor
        from email_analyzer import EmailAnalyzer
        
        # Create email analyzer and AI processor
        email_analyzer = EmailAnalyzer()
        ai_processor = AIProcessor(email_analyzer)
        email_analyzer.ai_processor = ai_processor
        
        generator = SummaryGenerator()
        summary_sections = generator.build_summary_sections(action_items_data, ai_processor)
        
        print("📋 Results After Deduplication:")
        print(f"   Required Actions: {len(summary_sections['required_actions'])} items")
        print(f"   FYI Notices: {len(summary_sections['fyi_notices'])} items")
        print()
        
        # Verify results
        total_items = len(summary_sections['required_actions']) + len(summary_sections['fyi_notices'])
        
        if total_items == 2:
            print("✅ SUCCESS: Duplicates properly eliminated!")
            print("   - Each email appears only once across all sections")
            
            # Check which emails were kept
            kept_entry_ids = set()
            for action in summary_sections['required_actions']:
                if '_entry_id' in action:
                    kept_entry_ids.add(action['_entry_id'])
            for fyi in summary_sections['fyi_notices']:
                if '_entry_id' in fyi:
                    kept_entry_ids.add(fyi['_entry_id'])
            
            print(f"   - Unique email IDs preserved: {len(kept_entry_ids)}")
            print(f"   - Email IDs: {sorted(kept_entry_ids)}")
            
        else:
            print(f"❌ FAILURE: Expected 2 total items, got {total_items}")
            print("   Duplicates were not properly eliminated")
            
            # Debug output
            print("\n🔍 Debug Information:")
            for i, action in enumerate(summary_sections['required_actions']):
                entry_id = action.get('_entry_id', 'NO_ID')
                print(f"   Action {i+1}: {action['subject']} (ID: {entry_id})")
            for i, fyi in enumerate(summary_sections['fyi_notices']):
                entry_id = fyi.get('_entry_id', 'NO_ID')
                print(f"   FYI {i+1}: {fyi['subject']} (ID: {entry_id})")
                
        print()
        print("=" * 60)
        print("✅ Deduplication test completed")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_duplicate_detection()
