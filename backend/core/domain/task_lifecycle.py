#!/usr/bin/env python3
"""Task Lifecycle - Task completion and expiration management."""

from datetime import datetime
from typing import Dict, List


class TaskLifecycle:
    """Manages task lifecycle including completion and expiration."""

    def __init__(self, storage):
        """Initialize with storage backend.

        Args:
            storage: TaskStorage instance for data operations.
        """
        self.storage = storage

    def is_event_expired(self, event: Dict) -> bool:
        """Check if an optional event has passed its date."""
        try:
            event_date_str = event.get('date', '')
            if not event_date_str:
                return False

            try:
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    event_date = datetime.strptime(event_date_str, '%m/%d/%Y')
                except ValueError:
                    return False

            current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return event_date < current_date

        except Exception as e:
            print(f"Warning: Could not check expiration for event: {e}")
            return False

    def mark_tasks_completed(self, completed_task_ids: List[str], completion_timestamp: str = None) -> None:
        """Mark specific tasks as completed and move them to completed tasks file."""
        if completion_timestamp is None:
            completion_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        outstanding_tasks = self.storage.load_outstanding_tasks_raw()
        completed_tasks = self.storage.load_completed_tasks()

        newly_completed = []

        for section_key in outstanding_tasks:
            tasks_to_keep = []
            for task in outstanding_tasks[section_key]:
                if task.get('task_id') in completed_task_ids:
                    task['status'] = 'completed'
                    task['completion_timestamp'] = completion_timestamp
                    newly_completed.append(task)
                else:
                    tasks_to_keep.append(task)
            outstanding_tasks[section_key] = tasks_to_keep

        if newly_completed:
            completed_tasks.extend(newly_completed)
            self.storage.save_outstanding_tasks_data(outstanding_tasks, completion_timestamp)
            self.storage.save_completed_tasks_data(completed_tasks)
            print(f"✅ Marked {len(newly_completed)} tasks as completed")

    def cleanup_old_completed_tasks(self, days_to_keep: int = 30) -> None:
        """Clean up completed tasks older than specified days."""
        completed_tasks = self.storage.load_completed_tasks()
        current_time = datetime.now()

        tasks_to_keep = []
        for task in completed_tasks:
            try:
                completion_time = datetime.strptime(task.get('completion_timestamp', ''), '%Y-%m-%d %H:%M:%S')
                days_old = (current_time - completion_time).days
                if days_old < days_to_keep:
                    tasks_to_keep.append(task)
            except:
                tasks_to_keep.append(task)

        if len(tasks_to_keep) < len(completed_tasks):
            self.storage.save_completed_tasks_data(tasks_to_keep)
            print(f"🧹 Cleaned up {len(completed_tasks) - len(tasks_to_keep)} old completed tasks")

    def record_task_resolution(self, task_id: str, resolution_type: str,
                              resolution_notes: str = "", completion_timestamp: str = None,
                              outstanding_tasks: Dict = None) -> bool:
        """Record task resolution with detailed tracking for historical analysis."""
        if completion_timestamp is None:
            completion_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            import os
            import json

            history_dir = os.path.join(self.storage.storage_dir, 'task_history')
            os.makedirs(history_dir, exist_ok=True)

            if outstanding_tasks is None:
                outstanding_tasks = self.storage.load_outstanding_tasks_raw()

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
                    'system_version': '1.0',
                    'recorded_by': 'user_interaction'
                }
            }

            current_month = datetime.now().strftime('%Y_%m')
            history_file = os.path.join(history_dir, f'task_resolutions_{current_month}.jsonl')

            with open(history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(resolution_record, default=str) + '\n')

            self.mark_tasks_completed([task_id], completion_timestamp)

            print(f"📝 Recorded task resolution: {task_id} - {resolution_type}")
            return True

        except Exception as e:
            print(f"⚠️ Error recording task resolution: {e}")
            return False

    def _calculate_task_age(self, task_data: Dict) -> int:
        """Calculate age of task in days."""
        try:
            first_seen = task_data.get('first_seen', '')
            if first_seen:
                first_seen_date = datetime.strptime(first_seen, '%Y-%m-%d %H:%M:%S')
                time_diff = datetime.now() - first_seen_date
                age_days = time_diff.days

                if age_days == 0 and time_diff.total_seconds() > 0:
                    age_days = 1
                return age_days
        except:
            pass
        return 0
