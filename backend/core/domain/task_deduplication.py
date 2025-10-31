#!/usr/bin/env python3
"""Task Deduplication - Task merging and ID generation logic."""

from datetime import datetime
from typing import Dict, List


class TaskDeduplication:
    """Handles task deduplication and merging operations."""
    
    def generate_task_id(self, task: Dict) -> str:
        """Generate unique ID for a task based on content."""
        subject = task.get('subject', '')
        sender = task.get('sender', '')
        action = task.get('action_required', '')
        
        content = f"{subject}:{sender}:{action}".lower().replace(' ', '')
        return str(hash(content) % 1000000)
    
    def merge_task_lists(self, existing_tasks: Dict, current_tasks: Dict, batch_timestamp: str) -> Dict:
        """Merge current batch tasks with existing outstanding tasks."""
        merged = existing_tasks.copy()
        
        for section_key in current_tasks:
            if section_key not in merged:
                merged[section_key] = []
            
            for current_task in current_tasks[section_key]:
                task_id = current_task.get('task_id')
                existing_task = None
                for existing in merged[section_key]:
                    if existing.get('task_id') == task_id:
                        existing_task = existing
                        break
                
                if existing_task:
                    existing_task['batch_timestamp'] = batch_timestamp
                    existing_task['batch_count'] = existing_task.get('batch_count', 1) + 1
                    
                    current_entry_ids = current_task.get('_entry_ids', [])
                    existing_entry_ids = existing_task.get('_entry_ids', [])
                    
                    all_entry_ids = list(set(existing_entry_ids + current_entry_ids))
                    existing_task['_entry_ids'] = all_entry_ids
                else:
                    merged[section_key].append(current_task)
        
        return merged
    
    def get_comprehensive_summary(self, current_summary_sections: Dict[str, List[Dict]], 
                                  outstanding_tasks: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Get comprehensive summary combining current batch with outstanding tasks."""
        comprehensive_summary = {
            'required_actions': [], 'team_actions': [], 'completed_team_actions': [],
            'optional_actions': [], 'job_listings': [], 'optional_events': [],
            'fyi_notices': [], 'newsletters': []
        }
        
        for section_key in comprehensive_summary.keys():
            comprehensive_summary[section_key].extend(outstanding_tasks.get(section_key, []))
            
            current_tasks = current_summary_sections.get(section_key, [])
            for task in current_tasks:
                task_id = self.generate_task_id(task)
                if not any(existing.get('task_id') == task_id for existing in comprehensive_summary[section_key]):
                    task_with_id = task.copy()
                    task_with_id['task_id'] = task_id
                    
                    if '_entry_id' in task_with_id and task_with_id['_entry_id']:
                        entry_id = task_with_id['_entry_id']
                        task_with_id['_entry_ids'] = [entry_id]
                        del task_with_id['_entry_id']
                    elif '_entry_ids' not in task_with_id:
                        task_with_id['_entry_ids'] = []
                    
                    comprehensive_summary[section_key].append(task_with_id)
        
        self._sort_tasks_by_priority(comprehensive_summary)
        return comprehensive_summary
    
    def _sort_tasks_by_priority(self, summary_sections: Dict) -> None:
        """Sort tasks within each section by priority and due date."""
        for section_key in summary_sections:
            if section_key in ['required_actions', 'team_actions', 'completed_team_actions', 'optional_actions']:
                summary_sections[section_key].sort(key=lambda x: (
                    x.get('batch_count', 1),
                    x.get('priority', 99),
                    x.get('due_date', 'zzz')
                ), reverse=False)
