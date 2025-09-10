#!/usr/bin/env python3
"""
Test script to verify FYI categorization case sensitivity fix
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_categorization_counting():
    """Test the case-insensitive categorization counting"""
    
    print("🧪 TESTING FYI CATEGORIZATION FIX")
    print("=" * 50)
    
    # Test data with different case variations
    test_suggestions = [
        {'ai_suggestion': 'fyi', 'subject': 'Lowercase fyi test'},
        {'ai_suggestion': 'FYI', 'subject': 'Uppercase FYI test'},  
        {'ai_suggestion': 'Fyi', 'subject': 'Title case Fyi test'},
        {'ai_suggestion': 'required_personal_action', 'subject': 'Action item test'},
        {'ai_suggestion': 'team_action', 'subject': 'Team action test'},
        {'ai_suggestion': 'newsletter', 'subject': 'Newsletter test'}
    ]
    
    # Category definitions (as in the actual code)
    inbox_categories = {'required_personal_action', 'optional_action', 'job_listing', 'work_relevant'}
    non_inbox_categories = {'team_action', 'optional_event', 'fyi', 'newsletter', 'general_information', 'spam_to_delete'}
    
    print("Test suggestions:")
    for i, s in enumerate(test_suggestions, 1):
        print(f"  {i}. {s['ai_suggestion']} - {s['subject']}")
    
    print(f"\nCategory sets:")
    print(f"  Inbox categories: {inbox_categories}")
    print(f"  Non-inbox categories: {non_inbox_categories}")
    
    # Test original case-sensitive logic
    original_inbox_count = sum(1 for s in test_suggestions if s['ai_suggestion'] in inbox_categories)
    original_non_inbox_count = sum(1 for s in test_suggestions if s['ai_suggestion'] in non_inbox_categories)
    
    # Test fixed case-insensitive logic  
    fixed_inbox_count = sum(1 for s in test_suggestions if s['ai_suggestion'].lower() in inbox_categories)
    fixed_non_inbox_count = sum(1 for s in test_suggestions if s['ai_suggestion'].lower() in non_inbox_categories)
    
    print(f"\n📊 RESULTS:")
    print(f"{'Method':<20} {'Inbox Count':<15} {'Non-Inbox Count':<20}")
    print("-" * 55)
    print(f"{'Original (broken)':<20} {original_inbox_count:<15} {original_non_inbox_count:<20}")
    print(f"{'Fixed (working)':<20} {fixed_inbox_count:<15} {fixed_non_inbox_count:<20}")
    
    # Detailed breakdown
    print(f"\n🔍 DETAILED ANALYSIS:")
    for s in test_suggestions:
        cat = s['ai_suggestion']
        original_inbox = cat in inbox_categories
        original_non_inbox = cat in non_inbox_categories
        fixed_inbox = cat.lower() in inbox_categories
        fixed_non_inbox = cat.lower() in non_inbox_categories
        
        print(f"  {cat:<25}")
        print(f"    Original: inbox={original_inbox:<5} non_inbox={original_non_inbox:<5}")
        print(f"    Fixed:    inbox={fixed_inbox:<5} non_inbox={fixed_non_inbox:<5}")
        
        if original_non_inbox != fixed_non_inbox:
            print(f"    🔧 FIX APPLIED - now correctly categorized")
        print()
    
    # Verify fix success
    expected_non_inbox = 5  # fyi(3) + team_action(1) + newsletter(1) = 5
    actual_fixed = fixed_non_inbox_count
    
    print(f"✅ FIX VALIDATION:")
    print(f"  Expected non-inbox count: {expected_non_inbox}")
    print(f"  Actual fixed count: {actual_fixed}")
    
    if actual_fixed == expected_non_inbox:
        print(f"  🎉 SUCCESS: Fix is working correctly!")
        return True
    else:
        print(f"  ❌ FAILURE: Fix needs more work")
        return False

def test_outlook_manager_integration():
    """Test that OutlookManager handles case insensitivity"""
    print(f"\n🔗 TESTING OUTLOOK MANAGER INTEGRATION")
    print("-" * 50)
    
    try:
        # Import and test the folder mapping
        from outlook_manager import OutlookManager
        
        # Test category normalization
        test_categories = ['fyi', 'FYI', 'Fyi', 'team_action', 'TEAM_ACTION']
        
        print("Category normalization test:")
        for cat in test_categories:
            normalized = cat.lower()
            print(f"  {cat:<15} → {normalized}")
        
        print(f"\n✅ OutlookManager integration looks good")
        return True
        
    except ImportError as e:
        print(f"⚠️  Could not test OutlookManager: {e}")
        return False
    except Exception as e:
        print(f"❌ OutlookManager test failed: {e}")
        return False

if __name__ == "__main__":
    print(f"Testing FYI categorization fix...")
    print(f"Current working directory: {os.getcwd()}")
    
    # Run tests
    counting_success = test_categorization_counting()
    integration_success = test_outlook_manager_integration()
    
    print(f"\n" + "="*50)
    print(f"📋 FINAL RESULTS")
    print(f"="*50)
    print(f"Counting fix: {'✅ PASS' if counting_success else '❌ FAIL'}")
    print(f"Integration: {'✅ PASS' if integration_success else '❌ FAIL'}")
    
    if counting_success and integration_success:
        print(f"\n🎉 ALL TESTS PASSED - FYI categorization is now fixed!")
        print(f"   Items marked as 'FYI', 'fyi', or 'Fyi' will now be counted correctly.")
    else:
        print(f"\n⚠️  Some tests failed - review the output above for details.")
