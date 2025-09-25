#!/usr/bin/env python3
"""
Test Suite for Task History - Block 4 Implementation

Tests for the new TaskPersistence methods:
- record_task_resolution()
- get_resolution_history()
"""

import sys
import os
import tempfile
import shutil
import json
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

try:
    from task_persistence import TaskPersistence
    
    def test_record_task_resolution():
        """Test record_task_resolution method"""
        print("🧪 Testing record_task_resolution()...")
        
        test_dir = tempfile.mkdtemp(prefix="task_resolution_test_")
        
        try:
            persistence = TaskPersistence(test_dir)
            
            # Create a test task first
            test_task = {
                'task_id': 'test_task_001',
                'description': 'Test task for resolution',
                'sender': 'test@example.com',
                'priority': 'high',
                'first_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '_entry_ids': ['entry001']
            }
            
            persistence.save_outstanding_tasks({
                'required_actions': [test_task],
                'team_actions': [],
                'completed_team_actions': [],
                'optional_actions': [],
                'job_listings': [],
                'optional_events': [],
                'fyi_notices': [],
                'newsletters': []
            })
            
            # Test recording resolution
            result = persistence.record_task_resolution(
                'test_task_001',
                'completed',
                'Task completed successfully'
            )
            
            assert result == True
            
            # Verify history file was created
            history_dir = os.path.join(test_dir, 'task_history')
            assert os.path.exists(history_dir)
            
            current_month = datetime.now().strftime('%Y_%m')
            history_file = os.path.join(history_dir, f'task_resolutions_{current_month}.jsonl')
            assert os.path.exists(history_file)
            
            # Verify file content
            with open(history_file, 'r') as f:
                entry = json.loads(f.readline().strip())
                assert entry['task_id'] == 'test_task_001'
                assert entry['resolution_type'] == 'completed'
                assert entry['resolution_notes'] == 'Task completed successfully'
            
            print("  ✅ record_task_resolution() works correctly")
            return True
            
        finally:
            shutil.rmtree(test_dir)
    
    def test_get_resolution_history():
        """Test get_resolution_history method"""
        print("🧪 Testing get_resolution_history()...")
        
        test_dir = tempfile.mkdtemp(prefix="history_test_")
        
        try:
            persistence = TaskPersistence(test_dir)
            
            # Test with no data
            history = persistence.get_resolution_history()
            assert history['total_count'] == 0
            assert history['resolutions'] == []
            
            # Create test resolutions
            test_tasks = [
                ('task_001', 'completed', 'First task'),
                ('task_002', 'dismissed', 'Second task'),
                ('task_003', 'completed', 'Third task')
            ]
            
            for task_id, res_type, description in test_tasks:
                # Create outstanding task
                test_task = {
                    'task_id': task_id,
                    'description': description,
                    'sender': 'test@example.com',
                    'first_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '_entry_ids': [f'entry_{task_id}']
                }
                
                persistence.save_outstanding_tasks({
                    'required_actions': [test_task],
                    'team_actions': [], 'completed_team_actions': [],
                    'optional_actions': [], 'job_listings': [],
                    'optional_events': [], 'fyi_notices': [], 'newsletters': []
                })
                
                # Record resolution
                persistence.record_task_resolution(task_id, res_type, f'{description} resolution')
            
            # Test retrieving all history
            history = persistence.get_resolution_history(include_stats=True)
            assert history['total_count'] == 3
            assert len(history['resolutions']) == 3
            
            # Test statistics
            stats = history.get('statistics', {})
            assert 'completion_rate' in stats
            assert 'resolution_type_distribution' in stats
            
            completion_rate = stats['completion_rate']
            assert completion_rate['completed'] == 2
            assert completion_rate['dismissed'] == 1
            
            # Test filtering by resolution type
            completed_history = persistence.get_resolution_history(resolution_type='completed')
            assert completed_history['total_count'] == 2
            
            print("  ✅ get_resolution_history() works correctly")
            return True
            
        finally:
            shutil.rmtree(test_dir)
    
    def test_resolution_statistics():
        """Test resolution statistics calculation"""
        print("🧪 Testing resolution statistics...")
        
        test_dir = tempfile.mkdtemp(prefix="stats_test_")
        
        try:
            persistence = TaskPersistence(test_dir)
            
            # Create resolutions with varying ages
            resolutions = [
                ('old_task', 'completed', 'Old completed task', 10),
                ('new_task', 'completed', 'New completed task', 1),
                ('dismissed_task', 'dismissed', 'Dismissed task', 5)
            ]
            
            # Create all tasks first
            all_tasks = []
            for task_id, res_type, description, age_days in resolutions:
                # Create task with specific age
                first_seen = (datetime.now() - timedelta(days=age_days)).strftime('%Y-%m-%d %H:%M:%S')
                test_task = {
                    'task_id': task_id,
                    'description': description,
                    'sender': 'test@example.com',
                    'first_seen': first_seen,
                    '_entry_ids': [f'entry_{task_id}']
                }
                all_tasks.append(test_task)
            
            # Save all tasks at once
            persistence.save_outstanding_tasks({
                'required_actions': all_tasks,
                'team_actions': [], 'completed_team_actions': [],
                'optional_actions': [], 'job_listings': [],
                'optional_events': [], 'fyi_notices': [], 'newsletters': []
            })
            
            # Now resolve each task
            for task_id, res_type, description, age_days in resolutions:
                persistence.record_task_resolution(task_id, res_type, f'{description} resolution')
            
            # Get statistics
            history = persistence.get_resolution_history(include_stats=True)
            stats = history['statistics']
            
            # Test age statistics
            age_stats = stats['age_statistics']
            assert age_stats['total_tasks'] == 3
            assert age_stats['average_age_days'] > 0
            assert age_stats['max_age_days'] >= age_stats['min_age_days']
            
            # Test resolution type distribution
            type_dist = stats['resolution_type_distribution']
            assert type_dist['completed'] == 2
            assert type_dist['dismissed'] == 1
            
            print("  ✅ Resolution statistics calculation works correctly")
            return True
            
        finally:
            shutil.rmtree(test_dir)
    
    def test_integration_with_task_persistence():
        """Test integration with existing task persistence functionality"""
        print("🧪 Testing integration with existing TaskPersistence...")
        
        test_dir = tempfile.mkdtemp(prefix="integration_test_")
        
        try:
            persistence = TaskPersistence(test_dir)
            
            # Create a task through existing flow
            test_task = {
                'task_id': 'integration_task',
                'description': 'Integration test task',
                'sender': 'integration@example.com',
                'first_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '_entry_ids': ['integration_entry']
            }
            
            persistence.save_outstanding_tasks({
                'required_actions': [test_task],
                'team_actions': [], 'completed_team_actions': [],
                'optional_actions': [], 'job_listings': [],
                'optional_events': [], 'fyi_notices': [], 'newsletters': []
            })
            
            # Record resolution BEFORE marking as completed (proper workflow)
            result = persistence.record_task_resolution(
                'integration_task',
                'completed',
                'Completed through integration test'
            )
            
            assert result == True  # Resolution recording should succeed
            
            # Now the task should be in resolution history
            resolution_history = persistence.get_resolution_history()
            assert resolution_history['total_count'] > 0
            
            # And also in completed tasks (done by record_task_resolution)
            completed_tasks = persistence.load_completed_tasks()
            assert len(completed_tasks) > 0
            
            print("  ✅ Integration with existing functionality works")
            return True
            
        finally:
            shutil.rmtree(test_dir)
    
    def main():
        print("🚀 TASK HISTORY TESTS")
        print("=" * 40)
        
        tests = [
            test_record_task_resolution,
            test_get_resolution_history,
            test_resolution_statistics,
            test_integration_with_task_persistence
        ]
        
        passed = 0
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"  ❌ {test.__name__} failed: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
        
        if passed == len(tests):
            print("🎉 ALL TASK HISTORY TESTS PASSED!")
        else:
            print("⚠️ Some tests failed")
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()