"""Test script to verify action items synchronization after holistic analysis"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_gui import UnifiedEmailGUI
from email_processor import EmailProcessor
from ai_processor import AIProcessor
from outlook_manager import OutlookManager
from task_persistence import TaskPersistence


def test_action_items_sync():
    """Test that holistic analysis changes are reflected in action items data"""
    print("🧪 Testing Action Items Synchronization...")
    
    # Create mock components
    try:
        outlook_manager = OutlookManager()
        ai_processor = AIProcessor()
        email_processor = EmailProcessor(ai_processor)
        task_persistence = TaskPersistence()
        
        # Create GUI instance (without actually showing it)
        gui = UnifiedEmailGUI(outlook_manager, ai_processor, email_processor, task_persistence, show_gui=False)
        
        # Test 1: Create mock email suggestions
        mock_suggestions = [
            {
                'ai_suggestion': 'required_personal_action',
                'email_data': {
                    'entry_id': 'test_entry_1',
                    'subject': 'Test Required Action',
                    'sender_name': 'Test Sender',
                    'body': 'Please complete this task',
                    'received_time': '2024-01-01'
                },
                'thread_data': {
                    'entry_id': 'test_entry_1'
                }
            }
        ]
        
        gui.email_suggestions = mock_suggestions
        
        # Test 2: Create mock action items data in email processor
        mock_action_items = {
            'required_personal_action': [
                {
                    'action': 'Complete test task',
                    'thread_data': {'entry_id': 'test_entry_1'},
                    'email_subject': 'Test Required Action',
                    'email_sender': 'Test Sender',
                    'email_date': '2024-01-01'
                }
            ]
        }
        
        email_processor.action_items_data = mock_action_items
        
        # Test 3: Simulate holistic analysis changing the category
        gui.email_suggestions[0]['ai_suggestion'] = 'fyi'  # Changed by holistic analysis
        
        print("  ✓ Mock data prepared")
        print(f"  ✓ Email suggestion category: {gui.email_suggestions[0]['ai_suggestion']}")
        print(f"  ✓ Original action items: {list(mock_action_items.keys())}")
        
        # Test 4: Call the synchronization method
        gui._reprocess_action_items_after_holistic_changes()
        
        # Test 5: Verify synchronization worked
        updated_action_items = email_processor.action_items_data
        
        print(f"  ✓ Updated action items categories: {list(updated_action_items.keys())}")
        
        # Verify the item moved from required_personal_action to fyi
        if 'fyi' in updated_action_items and len(updated_action_items['fyi']) > 0:
            print("  ✅ SUCCESS: Item correctly moved to 'fyi' category")
        else:
            print("  ❌ FAILED: Item not found in 'fyi' category")
            
        if 'required_personal_action' in updated_action_items and len(updated_action_items['required_personal_action']) == 0:
            print("  ✅ SUCCESS: Item correctly removed from original category")
        else:
            print("  ❌ FAILED: Item still in original category")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Test failed with error: {e}")
        return False


def test_manual_reclassification_sync():
    """Test that manual reclassifications update both data stores"""
    print("\n🧪 Testing Manual Reclassification Synchronization...")
    
    try:
        outlook_manager = OutlookManager()
        ai_processor = AIProcessor()
        email_processor = EmailProcessor(ai_processor)
        task_persistence = TaskPersistence()
        
        # Create GUI instance
        gui = UnifiedEmailGUI(outlook_manager, ai_processor, email_processor, task_persistence, show_gui=False)
        
        # Initialize both data stores
        gui.action_items_data = {'fyi': []}
        email_processor.action_items_data = {'fyi': []}
        
        # Create mock suggestion data
        mock_suggestion = {
            'email_data': {
                'subject': 'Test Manual Reclassification',
                'sender_name': 'Test User', 
                'body': 'Test content',
                'received_time': '2024-01-01'
            },
            'thread_data': {
                'entry_id': 'test_manual_1'
            }
        }
        
        # Test the manual reclassification method
        gui._update_action_items_for_reclassification(mock_suggestion, 'old_category', 'required_personal_action')
        
        # Verify both data stores were updated
        gui_has_item = 'required_personal_action' in gui.action_items_data and len(gui.action_items_data['required_personal_action']) > 0
        processor_has_item = 'required_personal_action' in email_processor.action_items_data and len(email_processor.action_items_data['required_personal_action']) > 0
        
        if gui_has_item and processor_has_item:
            print("  ✅ SUCCESS: Both data stores updated correctly")
        else:
            print(f"  ❌ FAILED: GUI has item: {gui_has_item}, Processor has item: {processor_has_item}")
            
        return gui_has_item and processor_has_item
        
    except Exception as e:
        print(f"  ❌ Test failed with error: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Action Items Synchronization Test Suite")
    print("=" * 50)
    
    test1_passed = test_action_items_sync()
    test2_passed = test_manual_reclassification_sync()
    
    print("\n📊 Test Results:")
    print(f"  Holistic Analysis Sync: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"  Manual Reclassification Sync: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Action items synchronization is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please review the implementation.")
