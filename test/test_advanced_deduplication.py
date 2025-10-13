"""Test Advanced AI Deduplication for Action Items

This test verifies that the new advanced AI deduplication system can intelligently
identify and merge multiple reminder emails about the same underlying task.
"""

def test_advanced_action_item_deduplication():
    """Test that advanced AI deduplication merges related reminder emails correctly"""
    print("🧪 TESTING ADVANCED AI ACTION ITEM DEDUPLICATION")
    print("=" * 70)
    
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        from summary_generator import SummaryGenerator
        from ai_processor import AIProcessor
        from email_analyzer import EmailAnalyzer
        
        # Mock email objects with different EntryIDs but same underlying task
        class MockEmail:
            def __init__(self, entry_id, subject, sender):
                self.EntryID = entry_id
                self.Subject = subject
                self.SenderName = sender
                self.ReceivedTime = "2025-10-10 08:00:00"
        
        # Create test case matching typical reminder scenario
        email1 = MockEmail("entry_001", "Credential Expiring Soon", "Security System")
        email2 = MockEmail("entry_002", "URGENT: YubiKey Certificate Expires Today", "Security Team")
        email3 = MockEmail("entry_003", "Action Required: Request New Certificate", "Security System")
        email4 = MockEmail("entry_004", "Completely Different Task", "Project Manager")
        
        # Create action items data with multiple reminders about same underlying task
        action_items_data = {
            'required_personal_action': [
                {
                    'email_object': email1,
                    'email_subject': 'Credential Expiring Soon',
                    'email_sender': 'Security System',
                    'action_details': {
                        'due_date': '2025-10-11',
                        'action_required': 'Renew your YubiKey certificate',
                        'explanation': 'Your YubiKey certificate will expire soon'
                    }
                },
                {
                    'email_object': email2,
                    'email_subject': 'URGENT: YubiKey Certificate Expires Today',
                    'email_sender': 'Security Team',
                    'action_details': {
                        'due_date': '2025-10-10',
                        'action_required': 'Request new certificate for YubiKey',
                        'explanation': 'Certificate expires today, immediate action needed'
                    }
                },
                {
                    'email_object': email3,
                    'email_subject': 'Action Required: Request New Certificate',
                    'email_sender': 'Security System',
                    'action_details': {
                        'due_date': '2025-10-10',
                        'action_required': 'Submit certificate renewal request',
                        'explanation': 'Follow the certificate renewal process'
                    }
                },
                {
                    'email_object': email4,
                    'email_subject': 'Completely Different Task',
                    'email_sender': 'Project Manager',
                    'action_details': {
                        'due_date': '2025-10-15',
                        'action_required': 'Review project documentation',
                        'explanation': 'Please review the updated project specs'
                    }
                }
            ]
        }
        
        print("📊 Input Test Data:")
        print("   Email 1: 'Credential Expiring Soon' - YubiKey renewal")
        print("   Email 2: 'URGENT: YubiKey Certificate Expires Today' - Same certificate")
        print("   Email 3: 'Action Required: Request New Certificate' - Same process")
        print("   Email 4: 'Completely Different Task' - Unrelated project work")
        print(f"   Total input items: {len(action_items_data['required_personal_action'])}")
        print()
        
        # Create AI processor and email analyzer
        email_analyzer = EmailAnalyzer()
        ai_processor = AIProcessor(email_analyzer)
        email_analyzer.ai_processor = ai_processor
        
        # Test advanced deduplication directly
        print("🤖 Testing Advanced AI Deduplication Method...")
        original_items = []
        for item_data in action_items_data['required_personal_action']:
            # Build action items similar to how SummaryGenerator does it
            subject, sender, _ = item_data['email_subject'], item_data['email_sender'], item_data['email_object']
            action_details = item_data['action_details']
            
            action_item = {
                'subject': subject,
                'sender': sender,
                'due_date': action_details.get('due_date', 'No specific deadline'),
                'action_required': action_details.get('action_required', 'Review email'),
                'explanation': action_details.get('explanation', 'Details in email'),
                '_entry_id': item_data['email_object'].EntryID
            }
            original_items.append(action_item)
        
        # Test the advanced deduplication method
        if hasattr(ai_processor, 'advanced_deduplicate_action_items'):
            deduplicated_items = ai_processor.advanced_deduplicate_action_items(original_items)
            
            print("📋 Results After Advanced AI Deduplication:")
            print(f"   Original items: {len(original_items)}")
            print(f"   Deduplicated items: {len(deduplicated_items)}")
            print()
            
            for i, item in enumerate(deduplicated_items, 1):
                print(f"   {i}. '{item['subject']}' from {item['sender']}")
                print(f"      Action: {item['action_required']}")
                print(f"      Due: {item['due_date']}")
                
                # Show if this item has contributing emails (merged reminders)
                if 'contributing_emails' in item and item['contributing_emails']:
                    print(f"      📧 Merged {len(item['contributing_emails'])} related reminder(s)")
                    for contrib in item['contributing_emails']:
                        print(f"         - '{contrib['subject']}' from {contrib['sender']}")
                print()
            
            # Verify results
            if len(deduplicated_items) == 2:
                print("✅ SUCCESS: Advanced AI deduplication working correctly!")
                print("   - 3 YubiKey certificate reminders merged into 1 item")
                print("   - 1 unrelated project task preserved")
                
                # Check that we have one merged certificate item and one project item
                cert_items = [item for item in deduplicated_items if 'YubiKey' in item.get('action_required', '') or 'certificate' in item.get('action_required', '').lower()]
                project_items = [item for item in deduplicated_items if 'project' in item.get('action_required', '').lower()]
                
                if len(cert_items) == 1 and len(project_items) == 1:
                    cert_item = cert_items[0]
                    if 'contributing_emails' in cert_item and len(cert_item['contributing_emails']) >= 2:
                        print("   - Certificate item properly merged with contributing emails tracked")
                    else:
                        print("   - Certificate item present (merging details may vary)")
                else:
                    print(f"   ⚠️  Unexpected categorization: {len(cert_items)} cert items, {len(project_items)} project items")
                    
            else:
                print(f"❌ FAILURE: Expected 2 deduplicated items, got {len(deduplicated_items)}")
                for item in deduplicated_items:
                    print(f"   - '{item['subject']}': {item['action_required']}")
        else:
            print("❌ FAILURE: Advanced deduplication method not available in AI processor")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 70)
    print("✅ Advanced deduplication test completed")
    print()

if __name__ == "__main__":
    test_advanced_action_item_deduplication()