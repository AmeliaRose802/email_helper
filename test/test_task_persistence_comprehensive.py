#!/usr/bin/env python3
"""Comprehensive tests for TaskPersistence module.

Tests cover:
- Task storage and retrieval
- Task deduplication and merging
- Task completion tracking
- Event expiration handling
- Resolution history tracking
- Edge cases and error handling
"""

import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from backend.core.domain.task_persistence import TaskPersistence


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def task_persistence(temp_storage_dir):
    """Create TaskPersistence instance with temp storage."""
    return TaskPersistence(storage_dir=temp_storage_dir)


@pytest.fixture
def sample_tasks():
    """Sample tasks for testing."""
    return {
        'required_actions': [
            {
                'subject': 'Review PR #123',
                'sender': 'developer@company.com',
                'action_required': 'Review and approve pull request',
                'due_date': '2025-01-20',
                'priority': 'high',
                '_entry_id': 'email_001'
            }
        ],
        'team_actions': [
            {
                'subject': 'Team standup notes',
                'sender': 'scrum@company.com',
                'action_required': 'Update ticket status',
                '_entry_id': 'email_002'
            }
        ],
        'optional_events': [
            {
                'subject': 'Company holiday party',
                'sender': 'hr@company.com',
                'date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
                '_entry_id': 'email_003'
            }
        ]
    }


class TestTaskPersistenceBasics:
    """Test basic task persistence operations."""
    
    def test_initialization(self, task_persistence, temp_storage_dir):
        """Test TaskPersistence initialization."""
        assert task_persistence.storage_dir == temp_storage_dir
        assert os.path.exists(temp_storage_dir)
        assert task_persistence.tasks_file == os.path.join(temp_storage_dir, 'outstanding_tasks.json')
        assert task_persistence.completed_file == os.path.join(temp_storage_dir, 'completed_tasks.json')
    
    def test_default_storage_directory(self):
        """Test default storage directory creation."""
        tp = TaskPersistence()
        assert 'runtime_data' in tp.storage_dir
        assert 'tasks' in tp.storage_dir
    
    def test_save_and_load_outstanding_tasks(self, task_persistence, sample_tasks):
        """Test saving and loading outstanding tasks."""
        task_persistence.save_outstanding_tasks(sample_tasks)
        
        loaded = task_persistence.load_outstanding_tasks()
        
        assert len(loaded['required_actions']) == 1
        assert len(loaded['team_actions']) == 1
        assert len(loaded['optional_events']) == 1
        assert loaded['required_actions'][0]['subject'] == 'Review PR #123'
    
    def test_empty_load_returns_empty_structure(self, task_persistence):
        """Test loading tasks when file doesn't exist."""
        loaded = task_persistence.load_outstanding_tasks()
        
        assert isinstance(loaded, dict)
        assert loaded['required_actions'] == []
        assert loaded['team_actions'] == []
        assert loaded['optional_events'] == []


class TestTaskDeduplication:
    """Test task deduplication and merging logic."""
    
    def test_duplicate_task_not_added_twice(self, task_persistence, sample_tasks):
        """Test that duplicate tasks are merged, not added twice."""
        # Save tasks first time
        task_persistence.save_outstanding_tasks(sample_tasks)
        
        # Save same tasks again
        task_persistence.save_outstanding_tasks(sample_tasks)
        
        loaded = task_persistence.load_outstanding_tasks()
        
        # Should still have only 1 of each task, not 2
        assert len(loaded['required_actions']) == 1
        assert len(loaded['team_actions']) == 1
        
        # Batch count should be incremented
        assert loaded['required_actions'][0]['batch_count'] == 2
    
    def test_entry_ids_merged_for_duplicates(self, task_persistence):
        """Test that entry IDs are merged when tasks are duplicated."""
        # First batch with one entry ID
        tasks1 = {
            'required_actions': [{
                'subject': 'Review document',
                'sender': 'boss@company.com',
                'action_required': 'Review',
                '_entry_id': 'email_001'
            }]
        }
        task_persistence.save_outstanding_tasks(tasks1)
        
        # Second batch with different entry ID but same task
        tasks2 = {
            'required_actions': [{
                'subject': 'Review document',
                'sender': 'boss@company.com',
                'action_required': 'Review',
                '_entry_id': 'email_002'
            }]
        }
        task_persistence.save_outstanding_tasks(tasks2)
        
        loaded = task_persistence.load_outstanding_tasks()
        
        # Should have both entry IDs
        assert len(loaded['required_actions']) == 1
        assert len(loaded['required_actions'][0]['_entry_ids']) == 2
        assert 'email_001' in loaded['required_actions'][0]['_entry_ids']
        assert 'email_002' in loaded['required_actions'][0]['_entry_ids']
    
    def test_task_id_generation(self, task_persistence):
        """Test task ID generation for deduplication."""
        task1 = {
            'subject': 'Test Subject',
            'sender': 'test@example.com',
            'action_required': 'Do something'
        }
        task2 = {
            'subject': 'Test Subject',
            'sender': 'test@example.com',
            'action_required': 'Do something'
        }
        
        id1 = task_persistence._generate_task_id(task1)
        id2 = task_persistence._generate_task_id(task2)
        
        # Same content should generate same ID
        assert id1 == id2
        assert isinstance(id1, str)
        assert len(id1) > 0


