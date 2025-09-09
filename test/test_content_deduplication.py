#!/usr/bin/env python3
"""
Test content-based deduplication for similar emails
"""

import sys
import os

# Add parent directory to path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

def test_content_deduplication():
    """Test that similar content emails are properly deduplicated"""
    print("🧪 TESTING CONTENT-BASED DEDUPLICATION")
    print("=" * 60)
    
    try:
        from summary_generator import SummaryGenerator
        
        # Mock email objects with different EntryIDs but similar content
        class MockEmail:
            def __init__(self, entry_id, subject, sender):
                self.EntryID = entry_id
                self.Subject = subject
                self.SenderName = sender
                self.ReceivedTime = "2025-09-09"
        
        # Create test case matching your screenshot
        email1 = MockEmail("entry_123", "Credential Expiring", "One Yubi")
        email2 = MockEmail("entry_456", "Credential Expiring", "One Yubi")  # Same content, different ID
        email3 = MockEmail("entry_789", "Different Task", "Another Sender")
        
        action_items_data = {
            'required_personal_action': [
                {
                    'email_object': email1,
                    'email_subject': 'Credential Expiring',
                    'email_sender': 'One Yubi',
                    'action_details': {
                        'due_date': '2025-10-09',
                        'action_required': 'Request a new certificate for your YubiKey credential',
                        'explanation': 'Your current YubiKey certificate is set to expire on 2025-10-09'
                    }
                },
                {
                    'email_object': email2,  # DUPLICATE CONTENT - same subject, sender, due date, action
                    'email_subject': 'Credential Expiring', 
                    'email_sender': 'One Yubi',
                    'action_details': {
                        'due_date': '2025-10-09',
                        'action_required': 'Request and set up a new certificate for your YubiKey',  # Slightly different wording
                        'explanation': 'The current certificate associated with your YubiKey is expiring in 45 days'
                    }
                },
                {
                    'email_object': email3,  # UNIQUE
                    'email_subject': 'Different Task',
                    'email_sender': 'Another Sender',
                    'action_details': {
                        'due_date': '2025-09-15',
                        'action_required': 'Complete project review',
                        'explanation': 'Need to review the project documentation'
                    }
                }
            ]
        }
        
        print("📊 Input Test Data:")
        print("   Email 1: 'Credential Expiring' from One Yubi (2025-10-09)")
        print("   Email 2: 'Credential Expiring' from One Yubi (2025-10-09) - SIMILAR CONTENT")
        print("   Email 3: 'Different Task' from Another Sender - UNIQUE")
        print(f"   Total input items: {len(action_items_data['required_personal_action'])}")
        print()
        
        # Test content-based deduplication
        generator = SummaryGenerator()
        summary_sections = generator.build_summary_sections(action_items_data)
        
        print("📋 Results After Content Deduplication:")
        required_actions = summary_sections['required_actions']
        print(f"   Required Actions: {len(required_actions)} items")
        
        for i, action in enumerate(required_actions, 1):
            print(f"   {i}. '{action['subject']}' from {action['sender']} (Due: {action['due_date']})")
        print()
        
        # Verify results
        if len(required_actions) == 2:
            print("✅ SUCCESS: Content-based deduplication working!")
            print("   - Similar 'Credential Expiring' emails merged to 1 item")
            print("   - 'Different Task' email preserved as unique")
            
            # Check that we kept the first occurrence
            credential_items = [a for a in required_actions if 'Credential' in a['subject']]
            if len(credential_items) == 1:
                print(f"   - Kept credential item with action: {credential_items[0]['action_required'][:50]}...")
            
        else:
            print(f"❌ FAILURE: Expected 2 items, got {len(required_actions)}")
            print("   Content-based deduplication not working properly")
            
            # Debug output
            print("\n🔍 Debug Information:")
            for i, action in enumerate(required_actions):
                content_hash = action.get('_content_hash', 'NO_HASH')
                print(f"   Item {i+1}: {action['subject']} (Hash: {content_hash[:8]}...)")
                
        print()
        print("=" * 60)
        print("✅ Content deduplication test completed")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_content_deduplication()
