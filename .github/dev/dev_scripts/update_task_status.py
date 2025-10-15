#!/usr/bin/env python3
"""
Helper script to update task completion status in parallel_execution_plan.json

Usage:
    python update_task_status.py mark-complete T1.1 --pr 123 --url https://github.com/...
    python update_task_status.py check-incidental T1.1 --files backend/services/com_email_provider.py
    python update_task_status.py report
"""

import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Set


class TaskStatusManager:
    """Manages task completion status in parallel execution plan"""
    
    def __init__(self, plan_path: str = "tasklist/plan/parallel_execution_plan.json"):
        self.plan_path = Path(plan_path)
        self.plan_data = None
        self.load_plan()
    
    def load_plan(self):
        """Load the parallel execution plan JSON"""
        if not self.plan_path.exists():
            raise FileNotFoundError(f"Plan file not found: {self.plan_path}")
        
        with open(self.plan_path, 'r', encoding='utf-8') as f:
            self.plan_data = json.load(f)
    
    def save_plan(self):
        """Save the updated plan back to JSON"""
        with open(self.plan_path, 'w', encoding='utf-8') as f:
            json.dump(self.plan_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Updated plan saved to {self.plan_path}")
    
    def find_task(self, task_id: str) -> tuple[Dict[str, Any], int, int]:
        """Find a task by ID and return (task, wave_idx, task_idx)"""
        waves = self.plan_data['execution_plan']['waves']
        
        for wave_idx, wave in enumerate(waves):
            for task_idx, task in enumerate(wave['tasks']):
                if task['task_id'] == task_id:
                    return task, wave_idx, task_idx
        
        raise ValueError(f"Task {task_id} not found in plan")
    
    def get_task_files(self, task_id: str) -> Set[str]:
        """Get all file patterns for a task"""
        task, _, _ = self.find_task(task_id)
        files = set()
        
        for file_spec in task.get('files', []):
            files.add(file_spec['pattern'])
        
        return files
    
    def mark_complete(self, task_id: str, pr_number: int, pr_url: str, 
                     actual_runtime_min: int = None, files_modified: List[str] = None,
                     completed_by: str = None, completion_type: str = "direct"):
        """Mark a task as completed"""
        task, wave_idx, task_idx = self.find_task(task_id)
        
        # Check if already completed
        if task.get('status') == 'completed':
            print(f"⚠️  Task {task_id} already marked as completed")
            return False
        
        # Add completion metadata
        task['status'] = 'completed'
        task['completed_at'] = datetime.now(timezone.utc).isoformat()
        task['pr_number'] = pr_number
        task['pr_url'] = pr_url
        task['completion_type'] = completion_type
        
        if actual_runtime_min:
            task['actual_runtime_min'] = actual_runtime_min
        
        if files_modified:
            task['files_modified'] = files_modified
        
        if completed_by:
            task['completed_by'] = completed_by
        
        # Update the plan
        self.plan_data['execution_plan']['waves'][wave_idx]['tasks'][task_idx] = task
        
        print(f"✅ Marked {task_id} as completed (PR #{pr_number})")
        if completion_type == "incidental":
            print(f"   └─ Completed incidentally by {completed_by}")
        
        return True
    
    def check_incidental_completions(self, primary_task_id: str, 
                                    modified_files: List[str], pr_number: int, 
                                    pr_url: str) -> List[str]:
        """Check if any other tasks were incidentally completed"""
        modified_set = set(modified_files)
        incidentally_completed = []
        
        waves = self.plan_data['execution_plan']['waves']
        
        for wave in waves:
            for task in wave['tasks']:
                task_id = task['task_id']
                
                # Skip the primary task and already completed tasks
                if task_id == primary_task_id or task.get('status') == 'completed':
                    continue
                
                # Check file overlap
                task_files = self.get_task_files(task_id)
                
                # Check if all task files are in modified files (exact match)
                exact_matches = task_files.intersection(modified_set)
                
                # If significant overlap (>50% of task files), consider it incidentally completed
                if exact_matches and len(exact_matches) / len(task_files) >= 0.5:
                    incidentally_completed.append(task_id)
                    print(f"🔍 Found incidental completion: {task_id}")
                    print(f"   Files overlap: {exact_matches}")
                    
                    # Mark it as completed
                    self.mark_complete(
                        task_id=task_id,
                        pr_number=pr_number,
                        pr_url=pr_url,
                        files_modified=list(exact_matches),
                        completed_by=primary_task_id,
                        completion_type="incidental"
                    )
        
        return incidentally_completed
    
    def get_progress_report(self) -> Dict[str, Any]:
        """Generate a progress report"""
        waves = self.plan_data['execution_plan']['waves']
        
        total_tasks = 0
        completed_tasks = 0
        completed_direct = 0
        completed_incidental = 0
        
        completed_list = []
        pending_list = []
        
        for wave in waves:
            for task in wave['tasks']:
                total_tasks += 1
                task_id = task['task_id']
                
                if task.get('status') == 'completed':
                    completed_tasks += 1
                    completed_list.append({
                        'task_id': task_id,
                        'summary': task['summary'],
                        'pr_number': task.get('pr_number'),
                        'completion_type': task.get('completion_type', 'direct'),
                        'completed_at': task.get('completed_at')
                    })
                    
                    if task.get('completion_type') == 'incidental':
                        completed_incidental += 1
                    else:
                        completed_direct += 1
                else:
                    pending_list.append({
                        'task_id': task_id,
                        'summary': task['summary'],
                        'wave': wave['wave_number']
                    })
        
        percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completed_direct': completed_direct,
            'completed_incidental': completed_incidental,
            'pending_tasks': total_tasks - completed_tasks,
            'percentage': round(percentage, 1),
            'completed_list': completed_list,
            'pending_list': pending_list
        }
    
    def print_report(self):
        """Print a formatted progress report"""
        report = self.get_progress_report()
        
        print("\n" + "="*80)
        print("📊 TASK COMPLETION REPORT")
        print("="*80)
        print(f"\n📈 Overall Progress: {report['completed_tasks']}/{report['total_tasks']} tasks ({report['percentage']}%)")
        print(f"   ✅ Direct completions: {report['completed_direct']}")
        print(f"   🔄 Incidental completions: {report['completed_incidental']}")
        print(f"   ⏳ Pending: {report['pending_tasks']}")
        
        if report['completed_list']:
            print(f"\n✅ Completed Tasks ({len(report['completed_list'])}):")
            for task in report['completed_list']:
                completion_icon = "🔄" if task['completion_type'] == 'incidental' else "✅"
                print(f"   {completion_icon} {task['task_id']}: {task['summary']}")
                if task.get('pr_number'):
                    print(f"      PR #{task['pr_number']}")
        
        if report['pending_list']:
            print(f"\n⏳ Pending Tasks ({len(report['pending_list'])}):")
            for task in report['pending_list']:
                print(f"   ⏳ {task['task_id']}: {task['summary']} (Wave {task['wave']})")
        
        print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(description='Manage task completion status')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # mark-complete command
    mark_parser = subparsers.add_parser('mark-complete', help='Mark a task as completed')
    mark_parser.add_argument('task_id', help='Task ID (e.g., T1.1)')
    mark_parser.add_argument('--pr', type=int, required=True, help='PR number')
    mark_parser.add_argument('--url', required=True, help='PR URL')
    mark_parser.add_argument('--runtime', type=int, help='Actual runtime in minutes')
    mark_parser.add_argument('--files', nargs='+', help='Files modified in PR')
    
    # check-incidental command
    incidental_parser = subparsers.add_parser('check-incidental', 
                                              help='Check for incidentally completed tasks')
    incidental_parser.add_argument('task_id', help='Primary task ID')
    incidental_parser.add_argument('--pr', type=int, required=True, help='PR number')
    incidental_parser.add_argument('--url', required=True, help='PR URL')
    incidental_parser.add_argument('--files', nargs='+', required=True, 
                                   help='Files modified in PR')
    
    # report command
    subparsers.add_parser('report', help='Generate progress report')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        manager = TaskStatusManager()
        
        if args.command == 'mark-complete':
            manager.mark_complete(
                task_id=args.task_id,
                pr_number=args.pr,
                pr_url=args.url,
                actual_runtime_min=args.runtime,
                files_modified=args.files
            )
            manager.save_plan()
            manager.print_report()
        
        elif args.command == 'check-incidental':
            manager.mark_complete(
                task_id=args.task_id,
                pr_number=args.pr,
                pr_url=args.url,
                files_modified=args.files
            )
            
            incidental = manager.check_incidental_completions(
                primary_task_id=args.task_id,
                modified_files=args.files,
                pr_number=args.pr,
                pr_url=args.url
            )
            
            if incidental:
                print(f"\n🎉 Found {len(incidental)} incidentally completed task(s)!")
            else:
                print(f"\n✅ No incidental completions found")
            
            manager.save_plan()
            manager.print_report()
        
        elif args.command == 'report':
            manager.print_report()
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