class TestTaskCompletion:
    """Test task completion tracking."""
    
    def test_mark_tasks_completed(self, task_persistence, sample_tasks):
        """Test marking tasks as completed."""
        task_persistence.save_outstanding_tasks(sample_tasks)
        
        loaded = task_persistence.load_outstanding_tasks()
        task_id = loaded['required_actions'][0]['task_id']
        
        task_persistence.mark_tasks_completed([task_id])
        
        # Task should be removed from outstanding
        loaded_after = task_persistence.load_outstanding_tasks()
        assert len(loaded_after['required_actions']) == 0
        
        # Task should be in completed
        completed = task_persistence.load_completed_tasks()
        assert len(completed) == 1
        assert completed[0]['task_id'] == task_id
        assert completed[0]['status'] == 'completed'
    
    def test_get_entry_ids_for_tasks(self, task_persistence, sample_tasks):
        """Test retrieving entry IDs for specific tasks."""
        task_persistence.save_outstanding_tasks(sample_tasks)
        
        loaded = task_persistence.load_outstanding_tasks()
        task_ids = [task['task_id'] for task in loaded['required_actions']]
        
        entry_ids = task_persistence.get_entry_ids_for_tasks(task_ids)
        
        assert 'email_001' in entry_ids
    
    def test_load_completed_tasks_empty(self, task_persistence):
        """Test loading completed tasks when file doesn't exist."""
        completed = task_persistence.load_completed_tasks()
        
        assert isinstance(completed, list)
        assert len(completed) == 0


class TestEventExpiration:
    """Test optional event expiration handling."""
    
    def test_expired_events_auto_removed(self, task_persistence):
        """Test that expired events are automatically removed on load."""
        # Create event in the past
        tasks = {
            'optional_events': [{
                'subject': 'Past event',
                'sender': 'organizer@company.com',
                'date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
                '_entry_id': 'email_expired'
            }]
        }
        task_persistence.save_outstanding_tasks(tasks)
        
        # Load with auto_clean_expired=True (default)
        loaded = task_persistence.load_outstanding_tasks(auto_clean_expired=True)
        
        # Expired event should be removed
        assert len(loaded['optional_events']) == 0
    
    def test_future_events_not_removed(self, task_persistence):
        """Test that future events are not removed."""
        tasks = {
            'optional_events': [{
                'subject': 'Future event',
                'sender': 'organizer@company.com',
                'date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
                '_entry_id': 'email_future'
            }]
        }
        task_persistence.save_outstanding_tasks(tasks)
        
        loaded = task_persistence.load_outstanding_tasks(auto_clean_expired=True)
        
        assert len(loaded['optional_events']) == 1
    
    def test_events_without_date_not_removed(self, task_persistence):
        """Test that events without dates are not removed."""
        tasks = {
            'optional_events': [{
                'subject': 'Event without date',
                'sender': 'organizer@company.com',
                '_entry_id': 'email_no_date'
            }]
        }
        task_persistence.save_outstanding_tasks(tasks)
        
        loaded = task_persistence.load_outstanding_tasks(auto_clean_expired=True)
        
        assert len(loaded['optional_events']) == 1


