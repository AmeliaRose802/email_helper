#!/usr/bin/env python3
"""Task Persistence for Email Helper - Unified Task Management Interface.

This module provides a unified interface for task persistence functionality,
delegating to specialized modules for specific operations.

Architecture:
- TaskStorage: Low-level file I/O and data persistence
- TaskLifecycle: Task completion, expiration, and resolution tracking  
- TaskDeduplication: Task merging and ID generation
- TaskQueries: Task retrieval, filtering, and statistics

This facade pattern maintains backward compatibility while providing
a cleaner, more maintainable internal structure.
"""

from datetime import datetime
from typing import Dict, List, Any

from .task_storage import TaskStorage
from .task_lifecycle import TaskLifecycle
from .task_deduplication import TaskDeduplication
from .task_queries import TaskQueries


class TaskPersistence:
    """Task persistence facade providing unified task management interface.
    
    This class maintains backward compatibility while delegating to specialized
    modules for improved maintainability and testability.
    """
    
    def __init__(self, storage_dir: str = None):
        """Initialize task persistence with storage directory.
        
        Args:
            storage_dir: Directory for task storage files.
        """
        self.storage = TaskStorage(storage_dir)
        self.lifecycle = TaskLifecycle(self.storage)
        self.deduplication = TaskDeduplication()
        self.queries = TaskQueries(self.storage, self.lifecycle)
        
        # Expose storage paths for backward compatibility
        self.storage_dir = self.storage.storage_dir
        self.tasks_file = self.storage.tasks_file
        self.completed_file = self.storage.completed_file
    
    def save_outstanding_tasks(self, summary_sections: Dict[str, List[Dict]], batch_timestamp: str = None) -> None:
        """Save outstanding tasks from current batch, merging with existing ones."""
        if batch_timestamp is None:
            batch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        existing_tasks = self.load_outstanding_tasks()
        
        current_tasks = {
            'required_actions': [], 'team_actions': [], 'completed_team_actions': [],
            'optional_actions': [], 'job_listings': [], 'optional_events': [],
            'fyi_notices': [], 'newsletters': []
        }
        
        for section_key in current_tasks.keys():
            if section_key in summary_sections:
                for task in summary_sections[section_key]:
                    task_with_metadata = task.copy()
                    
                    existing_task_id = task.get('task_id')
                    generated_task_id = existing_task_id if existing_task_id else self.deduplication.generate_task_id(task)
                    
                    task_with_metadata.update({
                        'batch_timestamp': batch_timestamp,
                        'first_seen': batch_timestamp,
                        'task_id': generated_task_id,
                        'status': 'outstanding',
                        'batch_count': 1
                    })
                    
                    if '_entry_id' in task_with_metadata and task_with_metadata['_entry_id']:
                        entry_id = task_with_metadata['_entry_id']
                        task_with_metadata['_entry_ids'] = [entry_id]
                        del task_with_metadata['_entry_id']
                    elif '_entry_ids' not in task_with_metadata:
                        task_with_metadata['_entry_ids'] = []
                    
                    current_tasks[section_key].append(task_with_metadata)
        
        merged_tasks = self.deduplication.merge_task_lists(existing_tasks, current_tasks, batch_timestamp)
        self.storage.save_outstanding_tasks_data(merged_tasks, batch_timestamp)
        
        print(f"💾 Saved {self.queries._count_total_tasks(merged_tasks)} outstanding tasks to persistent storage")
    
    def load_outstanding_tasks(self, auto_clean_expired=True) -> Dict[str, List[Dict]]:
        """Load outstanding tasks from persistent storage with optional cleaning."""
        tasks = self.storage.load_outstanding_tasks_raw()
        
        if not auto_clean_expired:
            return tasks
        
        cleaned_tasks = {}
        expired_events_count = 0
        auto_completed_actions_count = 0
        
        for section_key, task_list in tasks.items():
            cleaned_tasks[section_key] = []
            if not isinstance(task_list, list):
                print(f"Warning: {section_key} is not a list, skipping")
                continue
            
            for task in task_list:
                if not isinstance(task, dict) or 'task_id' not in task:
                    if isinstance(task, dict):
                        print(f"Warning: Task missing task_id: {task}")
                    else:
                        print(f"Warning: Invalid task format (not a dict): {task}")
                    continue
                
                if section_key == 'optional_events' and self.lifecycle.is_event_expired(task):
                    expired_events_count += 1
                    print(f"🗑️ Auto-removing expired event: {task.get('subject', 'Unknown')}")
                    continue
                
                if section_key == 'team_actions' and task.get('completion_status') == 'completed':
                    auto_completed_actions_count += 1
                    print(f"✅ Auto-moving completed team action: {task.get('subject', 'Unknown')}")
                    if 'completed_team_actions' not in cleaned_tasks:
                        cleaned_tasks['completed_team_actions'] = []
                    cleaned_tasks['completed_team_actions'].append(task)
                    continue
                
                if 'sender' not in task and 'email_sender' in task:
                    task['sender'] = task['email_sender']
                elif 'sender' not in task:
                    task['sender'] = 'Unknown'
                
                cleaned_tasks[section_key].append(task)
        
        if expired_events_count > 0 or auto_completed_actions_count > 0:
            if expired_events_count > 0:
                print(f"✅ Removed {expired_events_count} expired optional events")
            if auto_completed_actions_count > 0:
                print(f"✅ Moved {auto_completed_actions_count} completed team actions to completed section")
            self.storage.save_outstanding_tasks_data(cleaned_tasks)
        
        return cleaned_tasks
    
    def mark_tasks_completed(self, completed_task_ids: List[str], completion_timestamp: str = None) -> None:
        """Mark specific tasks as completed and move them to completed tasks file."""
        self.lifecycle.mark_tasks_completed(completed_task_ids, completion_timestamp)
    
    def get_entry_ids_for_tasks(self, task_ids: List[str]) -> List[str]:
        """Get all email EntryIDs associated with the specified task IDs."""
        return self.queries.get_entry_ids_for_tasks(task_ids)
    
    def get_comprehensive_summary(self, current_summary_sections: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Get comprehensive summary combining current batch with outstanding tasks from previous batches."""
        outstanding_tasks = self.load_outstanding_tasks()
        return self.deduplication.get_comprehensive_summary(current_summary_sections, outstanding_tasks)
    
    def load_completed_tasks(self) -> List[Dict]:
        """Load completed tasks from persistent storage."""
        return self.storage.load_completed_tasks()
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get statistics about tasks."""
        return self.queries.get_task_statistics()
    
    def cleanup_old_completed_tasks(self, days_to_keep: int = 30) -> None:
        """Clean up completed tasks older than specified days."""
        self.lifecycle.cleanup_old_completed_tasks(days_to_keep)
    
    def clear_fyi_items(self) -> int:
        """Clear all FYI items from persistent storage."""
        return self.queries.clear_fyi_items()
    
    def clear_newsletter_items(self) -> int:
        """Clear all newsletter items from persistent storage."""
        return self.queries.clear_newsletter_items()
    
    def clear_optional_events(self) -> int:
        """Clear all optional event items from persistent storage."""
        return self.queries.clear_optional_events()
    
    def clear_both_fyi_and_newsletters(self) -> tuple:
        """Clear both FYI and newsletter items from persistent storage."""
        return self.queries.clear_both_fyi_and_newsletters()
    
    def record_task_resolution(self, task_id: str, resolution_type: str, resolution_notes: str = "", 
                              completion_timestamp: str = None) -> bool:
        """Record task resolution with detailed tracking for historical analysis."""
        return self.lifecycle.record_task_resolution(task_id, resolution_type, resolution_notes, completion_timestamp)
    
    def get_resolution_history(self, days_back: int = 30, resolution_type: str = None, 
                               include_stats: bool = True) -> Dict[str, Any]:
        """Retrieve task resolution history for analysis and reporting."""
        return self.queries.get_resolution_history(days_back, resolution_type, include_stats)
    
    # Private helper methods for backward compatibility
    def _generate_task_id(self, task: Dict) -> str:
        """Generate unique ID for a task based on content."""
        return self.deduplication.generate_task_id(task)
    
    def _merge_task_lists(self, existing_tasks: Dict, current_tasks: Dict, batch_timestamp: str) -> Dict:
        """Merge current batch tasks with existing outstanding tasks."""
        return self.deduplication.merge_task_lists(existing_tasks, current_tasks, batch_timestamp)
    
    def _count_total_tasks(self, tasks_dict: Dict) -> int:
        """Count total tasks across all sections."""
        return self.queries._count_total_tasks(tasks_dict)
    
    def _sort_tasks_by_priority(self, summary_sections: Dict) -> None:
        """Sort tasks within each section by priority and due date."""
        self.deduplication._sort_tasks_by_priority(summary_sections)
    
    def _save_tasks_to_file(self, filepath: str, data: Any) -> None:
        """Save data to JSON file."""
        self.storage.save_to_file(filepath, data)
    
    def _is_event_expired(self, event: Dict) -> bool:
        """Check if an optional event has passed its date."""
        return self.lifecycle.is_event_expired(event)
    
    def _calculate_task_age(self, task_data: Dict) -> int:
        """Calculate age of task in days."""
        return self.lifecycle._calculate_task_age(task_data)
    
    def _calculate_resolution_statistics(self, resolutions: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive statistics from resolution data."""
        return self.queries._calculate_resolution_statistics(resolutions)
