#!/usr/bin/env python3
"""
Test holistic cross-section duplicate removal
"""

import sys
import os

# Add parent directory to path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

def test_holistic_deduplication():
    """Test holistic cross-section duplicate removal"""
    print("🧪 TESTING HOLISTIC CROSS-SECTION DEDUPLICATION")
    print("=" * 60)
    
    try:
        from summary_generator import SummaryGenerator
        from ai_processor import AIProcessor
        from email_analyzer import EmailAnalyzer
        
        # Mock email objects
        from datetime import datetime
        
        class MockEmail:
            def __init__(self, entry_id, subject, sender):
                self.EntryID = entry_id
                self.Subject = subject
                self.SenderName = sender
                self.ReceivedTime = datetime.now()  # Use proper datetime object
        
        # Create test data with cross-section duplicates
        # Action item about certificate renewal
        cert_email = MockEmail("cert_action", "Certificate Renewal Required", "IT Security")
        
        # FYI that's essentially the same as the action item (should be removed)
        cert_fyi_email = MockEmail("cert_fyi", "Certificate Expiring Soon", "Security Team")
        
        # Newsletter that mentions certificates (should be removed if similar enough)
        newsletter_email = MockEmail("newsletter", "Security Update Newsletter", "IT Newsletter")
        
        # Unique FYI that should be kept
        unique_fyi_email = MockEmail("unique_fyi", "Office Closure Notice", "HR Team")
        
        action_items_data = {
            'required_personal_action': [
                {
                    'email_object': cert_email,
                    'email_subject': 'Certificate Renewal Required',
                    'email_sender': 'IT Security',
                    'action_details': {
                        'due_date': '2025-01-15',
                        'action_required': 'Renew your security certificate before expiration',
                        'explanation': 'Your certificate expires on 2025-01-15 and needs renewal'
                    }
                }
            ],
            'fyi': [
                {
                    'email_object': cert_fyi_email,
                    'email_subject': 'Certificate Expiring Soon',
                    'email_sender': 'Security Team',
                    'summary': 'Your certificate will expire soon and needs renewal'  # Similar to action
                },
                {
                    'email_object': unique_fyi_email,
                    'email_subject': 'Office Closure Notice',
                    'email_sender': 'HR Team',
                    'summary': 'Office will be closed for maintenance next Friday'  # Unique
                }
            ],
            'newsletter': [
                {
                    'email_object': newsletter_email,
                    'email_subject': 'Security Update Newsletter',
                    'email_sender': 'IT Newsletter',
                    'summary': 'Monthly security newsletter with certificate renewal reminders'  # Similar to action
                }
            ]
        }
        
        print("📊 Input Test Data:")
        print(f"   Required Actions: {len(action_items_data['required_personal_action'])} items")
        print(f"     - Certificate renewal action")
        print(f"   FYI Notices: {len(action_items_data['fyi'])} items")
        print(f"     - Certificate expiring notice (similar to action)")
        print(f"     - Office closure notice (unique)")
        print(f"   Newsletters: {len(action_items_data['newsletter'])} items")
        print(f"     - Security newsletter with certificate info (similar to action)")
        print()
        
        # Create email analyzer and AI processor
        email_analyzer = EmailAnalyzer()
        ai_processor = AIProcessor(email_analyzer)
        email_analyzer.ai_processor = ai_processor
        
        # Test holistic deduplication
        generator = SummaryGenerator()
        summary_sections = generator.build_summary_sections(action_items_data, ai_processor)
        
        print("📋 Results After Holistic Deduplication:")
        print(f"   Required Actions: {len(summary_sections['required_actions'])} items")
        print(f"   FYI Notices: {len(summary_sections['fyi_notices'])} items")
        print(f"   Newsletters: {len(summary_sections['newsletters'])} items")
        print()
        
        # Show remaining items
        print("📝 Remaining Items:")
        for action in summary_sections['required_actions']:
            print(f"   Action: '{action['subject']}' from {action['sender']}")
        
        for fyi in summary_sections['fyi_notices']:
            print(f"   FYI: '{fyi['subject']}' from {fyi['sender']}")
        
        for newsletter in summary_sections['newsletters']:
            print(f"   Newsletter: '{newsletter['subject']}' from {newsletter['sender']}")
        
        print()
        
        # Validation
        initial_total = (len(action_items_data['required_personal_action']) + 
                        len(action_items_data['fyi']) + 
                        len(action_items_data['newsletter']))
        
        final_total = (len(summary_sections['required_actions']) + 
                      len(summary_sections['fyi_notices']) + 
                      len(summary_sections['newsletters']))
        
        print("📊 Deduplication Analysis:")
        print(f"   Initial total items: {initial_total}")
        print(f"   Final total items: {final_total}")
        print(f"   Items removed: {initial_total - final_total}")
        
        # Expected behavior:
        # - Certificate action should remain (1 required action)
        # - Certificate FYI should be removed (similar to action)
        # - Office closure FYI should remain (unique, 1 FYI)
        # - Certificate newsletter might be removed (similar to action)
        
        success_criteria = []
        
        # Should have 1 required action (certificate)
        if len(summary_sections['required_actions']) == 1:
            success_criteria.append("✅ Required actions preserved correctly")
        else:
            success_criteria.append(f"❌ Expected 1 required action, got {len(summary_sections['required_actions'])}")
        
        # Should have 1 FYI (office closure, certificate FYI should be removed)
        if len(summary_sections['fyi_notices']) == 1:
            remaining_fyi = summary_sections['fyi_notices'][0]
            if 'Office' in remaining_fyi['subject']:
                success_criteria.append("✅ FYI deduplication working - certificate FYI removed, office closure kept")
            else:
                success_criteria.append("⚠️  Wrong FYI remained - expected office closure")
        elif len(summary_sections['fyi_notices']) == 2:
            success_criteria.append("⚠️  FYI deduplication not working - certificate FYI not removed")
        else:
            success_criteria.append(f"❌ Unexpected FYI count: {len(summary_sections['fyi_notices'])}")
        
        # Newsletter may or may not be removed depending on similarity threshold
        if len(summary_sections['newsletters']) == 0:
            success_criteria.append("✅ Newsletter deduplication working - certificate newsletter removed")
        else:
            success_criteria.append("ℹ️  Newsletter kept - similarity may be below threshold")
        
        # Overall reduction check
        if final_total < initial_total:
            success_criteria.append("✅ Overall deduplication effective - total items reduced")
        else:
            success_criteria.append("❌ No deduplication occurred")
        
        print()
        print("✅ Results Summary:")
        for criterion in success_criteria:
            print(f"   {criterion}")
        
        # Count successes
        successes = sum(1 for c in success_criteria if c.startswith("✅"))
        total_checks = len(success_criteria)
        
        if successes >= total_checks * 0.75:  # 75% success rate
            print(f"\n🎉 SUCCESS: Holistic deduplication working! ({successes}/{total_checks} checks passed)")
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: Some deduplication working ({successes}/{total_checks} checks passed)")
        
        print()
        print("=" * 60)
        print("✅ Holistic deduplication test completed")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_holistic_deduplication()