#!/usr/bin/env python3
"""Task Storage - Core load/save operations for task persistence."""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class TaskStorage:
    """Handles low-level storage operations for task data."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize task storage with directory path.
        
        Args:
            storage_dir: Directory for task storage files.
        """
        if storage_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            storage_dir = os.path.join(project_root, 'runtime_data', 'tasks')
        
        self.storage_dir = storage_dir
        self.tasks_file = os.path.join(storage_dir, 'outstanding_tasks.json')
        self.completed_file = os.path.join(storage_dir, 'completed_tasks.json')
        
        os.makedirs(storage_dir, exist_ok=True)
    
    def save_to_file(self, filepath: str, data: Any) -> None:
        """Save data to JSON file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"⚠️ Error saving tasks to {filepath}: {e}")
    
    def load_outstanding_tasks_raw(self) -> Dict[str, Any]:
        """Load raw outstanding tasks data from file."""
        if not os.path.exists(self.tasks_file):
            return self._empty_tasks_structure()
        
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tasks = data.get('tasks', self._empty_tasks_structure())
                
                for section in self._task_sections():
                    if section not in tasks:
                        tasks[section] = []
                
                return tasks
        except Exception as e:
            print(f"⚠️ Error loading outstanding tasks: {e}")
            return self._empty_tasks_structure()
    
    def load_completed_tasks(self) -> List[Dict]:
        """Load completed tasks from persistent storage."""
        if not os.path.exists(self.completed_file):
            return []
        
        try:
            with open(self.completed_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading completed tasks: {e}")
            return []
    
    def save_outstanding_tasks_data(self, tasks: Dict[str, List[Dict]], timestamp: Optional[str] = None) -> None:
        """Save outstanding tasks data to file."""
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.save_to_file(self.tasks_file, {
            'last_updated': timestamp,
            'tasks': tasks
        })
    
    def save_completed_tasks_data(self, tasks: List[Dict]) -> None:
        """Save completed tasks data to file."""
        self.save_to_file(self.completed_file, tasks)
    
    def _empty_tasks_structure(self) -> Dict[str, List[Dict]]:
        """Return empty tasks structure."""
        return {section: [] for section in self._task_sections()}
    
    def _task_sections(self) -> List[str]:
        """Return list of all task section names."""
        return [
            'required_actions', 'team_actions', 'completed_team_actions',
            'optional_actions', 'job_listings', 'optional_events',
            'fyi_notices', 'newsletters'
        ]
