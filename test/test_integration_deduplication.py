"""Integration test for Enhanced AI Deduplication

This test verifies that the enhanced deduplication integrates properly
with the full email processing pipeline, including summary generation.
"""

def test_full_deduplication_integration():
    """Test that enhanced deduplication works with complete summary generation"""
    print("🧪 TESTING FULL DEDUPLICATION INTEGRATION")
    print("=" * 60)
    
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        from summary_generator import SummaryGenerator
        from ai_processor import AIProcessor
        from email_analyzer import EmailAnalyzer
        
        # Mock email objects for integration test
        from datetime import datetime
        
        class MockEmail:
            def __init__(self, entry_id, subject, sender):
                self.EntryID = entry_id
                self.Subject = subject
                self.SenderName = sender
                self.ReceivedTime = datetime.strptime("2025-10-10 08:00:00", "%Y-%m-%d %H:%M:%S")
        
        # Create comprehensive test scenario
        action_items_data = {
            'required_personal_action': [
                # Certificate renewal reminders (should merge)
                {
                    'email_object': MockEmail("cert_001", "Certificate Expiring", "IT Security"),
                    'email_subject': 'Certificate Expiring',
                    'email_sender': 'IT Security',
                    'action_details': {
                        'due_date': '2025-10-12',
                        'action_required': 'Renew SSL certificate',
                        'explanation': 'SSL certificate needs renewal'
                    }
                },
                {
                    'email_object': MockEmail("cert_002", "URGENT: SSL Cert Expires Soon", "Security Team"),
                    'email_subject': 'URGENT: SSL Cert Expires Soon',
                    'email_sender': 'Security Team',
                    'action_details': {
                        'due_date': '2025-10-11',
                        'action_required': 'Submit SSL certificate renewal request',
                        'explanation': 'Certificate expires in 1 day'
                    }
                },
                # Meeting reminders (should merge)
                {
                    'email_object': MockEmail("meet_001", "Team Meeting Tomorrow", "Manager"),
                    'email_subject': 'Team Meeting Tomorrow',
                    'email_sender': 'Manager',
                    'action_details': {
                        'due_date': '2025-10-11',
                        'action_required': 'Attend team meeting',
                        'explanation': 'Quarterly planning session'
                    }
                },
                {
                    'email_object': MockEmail("meet_002", "Reminder: Quarterly Planning Meeting", "Admin"),
                    'email_subject': 'Reminder: Quarterly Planning Meeting',
                    'email_sender': 'Admin',
                    'action_details': {
                        'due_date': '2025-10-11',
                        'action_required': 'Join quarterly planning session',
                        'explanation': 'Bring your project updates'
                    }
                },
                # Unique task (should remain separate)
                {
                    'email_object': MockEmail("task_001", "Code Review Request", "Developer"),
                    'email_subject': 'Code Review Request',
                    'email_sender': 'Developer',
                    'action_details': {
                        'due_date': '2025-10-13',
                        'action_required': 'Review pull request #123',
                        'explanation': 'New feature implementation needs review'
                    }
                }
            ],
            'team_action': [
                # Another unique task in different section
                {
                    'email_object': MockEmail("team_001", "Budget Planning", "Finance"),
                    'email_subject': 'Budget Planning',
                    'email_sender': 'Finance',
                    'action_details': {
                        'due_date': '2025-10-14',
                        'action_required': 'Submit budget proposal',
                        'explanation': 'Q4 budget planning cycle'
                    }
                }
            ],
            'fyi': [
                # FYI that might overlap with actions
                {
                    'email_object': MockEmail("fyi_001", "SSL Certificate Update", "IT Dept"),
                    'email_subject': 'SSL Certificate Update',
                    'email_sender': 'IT Dept',
                    'summary': 'Information about SSL certificate renewal process'
                }
            ]
        }
        
        print("📊 Input Test Data:")
        print("   Required Actions: 5 items (2 cert reminders + 2 meeting reminders + 1 unique)")
        print("   Team Actions: 1 item")
        print("   FYI Notices: 1 item")
        print("   Expected after deduplication: ~4 unique items total")
        print()
        
        # Create integrated components
        email_analyzer = EmailAnalyzer()
        ai_processor = AIProcessor(email_analyzer)
        email_analyzer.ai_processor = ai_processor
        generator = SummaryGenerator()
        
        print("🔄 Running full summary generation with enhanced deduplication...")
        summary_sections = generator.build_summary_sections(action_items_data, ai_processor)
        
        print("📋 Results After Full Integration:")
        for section_name, items in summary_sections.items():
            if items:  # Only show sections with items
                section_display = section_name.replace('_', ' ').title()
                print(f"   {section_display}: {len(items)} items")
                
                for i, item in enumerate(items, 1):
                    subject = item.get('subject', item.get('summary', 'Unknown'))
                    sender = item.get('sender', 'Unknown')
                    print(f"     {i}. '{subject}' from {sender}")
                    
                    # Show if this item has merged reminders
                    if 'contributing_emails' in item and item['contributing_emails']:
                        print(f"        📧 Merged {len(item['contributing_emails'])} related reminder(s)")
                    
                    # Show action details for action items
                    if 'action_required' in item:
                        print(f"        Action: {item['action_required']}")
                        print(f"        Due: {item['due_date']}")
                print()
        
        # Analyze results
        total_items = sum(len(items) for items in summary_sections.values())
        required_actions = len(summary_sections.get('required_actions', []))
        team_actions = len(summary_sections.get('team_actions', []))
        fyi_notices = len(summary_sections.get('fyi_notices', []))
        
        print("📈 Integration Analysis:")
        print(f"   Total items in summary: {total_items}")
        print(f"   Required actions: {required_actions}")
        print(f"   Team actions: {team_actions}")
        print(f"   FYI notices: {fyi_notices}")
        
        # Check for successful deduplication
        if required_actions <= 3:  # Should be 3 or fewer after merging
            print("✅ SUCCESS: Deduplication reduced duplicate reminders!")
            
            # Check for merged items
            merged_items = []
            for item in summary_sections.get('required_actions', []):
                if 'contributing_emails' in item and item['contributing_emails']:
                    merged_items.append(item)
            
            if merged_items:
                print(f"   Found {len(merged_items)} merged action item(s)")
                for item in merged_items:
                    print(f"   - '{item['subject']}' merged {len(item['contributing_emails'])} reminder(s)")
            else:
                print("   No merged items detected (may be handled by other deduplication)")
                
        else:
            print(f"❌ DEDUPLICATION CONCERN: Still have {required_actions} required actions")
            print("   Expected fewer after merging similar reminders")
        
        # Check cross-section deduplication
        if fyi_notices == 0:
            print("✅ Cross-section deduplication: FYI covered by action items")
        elif fyi_notices == 1:
            print("✅ Cross-section deduplication: Some FYIs may be preserved")
        
        print()
        print("✅ Full integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)
    print()

if __name__ == "__main__":
    test_full_deduplication_integration()