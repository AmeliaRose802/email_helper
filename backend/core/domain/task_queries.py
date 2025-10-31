#!/usr/bin/env python3
"""Task Queries - Task querying and filtering operations."""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any


class TaskQueries:
    """Handles task querying and retrieval operations."""
    
    def __init__(self, storage, lifecycle):
        """Initialize with storage and lifecycle backends.
        
        Args:
            storage: TaskStorage instance for data operations.
            lifecycle: TaskLifecycle instance for age calculations.
        """
        self.storage = storage
        self.lifecycle = lifecycle
    
    def get_entry_ids_for_tasks(self, task_ids: List[str], outstanding_tasks: Dict = None) -> List[str]:
        """Get all email EntryIDs associated with the specified task IDs."""
        if outstanding_tasks is None:
            outstanding_tasks = self.storage.load_outstanding_tasks_raw()
        
        entry_ids = []
        for section_key in outstanding_tasks:
            for task in outstanding_tasks[section_key]:
                if task.get('task_id') in task_ids:
                    task_entry_ids = task.get('_entry_ids', [])
                    entry_ids.extend(task_entry_ids)
        
        return list(set(entry_ids))
    
    def get_task_statistics(self, outstanding_tasks: Dict = None) -> Dict[str, Any]:
        """Get statistics about tasks."""
        if outstanding_tasks is None:
            outstanding_tasks = self.storage.load_outstanding_tasks_raw()
        
        completed_tasks = self.storage.load_completed_tasks()
        
        outstanding_count = self._count_total_tasks(outstanding_tasks)
        completed_count = len(completed_tasks)
        
        old_tasks = []
        current_time = datetime.now()
        
        for section_key in outstanding_tasks:
            for task in outstanding_tasks[section_key]:
                try:
                    first_seen = datetime.strptime(task.get('first_seen', ''), '%Y-%m-%d %H:%M:%S')
                    days_old = (current_time - first_seen).days
                    if days_old >= 7:
                        old_tasks.append({
                            'task': task,
                            'days_old': days_old,
                            'section': section_key
                        })
                except:
                    pass
        
        return {
            'outstanding_total': outstanding_count,
            'completed_total': completed_count,
            'old_tasks_count': len(old_tasks),
            'old_tasks': old_tasks[:5],
            'sections_breakdown': {
                section: len(tasks) for section, tasks in outstanding_tasks.items()
            }
        }
    
    def get_resolution_history(self, days_back: int = 30, resolution_type: str = None, 
                               include_stats: bool = True) -> Dict[str, Any]:
        """Retrieve task resolution history for analysis and reporting."""
        try:
            history_dir = os.path.join(self.storage.storage_dir, 'task_history')
            if not os.path.exists(history_dir):
                return {
                    'resolutions': [],
                    'total_count': 0,
                    'statistics': {} if include_stats else None
                }
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            resolutions = []
            
            for filename in os.listdir(history_dir):
                if filename.startswith('task_resolutions_') and filename.endswith('.jsonl'):
                    file_path = os.path.join(history_dir, filename)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                record = json.loads(line.strip())
                                record_date = datetime.strptime(record['resolution_timestamp'], '%Y-%m-%d %H:%M:%S')
                                
                                if record_date >= cutoff_date:
                                    if resolution_type is None or record['resolution_type'] == resolution_type:
                                        resolutions.append(record)
                                        
                            except (json.JSONDecodeError, ValueError, KeyError) as e:
                                print(f"⚠️ Error parsing resolution record: {e}")
                                continue
            
            resolutions.sort(key=lambda x: x['resolution_timestamp'], reverse=True)
            
            result = {
                'resolutions': resolutions,
                'total_count': len(resolutions),
                'date_range': {
                    'start_date': cutoff_date.strftime('%Y-%m-%d'),
                    'end_date': datetime.now().strftime('%Y-%m-%d'),
                    'days_covered': days_back
                }
            }
            
            if include_stats and resolutions:
                result['statistics'] = self._calculate_resolution_statistics(resolutions)
            
            return result
            
        except Exception as e:
            print(f"⚠️ Error retrieving resolution history: {e}")
            return {
                'resolutions': [],
                'total_count': 0,
                'statistics': {} if include_stats else None,
                'error': str(e)
            }
    
    def clear_fyi_items(self, outstanding_tasks: Dict = None) -> int:
        """Clear all FYI items from persistent storage."""
        if outstanding_tasks is None:
            outstanding_tasks = self.storage.load_outstanding_tasks_raw()
        
        cleared_count = len(outstanding_tasks.get('fyi_notices', []))
        
        if cleared_count > 0:
            outstanding_tasks['fyi_notices'] = []
            batch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.storage.save_outstanding_tasks_data(outstanding_tasks, batch_timestamp)
            print(f"🗑️ Cleared {cleared_count} FYI items from persistent storage")
        
        return cleared_count
    
    def clear_newsletter_items(self, outstanding_tasks: Dict = None) -> int:
        """Clear all newsletter items from persistent storage."""
        if outstanding_tasks is None:
            outstanding_tasks = self.storage.load_outstanding_tasks_raw()
        
        cleared_count = len(outstanding_tasks.get('newsletters', []))
        
        if cleared_count > 0:
            outstanding_tasks['newsletters'] = []
            batch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.storage.save_outstanding_tasks_data(outstanding_tasks, batch_timestamp)
            print(f"🗑️ Cleared {cleared_count} newsletter items from persistent storage")
        
        return cleared_count
    
    def clear_optional_events(self, outstanding_tasks: Dict = None) -> int:
        """Clear all optional event items from persistent storage."""
        if outstanding_tasks is None:
            outstanding_tasks = self.storage.load_outstanding_tasks_raw()
        
        cleared_count = len(outstanding_tasks.get('optional_events', []))
        
        if cleared_count > 0:
            outstanding_tasks['optional_events'] = []
            batch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.storage.save_outstanding_tasks_data(outstanding_tasks, batch_timestamp)
            print(f"🗑️ Cleared {cleared_count} optional event items from persistent storage")
        
        return cleared_count
    
    def clear_both_fyi_and_newsletters(self, outstanding_tasks: Dict = None) -> tuple:
        """Clear both FYI and newsletter items from persistent storage."""
        if outstanding_tasks is None:
            outstanding_tasks = self.storage.load_outstanding_tasks_raw()
        
        fyi_count = len(outstanding_tasks.get('fyi_notices', []))
        newsletter_count = len(outstanding_tasks.get('newsletters', []))
        
        if fyi_count > 0 or newsletter_count > 0:
            outstanding_tasks['fyi_notices'] = []
            outstanding_tasks['newsletters'] = []
            batch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.storage.save_outstanding_tasks_data(outstanding_tasks, batch_timestamp)
            print(f"🗑️ Cleared {fyi_count} FYI items and {newsletter_count} newsletter items from persistent storage")
        
        return fyi_count, newsletter_count
    
    def _count_total_tasks(self, tasks_dict: Dict) -> int:
        """Count total tasks across all sections."""
        return sum(len(tasks) for tasks in tasks_dict.values())
    
    def _calculate_resolution_statistics(self, resolutions: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive statistics from resolution data."""
        if not resolutions:
            return {}
        
        resolution_types = {}
        task_sections = {}
        age_distribution = []
        
        for resolution in resolutions:
            res_type = resolution.get('resolution_type', 'unknown')
            resolution_types[res_type] = resolution_types.get(res_type, 0) + 1
            
            section = resolution.get('task_section', 'unknown')
            task_sections[section] = task_sections.get(section, 0) + 1
            
            age = resolution.get('task_age_days', 0)
            age_distribution.append(age)
        
        avg_age = sum(age_distribution) / len(age_distribution) if age_distribution else 0
        max_age = max(age_distribution) if age_distribution else 0
        min_age = min(age_distribution) if age_distribution else 0
        
        return {
            'resolution_type_distribution': resolution_types,
            'task_section_distribution': task_sections,
            'age_statistics': {
                'average_age_days': round(avg_age, 1),
                'max_age_days': max_age,
                'min_age_days': min_age,
                'total_tasks': len(resolutions)
            }
        }