class TestResolutionHistory:
    """Test task resolution history tracking."""
    
    def test_record_task_resolution(self, task_persistence, sample_tasks):
        """Test recording task resolution with history."""
        task_persistence.save_outstanding_tasks(sample_tasks)
        
        loaded = task_persistence.load_outstanding_tasks()
        task_id = loaded['required_actions'][0]['task_id']
        
        result = task_persistence.record_task_resolution(
            task_id=task_id,
            resolution_type='completed',
            resolution_notes='Finished review'
        )
        
        assert result is True
        
        # Check history directory was created
        history_dir = os.path.join(task_persistence.storage_dir, 'task_history')
        assert os.path.exists(history_dir)
        
        # Check resolution was recorded
        history = task_persistence.get_resolution_history(days_back=1)
        assert history['total_count'] == 1
        assert history['resolutions'][0]['resolution_type'] == 'completed'
        assert history['resolutions'][0]['resolution_notes'] == 'Finished review'
    
    def test_resolution_history_filtering(self, task_persistence, sample_tasks):
        """Test filtering resolution history by type."""
        task_persistence.save_outstanding_tasks(sample_tasks)
        loaded = task_persistence.load_outstanding_tasks()
        
        # Record multiple resolutions
        task_persistence.record_task_resolution(
            loaded['required_actions'][0]['task_id'],
            'completed'
        )
        task_persistence.record_task_resolution(
            loaded['team_actions'][0]['task_id'],
            'dismissed'
        )
        
        # Filter by type
        completed_history = task_persistence.get_resolution_history(
            days_back=1,
            resolution_type='completed'
        )
        
        assert completed_history['total_count'] == 1
        assert completed_history['resolutions'][0]['resolution_type'] == 'completed'
    
    def test_resolution_statistics(self, task_persistence, sample_tasks):
        """Test resolution statistics calculation."""
        task_persistence.save_outstanding_tasks(sample_tasks)
        loaded = task_persistence.load_outstanding_tasks()
        
        task_persistence.record_task_resolution(
            loaded['required_actions'][0]['task_id'],
            'completed'
        )
        
        history = task_persistence.get_resolution_history(days_back=1, include_stats=True)
        
        assert 'statistics' in history
        assert 'resolution_type_distribution' in history['statistics']
        assert 'age_statistics' in history['statistics']
        assert history['statistics']['resolution_type_distribution']['completed'] == 1


class TestTaskStatistics:
    """Test task statistics and reporting."""
    
    def test_get_task_statistics(self, task_persistence, sample_tasks):
        """Test getting task statistics."""
        task_persistence.save_outstanding_tasks(sample_tasks)
        
        stats = task_persistence.get_task_statistics()
        
        assert stats['outstanding_total'] == 3  # 1 required + 1 team + 1 optional
        assert stats['completed_total'] == 0
        assert 'sections_breakdown' in stats
        assert stats['sections_breakdown']['required_actions'] == 1
    
    def test_cleanup_old_completed_tasks(self, task_persistence, sample_tasks):
        """Test cleaning up old completed tasks."""
        task_persistence.save_outstanding_tasks(sample_tasks)
        
        loaded = task_persistence.load_outstanding_tasks()
        task_id = loaded['required_actions'][0]['task_id']
        
        # Complete a task with old timestamp
        old_timestamp = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d %H:%M:%S')
        task_persistence.mark_tasks_completed([task_id], completion_timestamp=old_timestamp)
        
        # Clean up tasks older than 30 days
        task_persistence.cleanup_old_completed_tasks(days_to_keep=30)
        
        completed = task_persistence.load_completed_tasks()
        assert len(completed) == 0  # Old task should be removed


