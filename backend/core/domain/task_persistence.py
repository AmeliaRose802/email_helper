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
        """Mark specific tasks as completed and move them to completed tasks file"""
        if completion_timestamp is None:
            completion_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        outstanding_tasks = self.load_outstanding_tasks()
        completed_tasks = self.load_completed_tasks()
        
        newly_completed = []
        
        # Find and remove completed tasks from outstanding
        for section_key in outstanding_tasks:
            tasks_to_keep = []
            for task in outstanding_tasks[section_key]:
                if task.get('task_id') in completed_task_ids:
                    # Mark as completed and add to completed list
                    task['status'] = 'completed'
                    task['completion_timestamp'] = completion_timestamp
                    newly_completed.append(task)
                else:
                    tasks_to_keep.append(task)
            outstanding_tasks[section_key] = tasks_to_keep
        
        # Add to completed tasks
        if newly_completed:
            completed_tasks.extend(newly_completed)
            
            # Save updated files
            self._save_tasks_to_file(self.tasks_file, {
                'last_updated': completion_timestamp,
                'tasks': outstanding_tasks
            })
            
            self._save_tasks_to_file(self.completed_file, completed_tasks)
            
            print(f"✅ Marked {len(newly_completed)} tasks as completed")
    
    def get_entry_ids_for_tasks(self, task_ids: List[str]) -> List[str]:
        """Get all email EntryIDs associated with the specified task IDs"""
        outstanding_tasks = self.load_outstanding_tasks()
        entry_ids = []
        
        for section_key in outstanding_tasks:
            for task in outstanding_tasks[section_key]:
                if task.get('task_id') in task_ids:
                    # Get entry IDs
                    task_entry_ids = task.get('_entry_ids', [])
                    entry_ids.extend(task_entry_ids)
        
        return list(set(entry_ids))  # Remove duplicates
    
    def get_comprehensive_summary(self, current_summary_sections: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Get comprehensive summary combining current batch with outstanding tasks from previous batches"""
        outstanding_tasks = self.load_outstanding_tasks()
        
        # Create comprehensive summary
        comprehensive_summary = {
            'required_actions': [],
            'team_actions': [],
            'completed_team_actions': [],
            'optional_actions': [],
            'job_listings': [],
            'optional_events': [],
            'fyi_notices': [],
            'newsletters': []
        }
        
        # Merge all task types (current + outstanding) including FYI and newsletters
        for section_key in ['required_actions', 'team_actions', 'completed_team_actions', 'optional_actions', 'job_listings', 'optional_events', 'fyi_notices', 'newsletters']:
            # Add outstanding tasks first (older, potentially higher priority)
            comprehensive_summary[section_key].extend(outstanding_tasks.get(section_key, []))
            
            # Add current batch tasks
            current_tasks = current_summary_sections.get(section_key, [])
            for task in current_tasks:
                # Check if this task is already in outstanding (avoid duplicates)
                task_id = self._generate_task_id(task)
                if not any(existing.get('task_id') == task_id for existing in comprehensive_summary[section_key]):
                    # Add task_id to the current task for UI completion buttons
                    task_with_id = task.copy()
                    task_with_id['task_id'] = task_id
                    
                    # Convert _entry_id (singular) to _entry_ids (plural list) for email associations
                    if '_entry_id' in task_with_id and task_with_id['_entry_id']:
                        entry_id = task_with_id['_entry_id']
                        task_with_id['_entry_ids'] = [entry_id]
                        # Remove the singular version to avoid confusion
                        del task_with_id['_entry_id']
                    elif '_entry_ids' not in task_with_id:
                        # Ensure _entry_ids field exists even if empty
                        task_with_id['_entry_ids'] = []
                    
                    comprehensive_summary[section_key].append(task_with_id)
        
        # Sort by priority and due date
        self._sort_tasks_by_priority(comprehensive_summary)
        
        return comprehensive_summary
    
    def load_completed_tasks(self) -> List[Dict]:
        """Load completed tasks from persistent storage"""
        if not os.path.exists(self.completed_file):
            return []
        
        try:
            with open(self.completed_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading completed tasks: {e}")
            return []
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get statistics about tasks"""
        outstanding_tasks = self.load_outstanding_tasks()
        completed_tasks = self.load_completed_tasks()
        
        outstanding_count = self._count_total_tasks(outstanding_tasks)
        completed_count = len(completed_tasks)
        
        # Calculate task age statistics
        old_tasks = []  # tasks older than 7 days
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
            'old_tasks': old_tasks[:5],  # Show only first 5 old tasks
            'sections_breakdown': {
                section: len(tasks) for section, tasks in outstanding_tasks.items()
            }
        }
    
    def cleanup_old_completed_tasks(self, days_to_keep: int = 30) -> None:
        """Clean up completed tasks older than specified days"""
        completed_tasks = self.load_completed_tasks()
        current_time = datetime.now()
        
        tasks_to_keep = []
        for task in completed_tasks:
            try:
                completion_time = datetime.strptime(task.get('completion_timestamp', ''), '%Y-%m-%d %H:%M:%S')
                days_old = (current_time - completion_time).days
                if days_old < days_to_keep:
                    tasks_to_keep.append(task)
            except:
                # Keep tasks with invalid timestamps
                tasks_to_keep.append(task)
        
        if len(tasks_to_keep) < len(completed_tasks):
            self._save_tasks_to_file(self.completed_file, tasks_to_keep)
            print(f"🧹 Cleaned up {len(completed_tasks) - len(tasks_to_keep)} old completed tasks")
    
    def _generate_task_id(self, task: Dict) -> str:
        """Generate unique ID for a task based on content"""
        subject = task.get('subject', '')
        sender = task.get('sender', '')
        action = task.get('action_required', '')
        
        # Create a simple hash-like ID
        content = f"{subject}:{sender}:{action}".lower().replace(' ', '')
        return str(hash(content) % 1000000)  # 6-digit ID
    
    def _merge_task_lists(self, existing_tasks: Dict, current_tasks: Dict, batch_timestamp: str) -> Dict:
        """Merge current batch tasks with existing outstanding tasks"""
        merged = existing_tasks.copy()
        
        for section_key in current_tasks:
            if section_key not in merged:
                merged[section_key] = []
            
            for current_task in current_tasks[section_key]:
                # Check if task already exists
                task_id = current_task.get('task_id')
                existing_task = None
                for i, existing in enumerate(merged[section_key]):
                    if existing.get('task_id') == task_id:
                        existing_task = existing
                        break
                
                if existing_task:
                    # Update existing task (increment batch count, update timestamp, merge entry IDs)
                    existing_task['batch_timestamp'] = batch_timestamp
                    existing_task['batch_count'] = existing_task.get('batch_count', 1) + 1
                    
                    # Merge entry IDs (both tasks should have proper _entry_ids arrays)
                    current_entry_ids = current_task.get('_entry_ids', [])
                    existing_entry_ids = existing_task.get('_entry_ids', [])
                    
                    # Combine entry IDs without duplicates
                    all_entry_ids = list(set(existing_entry_ids + current_entry_ids))
                    existing_task['_entry_ids'] = all_entry_ids
                else:
                    # Add new task
                    merged[section_key].append(current_task)
        
        return merged
    
    def _count_total_tasks(self, tasks_dict: Dict) -> int:
        """Count total tasks across all sections"""
        return sum(len(tasks) for tasks in tasks_dict.values())
    
    def _sort_tasks_by_priority(self, summary_sections: Dict) -> None:
        """Sort tasks within each section by priority and due date"""
        for section_key in summary_sections:
            if section_key in ['required_actions', 'team_actions', 'completed_team_actions', 'optional_actions']:
                summary_sections[section_key].sort(key=lambda x: (
                    x.get('batch_count', 1),  # Older tasks first (higher batch count)
                    x.get('priority', 99),    # Higher priority first
                    x.get('due_date', 'zzz')  # Earlier due dates first
                ), reverse=False)
    
    def clear_fyi_items(self) -> int:
        """Clear all FYI items from persistent storage"""
        outstanding_tasks = self.load_outstanding_tasks()
        cleared_count = len(outstanding_tasks.get('fyi_notices', []))
        
        if cleared_count > 0:
            outstanding_tasks['fyi_notices'] = []
            
            # Save updated tasks
            batch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save_tasks_to_file(self.tasks_file, {
                'last_updated': batch_timestamp,
                'tasks': outstanding_tasks
            })
            
            print(f"🗑️ Cleared {cleared_count} FYI items from persistent storage")
        
        return cleared_count
    
    def clear_newsletter_items(self) -> int:
        """Clear all newsletter items from persistent storage"""
        outstanding_tasks = self.load_outstanding_tasks()
        cleared_count = len(outstanding_tasks.get('newsletters', []))
        
        if cleared_count > 0:
            outstanding_tasks['newsletters'] = []
            
            # Save updated tasks
            batch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save_tasks_to_file(self.tasks_file, {
                'last_updated': batch_timestamp,
                'tasks': outstanding_tasks
            })
            
            print(f"🗑️ Cleared {cleared_count} newsletter items from persistent storage")
        
        return cleared_count
    
    def clear_optional_events(self) -> int:
        """Clear all optional event items from persistent storage"""
        outstanding_tasks = self.load_outstanding_tasks()
        cleared_count = len(outstanding_tasks.get('optional_events', []))
        
        if cleared_count > 0:
            outstanding_tasks['optional_events'] = []
            
            # Save updated tasks
            batch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save_tasks_to_file(self.tasks_file, {
                'last_updated': batch_timestamp,
                'tasks': outstanding_tasks
            })
            
            print(f"🗑️ Cleared {cleared_count} optional event items from persistent storage")
        
        return cleared_count
    
    def clear_both_fyi_and_newsletters(self) -> tuple:
        """Clear both FYI and newsletter items from persistent storage"""
        outstanding_tasks = self.load_outstanding_tasks()
        fyi_count = len(outstanding_tasks.get('fyi_notices', []))
        newsletter_count = len(outstanding_tasks.get('newsletters', []))
        
        if fyi_count > 0 or newsletter_count > 0:
            outstanding_tasks['fyi_notices'] = []
            outstanding_tasks['newsletters'] = []
            
            # Save updated tasks
            batch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save_tasks_to_file(self.tasks_file, {
                'last_updated': batch_timestamp,
                'tasks': outstanding_tasks
            })
            
            print(f"🗑️ Cleared {fyi_count} FYI items and {newsletter_count} newsletter items from persistent storage")
        
        return fyi_count, newsletter_count
    
    def _save_tasks_to_file(self, filepath: str, data: Any) -> None:
        """Save data to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"⚠️ Error saving tasks to {filepath}: {e}")

    def record_task_resolution(self, task_id: str, resolution_type: str, resolution_notes: str = "", completion_timestamp: str = None) -> bool:
        """
        Record task resolution with detailed tracking for historical analysis.
        
        Args:
            task_id (str): Unique identifier for the task
            resolution_type (str): Type of resolution ('completed', 'dismissed', 'deferred', 'delegated')
            resolution_notes (str): Optional notes about the resolution
            completion_timestamp (str): Optional custom timestamp
            
        Returns:
            bool: True if resolution was successfully recorded
        """
        if completion_timestamp is None:
            completion_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # Create resolution history directory
            history_dir = os.path.join(self.storage_dir, 'task_history')
            os.makedirs(history_dir, exist_ok=True)
            
            # Load outstanding tasks to get task details
            outstanding_tasks = self.load_outstanding_tasks()
            completed_tasks = self.load_completed_tasks()
            
            # Find the task being resolved
            task_data = None
            task_section = None
            
            for section_key in outstanding_tasks:
                for task in outstanding_tasks[section_key]:
                    if task.get('task_id') == task_id:
                        task_data = task.copy()
                        task_section = section_key
                        break
                if task_data:
                    break
            
            if not task_data:
                print(f"⚠️ Task {task_id} not found in outstanding tasks")
                return False
            
            # Create detailed resolution record
            resolution_record = {
                'task_id': task_id,
                'resolution_timestamp': completion_timestamp,
                'resolution_type': resolution_type,
                'resolution_notes': resolution_notes,
                'task_section': task_section,
                'task_data': task_data,
                'task_age_days': self._calculate_task_age(task_data),
                'associated_emails': task_data.get('_entry_ids', []),
                'task_priority': task_data.get('priority', 'normal'),
                'task_sender': task_data.get('sender', 'unknown'),
                'resolution_metadata': {
                    'system_version': '1.0',  # Track for future compatibility
                    'recorded_by': 'user_interaction'
                }
            }
            
            # Save to monthly resolution history file
            current_month = datetime.now().strftime('%Y_%m')
            history_file = os.path.join(history_dir, f'task_resolutions_{current_month}.jsonl')
            
            with open(history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(resolution_record, default=str) + '\n')
            
            # Mark task as completed in the regular completed tasks (existing behavior)
            self.mark_tasks_completed([task_id], completion_timestamp)
            
            print(f"📝 Recorded task resolution: {task_id} - {resolution_type}")
            return True
            
        except Exception as e:
            print(f"⚠️ Error recording task resolution: {e}")
            return False
    
    def get_resolution_history(self, days_back: int = 30, resolution_type: str = None, include_stats: bool = True) -> Dict[str, Any]:
        """
        Retrieve task resolution history for analysis and reporting.
        
        Args:
            days_back (int): Number of days to look back for history
            resolution_type (str): Filter by specific resolution type
            include_stats (bool): Whether to include summary statistics
            
        Returns:
            dict: Resolution history with optional statistics
        """
        try:
            history_dir = os.path.join(self.storage_dir, 'task_history')
            if not os.path.exists(history_dir):
                return {
                    'resolutions': [],
                    'total_count': 0,
                    'statistics': {} if include_stats else None
                }
            
            # Load resolution records from all relevant monthly files
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
                                
                                # Filter by date range
                                if record_date >= cutoff_date:
                                    # Filter by resolution type if specified
                                    if resolution_type is None or record['resolution_type'] == resolution_type:
                                        resolutions.append(record)
                                        
                            except (json.JSONDecodeError, ValueError, KeyError) as e:
                                print(f"⚠️ Error parsing resolution record: {e}")
                                continue
            
            # Sort by resolution timestamp (most recent first)
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
            
            # Calculate statistics if requested
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
    
    def _calculate_task_age(self, task_data: Dict) -> int:
        """Calculate age of task in days."""
        try:
            first_seen = task_data.get('first_seen', '')
            if first_seen:
                first_seen_date = datetime.strptime(first_seen, '%Y-%m-%d %H:%M:%S')
                time_diff = datetime.now() - first_seen_date
                age_days = time_diff.days
                
                # If the difference is less than a full day but more than 0, round up to 1 day
                if age_days == 0 and time_diff.total_seconds() > 0:
                    age_days = 1
                return age_days
        except:
            pass
        return 0
    
    def _calculate_resolution_statistics(self, resolutions: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive statistics from resolution data."""
        if not resolutions:
            return {}
        
        # Resolution type distribution
        resolution_types = {}
        task_sections = {}
        age_distribution = []
        
        for resolution in resolutions:
            # Count resolution types
            res_type = resolution.get('resolution_type', 'unknown')
            resolution_types[res_type] = resolution_types.get(res_type, 0) + 1
            
            # Count task sections
            section = resolution.get('task_section', 'unknown')
            task_sections[section] = task_sections.get(section, 0) + 1
            
            # Collect age data
            age = resolution.get('task_age_days', 0)
            age_distribution.append(age)
        
        # Calculate age statistics
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
            },
            'completion_rate': {
                'completed': resolution_types.get('completed', 0),
                'dismissed': resolution_types.get('dismissed', 0),
                'deferred': resolution_types.get('deferred', 0),
                'total': len(resolutions)
            }
        }
