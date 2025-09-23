#!/usr/bin/env python3
"""
Debug script to test the full deduplication pipeline
"""

import sys
import os

# Add parent directory to path so we can import from src
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

def test_full_deduplication_pipeline():
    """Test the full deduplication pipeline with debug output"""
    print("🔍 TESTING FULL DEDUPLICATION PIPELINE")
    print("=" * 60)
    
    try:
        from summary_generator import SummaryGenerator
        from ai_processor import AIProcessor
        from email_analyzer import EmailAnalyzer
        
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
        print(f"   Total input items: {len(action_items_data['required_personal_action'])}")
        print()
        
        # Create email analyzer and AI processor
        email_analyzer = EmailAnalyzer()
        ai_processor = AIProcessor(email_analyzer)
        email_analyzer.ai_processor = ai_processor
        
        print("🔧 Component Setup:")
        print(f"   Email Analyzer: {email_analyzer}")
        print(f"   AI Processor: {ai_processor}")
        print(f"   AI Processor has email_analyzer: {hasattr(ai_processor, 'email_analyzer')}")
        print(f"   AI Processor.email_analyzer: {getattr(ai_processor, 'email_analyzer', None)}")
        print()
        
        # Test the summary generator
        generator = SummaryGenerator()
        
        # Add debug to the _remove_duplicate_items method
        original_method = generator._remove_duplicate_items
        
        def debug_remove_duplicate_items(summary_sections, ai_processor):
            print("🔍 DEBUG: _remove_duplicate_items called")
            print(f"   ai_processor: {ai_processor}")
            print(f"   hasattr(ai_processor, 'email_analyzer'): {hasattr(ai_processor, 'email_analyzer') if ai_processor else 'N/A'}")
            print(f"   ai_processor.email_analyzer: {getattr(ai_processor, 'email_analyzer', None) if ai_processor else 'N/A'}")
            
            result = original_method(summary_sections, ai_processor)
            print("🔍 DEBUG: _remove_duplicate_items completed")
            return result
        
        generator._remove_duplicate_items = debug_remove_duplicate_items
        
        summary_sections = generator.build_summary_sections(action_items_data, ai_processor)
        
        print("📋 Results After Content Deduplication:")
        required_actions = summary_sections['required_actions']
        print(f"   Required Actions: {len(required_actions)} items")
        
        for i, action in enumerate(required_actions, 1):
            print(f"   {i}. '{action['subject']}' from {action['sender']} (Due: {action['due_date']})")
            if 'contributing_emails' in action:
                print(f"      Contributing emails: {len(action['contributing_emails'])}")
        print()
        
        # Verify results
        if len(required_actions) == 2:
            print("✅ SUCCESS: Content-based deduplication working!")
            print("   - Similar 'Credential Expiring' emails merged to 1 item")
            print("   - 'Different Task' email preserved as unique")
            
        else:
            print(f"❌ FAILURE: Expected 2 items, got {len(required_actions)}")
            print("   Content-based deduplication not working properly")
        
        print()
        print("=" * 60)
        print("✅ Full pipeline test completed")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_deduplication_pipeline()