class TestComprehensiveSummary:
    """Test comprehensive summary generation."""
    
    def test_get_comprehensive_summary(self, task_persistence, sample_tasks):
        """Test generating comprehensive summary combining old and new tasks."""
        # Save initial tasks
        task_persistence.save_outstanding_tasks(sample_tasks)
        
        # Create new batch with different tasks
        new_tasks = {
            'required_actions': [{
                'subject': 'New urgent task',
                'sender': 'boss@company.com',
                'action_required': 'Complete immediately',
                '_entry_id': 'email_004'
            }]
        }
        
        summary = task_persistence.get_comprehensive_summary(new_tasks)
        
        # Should have both old and new tasks
        assert len(summary['required_actions']) == 2
        assert len(summary['team_actions']) == 1
    
    def test_comprehensive_summary_deduplication(self, task_persistence, sample_tasks):
        """Test that comprehensive summary deduplicates tasks."""
        task_persistence.save_outstanding_tasks(sample_tasks)
        
        # Pass same tasks as "current" batch
        summary = task_persistence.get_comprehensive_summary(sample_tasks)
        
        # Should not have duplicates
        assert len(summary['required_actions']) == 1
        assert len(summary['team_actions']) == 1


class TestClearOperations:
    """Test clearing FYI and newsletter items."""
    
    def test_clear_fyi_items(self, task_persistence):
        """Test clearing FYI items."""
        tasks = {
            'fyi_notices': [{
                'subject': 'FYI: Update',
                'sender': 'info@company.com',
                '_entry_id': 'email_fyi'
            }]
        }
        task_persistence.save_outstanding_tasks(tasks)
        
        cleared_count = task_persistence.clear_fyi_items()
        
        assert cleared_count == 1
        
        loaded = task_persistence.load_outstanding_tasks()
        assert len(loaded['fyi_notices']) == 0
    
    def test_clear_newsletter_items(self, task_persistence):
        """Test clearing newsletter items."""
        tasks = {
            'newsletters': [{
                'subject': 'Weekly Newsletter',
                'sender': 'news@company.com',
                '_entry_id': 'email_newsletter'
            }]
        }
        task_persistence.save_outstanding_tasks(tasks)
        
        cleared_count = task_persistence.clear_newsletter_items()
        
        assert cleared_count == 1
        
        loaded = task_persistence.load_outstanding_tasks()
        assert len(loaded['newsletters']) == 0
    
    def test_clear_both_fyi_and_newsletters(self, task_persistence):
        """Test clearing both FYI and newsletters."""
        tasks = {
            'fyi_notices': [{'subject': 'FYI', 'sender': 'a@b.com', '_entry_id': 'e1'}],
            'newsletters': [{'subject': 'News', 'sender': 'c@d.com', '_entry_id': 'e2'}]
        }
        task_persistence.save_outstanding_tasks(tasks)
        
        fyi_count, newsletter_count = task_persistence.clear_both_fyi_and_newsletters()
        
        assert fyi_count == 1
        assert newsletter_count == 1
        
        loaded = task_persistence.load_outstanding_tasks()
        assert len(loaded['fyi_notices']) == 0
        assert len(loaded['newsletters']) == 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_invalid_task_data_handled(self, task_persistence):
        """Test handling of invalid task data."""
        # Save tasks with missing fields
        tasks = {
            'required_actions': [
                {'subject': 'Valid task', 'sender': 'a@b.com', '_entry_id': 'e1'},
                {'subject': 'Invalid'},  # Missing sender and _entry_id
            ]
        }
        
        # Should not crash
        task_persistence.save_outstanding_tasks(tasks)
        loaded = task_persistence.load_outstanding_tasks()
        
        # Both tasks should be loaded (missing fields get defaults)
        assert len(loaded['required_actions']) == 2
    
    def test_corrupted_json_file(self, task_persistence, temp_storage_dir):
        """Test handling of corrupted JSON file."""
        # Write corrupted JSON
        with open(task_persistence.tasks_file, 'w') as f:
            f.write('{ corrupted json content [[[')
        
        # Should return empty structure without crashing
        loaded = task_persistence.load_outstanding_tasks()
        assert isinstance(loaded, dict)
        assert loaded['required_actions'] == []
    
    def test_task_age_calculation(self, task_persistence):
        """Test task age calculation."""
        task_data = {
            'first_seen': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        age = task_persistence._calculate_task_age(task_data)
        
        assert age == 5
    
    def test_task_age_same_day(self, task_persistence):
        """Test task age calculation for same-day tasks."""
        task_data = {
            'first_seen': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        age = task_persistence._calculate_task_age(task_data)
        
        assert age == 1  # Should round up to 1 day


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
