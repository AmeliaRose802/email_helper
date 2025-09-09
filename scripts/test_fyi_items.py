#!/usr/bin/env python3
"""
FYI Items Verification Script - Test if FYI items are working correctly in the summary
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from summary_generator import SummaryGenerator
from task_persistence import TaskPersistence

def test_fyi_items():
    print("🔍 TESTING FYI ITEMS IN SUMMARY")
    print("=" * 50)
    
    # Create test data that mirrors actual email processing
    test_action_items = {
        'required_personal_action': [
            {
                'action': 'Complete quarterly report',
                'email_subject': 'Q3 Report Due',
                'email_sender': 'Manager',
                'email_date': '2025-09-08',
                'action_details': {
                    'due_date': '2025-09-15',
                    'explanation': 'Quarterly business report needed',
                    'action_required': 'Complete and submit report',
                    'links': []
                }
            }
        ],
        'fyi': [
            {
                'summary': 'Office maintenance scheduled for this Friday',
                'email_subject': 'Building Maintenance Notice',
                'email_sender': 'Facilities Management',
                'email_date': '2025-09-08'
            },
            {
                'summary': 'New employee John Smith started in Engineering',
                'email_subject': 'New Team Member Announcement',
                'email_sender': 'HR Department',
                'email_date': '2025-09-08'
            }
        ],
        'newsletter': [
            {
                'summary': 'Monthly tech newsletter with industry updates',
                'email_subject': 'Tech Industry Newsletter - September 2025',
                'email_sender': 'Tech News Daily',
                'email_date': '2025-09-08'
            }
        ]
    }
    
    print("📧 Test data created:")
    print(f"  - Required actions: {len(test_action_items['required_personal_action'])}")
    print(f"  - FYI items: {len(test_action_items['fyi'])}")
    print(f"  - Newsletters: {len(test_action_items['newsletter'])}")
    
    # Test SummaryGenerator
    print("\n🔄 Testing SummaryGenerator...")
    sg = SummaryGenerator()
    summary_sections = sg.build_summary_sections(test_action_items)
    
    print("📋 Generated summary sections:")
    for section_key, items in summary_sections.items():
        if items:
            print(f"  ✅ {section_key}: {len(items)} items")
            if section_key == 'fyi_notices':
                for i, item in enumerate(items, 1):
                    print(f"     {i}. {item.get('summary', 'No summary')}")
                    print(f"        From: {item.get('sender', 'No sender')}")
        else:
            print(f"  ⚪ {section_key}: 0 items")
    
    # Test TaskPersistence comprehensive summary
    print("\n🔄 Testing TaskPersistence comprehensive summary...")
    tp = TaskPersistence()
    comprehensive_summary = tp.get_comprehensive_summary(summary_sections)
    
    print("🎯 Comprehensive summary:")
    for section_key, items in comprehensive_summary.items():
        if items:
            print(f"  ✅ {section_key}: {len(items)} items")
        else:
            print(f"  ⚪ {section_key}: 0 items")
    
    # Test specific FYI display logic
    print("\n🖥️ Testing FYI display logic...")
    fyi_items = comprehensive_summary.get('fyi_notices', [])
    if fyi_items:
        print(f"✅ Found {len(fyi_items)} FYI items for display:")
        for i, item in enumerate(fyi_items, 1):
            # Simulate the display format used in the app
            display_text = f"• {item['summary']} ({item['sender']})"
            print(f"  {i}. {display_text}")
    else:
        print("❌ No FYI items found for display!")
    
    # Test newsletter display
    newsletter_items = comprehensive_summary.get('newsletters', [])
    if newsletter_items:
        print(f"\n📰 Found {len(newsletter_items)} newsletter items:")
        for i, item in enumerate(newsletter_items, 1):
            print(f"  {i}. {item.get('summary', 'No summary')} (from: {item.get('sender', 'Unknown')})")
    else:
        print("\n📰 No newsletter items found")
    
    # Test the display condition logic
    print("\n🔍 Testing display condition logic...")
    sections_config = [
        ('required_actions', '🔴 REQUIRED ACTION ITEMS (ME)'),
        ('team_actions', '👥 TEAM ACTION ITEMS'),
        ('optional_actions', '📝 OPTIONAL ACTION ITEMS'),
        ('job_listings', '💼 JOB LISTINGS'),
        ('optional_events', '🎪 OPTIONAL EVENTS'),
        ('fyi_notices', '📋 FYI NOTICES'),
        ('newsletters', '📰 NEWSLETTERS SUMMARY')
    ]
    
    for section_key, title in sections_config:
        items = comprehensive_summary.get(section_key, [])
        
        # This is the logic from the actual display code
        if not items and section_key in ['required_actions', 'team_actions']:
            # Always show critical sections even if empty
            display_decision = "SHOW (critical section)"
        elif not items:
            # Skip empty optional sections
            display_decision = "SKIP (empty optional section)"
        else:
            display_decision = f"SHOW ({len(items)} items)"
        
        print(f"  {section_key}: {display_decision}")
    
    print("\n✅ FYI ITEMS TEST COMPLETE")
    
    # Summary
    total_items = sum(len(items) for items in comprehensive_summary.values())
    fyi_count = len(comprehensive_summary.get('fyi_notices', []))
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total items in comprehensive summary: {total_items}")
    print(f"  FYI notices: {fyi_count}")
    
    if fyi_count > 0:
        print(f"  ✅ FYI items are working correctly!")
    else:
        print(f"  ❌ FYI items are NOT working - investigate further!")
    
    return fyi_count > 0

if __name__ == "__main__":
    success = test_fyi_items()
    sys.exit(0 if success else 1)
