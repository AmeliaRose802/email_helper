#!/usr/bin/env python3
"""
Task Persistence - Manages persistent storage of outstanding tasks across batches
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any


class TaskPersistence:
    def __init__(self, storage_dir: str = None):
        """Initialize task persistence with storage directory"""
        if storage_dir is None:
            # Default to runtime_data/tasks
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            storage_dir = os.path.join(project_root, 'runtime_data', 'tasks')
        
        self.storage_dir = storage_dir
        self.tasks_file = os.path.join(storage_dir, 'outstanding_tasks.json')
        self.completed_file = os.path.join(storage_dir, 'completed_tasks.json')
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
    
    def save_outstanding_tasks(self, summary_sections: Dict[str, List[Dict]], batch_timestamp: str = None) -> None:
        """Save outstanding tasks from current batch, merging with existing ones"""
        if batch_timestamp is None:
            batch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Load existing tasks
        existing_tasks = self.load_outstanding_tasks()
        
        # Process current batch tasks
        current_tasks = {
            'required_actions': [],
            'team_actions': [],
            'completed_team_actions': [],
            'optional_actions': [],
            'job_listings': [],
            'optional_events': []
        }
        
        # Extract actionable tasks from summary sections
        for section_key in ['required_actions', 'team_actions', 'completed_team_actions', 'optional_actions', 'job_listings', 'optional_events']:
            if section_key in summary_sections:
                for task in summary_sections[section_key]:
                    # Add batch metadata
                    task_with_metadata = task.copy()
                    task_with_metadata.update({
                        'batch_timestamp': batch_timestamp,
                        'first_seen': batch_timestamp,
                        'task_id': self._generate_task_id(task),
                        'status': 'outstanding',
                        'batch_count': 1
                    })
                    
                    # Convert _entry_id (singular) to _entry_ids (plural list) for email associations
                    if '_entry_id' in task_with_metadata and task_with_metadata['_entry_id']:
                        entry_id = task_with_metadata['_entry_id']
                        task_with_metadata['_entry_ids'] = [entry_id]
                        # Remove the singular version to avoid confusion
                        del task_with_metadata['_entry_id']
                    elif '_entry_ids' not in task_with_metadata:
                        # Ensure _entry_ids field exists even if empty
                        task_with_metadata['_entry_ids'] = []
                    
                    current_tasks[section_key].append(task_with_metadata)
        
        # Merge with existing tasks (avoid duplicates, update batch counts)
        merged_tasks = self._merge_task_lists(existing_tasks, current_tasks, batch_timestamp)
        
        # Save merged tasks
        self._save_tasks_to_file(self.tasks_file, {
            'last_updated': batch_timestamp,
            'tasks': merged_tasks
        })
        
        print(f"💾 Saved {self._count_total_tasks(merged_tasks)} outstanding tasks to persistent storage")
    
    def load_outstanding_tasks(self) -> Dict[str, List[Dict]]:
        """Load outstanding tasks from persistent storage"""
        if not os.path.exists(self.tasks_file):
            return {
                'required_actions': [],
                'team_actions': [],
                'completed_team_actions': [],
                'optional_actions': [],
                'job_listings': [],
                'optional_events': []
            }
        
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tasks = data.get('tasks', {
                    'required_actions': [],
                    'team_actions': [],
                    'completed_team_actions': [],
                    'optional_actions': [],
                    'job_listings': [],
                    'optional_events': []
                })
                
                # Validate and clean task data
                cleaned_tasks = {}
                for section_key, task_list in tasks.items():
                    cleaned_tasks[section_key] = []
                    if not isinstance(task_list, list):
                        print(f"Warning: {section_key} is not a list, skipping")
                        continue
                    
                    for task in task_list:
                        if isinstance(task, dict):
                            # Ensure required fields exist
                            if 'task_id' not in task:
                                print(f"Warning: Task missing task_id: {task}")
                                continue
                            # Ensure sender field exists (fallback to email_sender if needed)
                            if 'sender' not in task and 'email_sender' in task:
                                task['sender'] = task['email_sender']
                            elif 'sender' not in task:
                                task['sender'] = 'Unknown'
                            cleaned_tasks[section_key].append(task)
                        else:
                            print(f"Warning: Invalid task format (not a dict): {task}")
                
                return cleaned_tasks
                
        except Exception as e:
            print(f"⚠️ Error loading outstanding tasks: {e}")
            return {
                'required_actions': [],
                'team_actions': [],
                'completed_team_actions': [],
                'optional_actions': [],
                'job_listings': [],
                'optional_events': []
            }
    
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
            'fyi_notices': current_summary_sections.get('fyi_notices', []),
            'newsletters': current_summary_sections.get('newsletters', [])
        }
        
        # Merge actionable tasks (current + outstanding)
        for section_key in ['required_actions', 'team_actions', 'completed_team_actions', 'optional_actions', 'job_listings', 'optional_events']:
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
    
    def _save_tasks_to_file(self, filepath: str, data: Any) -> None:
        """Save data to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"⚠️ Error saving tasks to {filepath}: {e}")
