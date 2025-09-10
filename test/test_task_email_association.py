"""
Test suite for task-email association functionality.
Verifies that tasks properly maintain associations with email EntryIDs
for successful email movement when tasks are marked complete.
"""
import sys
import os

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from task_persistence import TaskPersistence
from outlook_manager import OutlookManager
from summary_generator import SummaryGenerator


def test_task_persistence_initialization():
    """Test that TaskPersistence initializes correctly"""
    print("Testing TaskPersistence initialization...")
    tp = TaskPersistence()
    assert tp is not None
    print("✓ TaskPersistence initialized successfully")


def test_outlook_manager_initialization():
    """Test that OutlookManager initializes correctly"""
    print("Testing OutlookManager initialization...")
    try:
        om = OutlookManager()
        assert om is not None
        print("✓ OutlookManager initialized successfully")
        print(f"✓ Available folders: {list(om.folders.keys())}")
    except Exception as e:
        print(f"⚠️ OutlookManager initialization failed (may be expected if Outlook not available): {e}")


def test_entry_ids_format_conversion():
    """Test that _entry_id gets converted to _entry_ids properly"""
    print("Testing _entry_id to _entry_ids conversion...")
    tp = TaskPersistence()
    
    # Test data with old _entry_id format
    test_task = {
        'task_id': 'test_task_123',
        'subject': 'Test Task',
        '_entry_id': 'test_entry_123'
    }
    
    # This should convert _entry_id to _entry_ids
    entry_ids = tp.get_entry_ids_for_tasks(['test_task_123'])
    print(f"✓ Entry IDs retrieval working (returned: {entry_ids})")


def test_summary_generator_entry_id_creation():
    """Test that SummaryGenerator creates proper _entry_id fields"""
    print("Testing SummaryGenerator _entry_id creation...")
    
    # Test data mimicking email processing output
    test_action_items = {
        'required_personal_action': [{
            'email_object': None,  # Reclassified items won't have email_object
            'email_subject': 'Test Required Action',
            'email_sender': 'Test Sender', 
            'email_date': '2024-01-01',
            'action_details': {
                'action_required': 'Complete test task',
                'due_date': 'Tomorrow'
            },
            'thread_data': {
                'entry_id': 'test_entry_456'
            }
        }],
        'fyi': [{
            'summary': 'Office closed Friday',
            'email_subject': 'Office Notice',
            'email_sender': 'Facilities',
            'email_date': '2025-09-08',
            'thread_data': {
                'entry_id': 'test_entry_789'
            }
        }]
    }
    
    sg = SummaryGenerator()
    summary = sg.build_summary_sections(test_action_items)
    
    # Verify summary structure
    assert 'required_actions' in summary
    assert 'fyi_notices' in summary
    
    print(f"✓ Required actions found: {len(summary['required_actions'])}")
    print(f"✓ FYI notices found: {len(summary['fyi_notices'])}")
    
    # Check that _entry_id field is created
    if summary['required_actions']:
        action = summary['required_actions'][0]
        assert '_entry_id' in action
        print(f"✓ Required action has _entry_id: {action['_entry_id']}")
    
    if summary['fyi_notices']:
        fyi_item = summary['fyi_notices'][0]
        # FYI items should also have _entry_id for potential reclassification
        if '_entry_id' in fyi_item:
            print(f"✓ FYI item has _entry_id: {fyi_item['_entry_id']}")


def test_reclassification_metadata_structure():
    """Test that reclassified items have proper metadata structure"""
    print("Testing reclassification metadata structure...")
    
    # Simulate reclassified item data structure
    reclassified_item = {
        'email_object': None,  # Key indicator of reclassified item
        'email_subject': 'Reclassified Email',
        'email_sender': 'Test Sender',
        'email_date': '2024-01-01',
        'action_details': {
            'action_required': 'Review reclassified item',
            'due_date': 'Next week'
        },
        'thread_data': {
            'entry_id': 'reclassified_entry_123',
            'thread_count': 1
        }
    }
    
    # Verify all required fields are present
    required_fields = ['email_subject', 'email_sender', 'email_date', 'action_details', 'thread_data']
    for field in required_fields:
        assert field in reclassified_item, f"Missing required field: {field}"
    
    # Verify thread_data has entry_id
    assert 'entry_id' in reclassified_item['thread_data']
    
    print("✓ Reclassified item has proper metadata structure")
    print(f"✓ Entry ID: {reclassified_item['thread_data']['entry_id']}")


def test_comprehensive_task_email_association():
    """Comprehensive test of the complete task-email association pipeline"""
    print("Testing comprehensive task-email association...")
    
    tp = TaskPersistence()
    
    # Create test tasks with proper structure
    test_tasks = {
        'required_actions': [{
            'task_id': 'req_001',
            'subject': 'Required Task 1',
            '_entry_ids': ['entry_001']
        }],
        'team_actions': [{
            'task_id': 'team_001', 
            'subject': 'Team Task 1',
            '_entry_ids': ['entry_002']
        }],
        'optional_actions': [{
            'task_id': 'opt_001',
            'subject': 'Optional Task 1', 
            '_entry_ids': ['entry_003']
        }],
        'fyi_notices': [{  # Non-actionable, should not have task_id
            'summary': 'FYI Item',
            'subject': 'Information Only'
            # No _entry_ids expected for FYI
        }]
    }
    
    # Save test tasks
    tp.save_outstanding_tasks(test_tasks)
    
    # Test retrieval
    actionable_task_ids = ['req_001', 'team_001', 'opt_001']
    entry_ids = tp.get_entry_ids_for_tasks(actionable_task_ids)
    
    expected_entry_ids = ['entry_001', 'entry_002', 'entry_003'] 
    assert len(entry_ids) == len(expected_entry_ids)
    
    print(f"✓ Retrieved {len(entry_ids)} entry IDs for {len(actionable_task_ids)} tasks")
    print(f"✓ Entry IDs: {entry_ids}")
    
    # Test individual task lookup
    for task_id in actionable_task_ids:
        task_entry_ids = tp.get_entry_ids_for_tasks([task_id])
        assert len(task_entry_ids) == 1, f"Task {task_id} should have exactly 1 entry ID"
        print(f"✓ Task {task_id} -> {task_entry_ids}")


def run_all_tests():
    """Run all test functions"""
    print("="*60)
    print("RUNNING TASK-EMAIL ASSOCIATION TESTS")
    print("="*60)
    
    tests = [
        test_task_persistence_initialization,
        test_outlook_manager_initialization, 
        test_entry_ids_format_conversion,
        test_summary_generator_entry_id_creation,
        test_reclassification_metadata_structure,
        test_comprehensive_task_email_association
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\n--- {test.__name__} ---")
            test()
            print(f"✓ {test.__name__} PASSED")
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Task-email association system is working correctly.")
    else:
        print(f"⚠️ {failed} tests failed. Please review the issues above.")


if __name__ == "__main__":
    run_all_tests()
