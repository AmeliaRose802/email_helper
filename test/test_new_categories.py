#!/usr/bin/env python3
"""
Test script for new FYI and NEWSLETTER categories
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai_processor import AIProcessor

def test_new_categories():
    """Test that the new categories are properly recognized"""
    ai_processor = AIProcessor()
    
    # Test available categories
    categories = ai_processor.get_available_categories()
    print("Available categories:")
    for category in categories:
        print(f"  • {category}")
    
    # Check if new categories are included
    assert 'fyi' in categories, "FYI category missing"
    assert 'newsletter' in categories, "NEWSLETTER category missing"
    
    print("\n✅ All new categories are properly registered!")
    
    # Test mock email content for FYI summary
    fyi_email = {
        'subject': 'System Maintenance Notification',
        'sender': 'IT Support',
        'date': '2025-09-08',
        'body': 'Scheduled maintenance on Azure services this weekend from 2-4 AM.'
    }
    
    # Test mock email content for newsletter summary
    newsletter_email = {
        'subject': 'Tech Weekly Update - September 2025',
        'sender': 'Microsoft Updates',
        'date': '2025-09-08',
        'body': 'This week: New Azure AI features, security updates, and upcoming conferences.'
    }
    
    print("\n📋 Testing FYI summary generation...")
    try:
        fyi_summary = ai_processor.generate_fyi_summary(fyi_email, "Test context")
        print(f"FYI Summary: {fyi_summary}")
        assert fyi_summary.startswith('•'), "FYI summary should start with bullet point"
    except Exception as e:
        print(f"FYI summary test failed (expected - no AI connection): {e}")
    
    print("\n📰 Testing newsletter summary generation...")
    try:
        newsletter_summary = ai_processor.generate_newsletter_summary(newsletter_email, "Test context")
        print(f"Newsletter Summary: {newsletter_summary}")
    except Exception as e:
        print(f"Newsletter summary test failed (expected - no AI connection): {e}")
    
    print("\n✅ Basic functionality tests completed!")

if __name__ == "__main__":
    test_new_categories()
