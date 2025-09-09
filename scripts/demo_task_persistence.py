#!/usr/bin/env python3
"""
Task Persistence Demo - Demonstrates the new persistent task tracking feature
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from task_persistence import TaskPersistence
from datetime import datetime

def demo_task_persistence():
    """Demonstrate task persistence functionality"""
    
    print("🔄 TASK PERSISTENCE FEATURE DEMO")
    print("=" * 50)
    
    # Initialize task persistence
    tp = TaskPersistence()
    
    # Create sample summary sections (simulating first batch)
    batch1_summary = {
        'required_actions': [
            {
                'subject': 'Complete security training',
                'sender': 'Security Team',
                'due_date': '2025-09-15',
                'explanation': 'Annual security training is due',
                'action_required': 'Complete online training modules',
                'links': ['https://training.company.com']
            },
            {
                'subject': 'Review project proposal',
                'sender': 'Manager',
                'due_date': '2025-09-10',
                'explanation': 'New project needs approval',
                'action_required': 'Review and provide feedback',
                'links': []
            }
        ],
        'team_actions': [
            {
                'subject': 'Team meeting planning',
                'sender': 'Team Lead',
                'due_date': '2025-09-12',
                'explanation': 'Plan agenda for weekly team meeting',
                'action_required': 'Prepare agenda items',
                'links': []
            }
        ],
        'optional_actions': [],
        'job_listings': [],
        'optional_events': [],
        'fyi_notices': [
            {
                'summary': 'Office closure on Friday for maintenance',
                'email_subject': 'Office Maintenance Notice',
                'email_sender': 'Facilities',
                'email_date': datetime.now()
            }
        ],
        'newsletters': []
    }
    
    print("📧 BATCH 1: Processing initial emails...")
    print(f"   - Required Actions: {len(batch1_summary['required_actions'])}")
    print(f"   - Team Actions: {len(batch1_summary['team_actions'])}")
    
    # Save first batch
    tp.save_outstanding_tasks(batch1_summary, "2025-09-08 10:00:00")
    
    # Show statistics after first batch
    stats = tp.get_task_statistics()
    print(f"\n📊 After Batch 1:")
    print(f"   - Outstanding tasks: {stats['outstanding_total']}")
    print(f"   - Required actions: {stats['sections_breakdown']['required_actions']}")
    print(f"   - Team actions: {stats['sections_breakdown']['team_actions']}")
    
    # Simulate second batch (some new tasks, some overlapping)
    batch2_summary = {
        'required_actions': [
            {
                'subject': 'Complete security training',  # Same task - should merge
                'sender': 'Security Team',
                'due_date': '2025-09-15',
                'explanation': 'Annual security training is due',
                'action_required': 'Complete online training modules',
                'links': ['https://training.company.com']
            },
            {
                'subject': 'Submit expense report',  # New task
                'sender': 'Finance',
                'due_date': '2025-09-14',
                'explanation': 'Monthly expense report submission',
                'action_required': 'Submit receipts and report',
                'links': []
            }
        ],
        'team_actions': [],  # No team actions in this batch
        'optional_actions': [
            {
                'subject': 'Attend optional workshop',  # New optional task
                'sender': 'HR',
                'explanation': 'Professional development opportunity',
                'action_required': 'Register for workshop',
                'why_relevant': 'Skill development',
                'links': []
            }
        ],
        'job_listings': [],
        'optional_events': [],
        'fyi_notices': [],
        'newsletters': []
    }
    
    print(f"\n📧 BATCH 2: Processing new emails...")
    print(f"   - Required Actions: {len(batch2_summary['required_actions'])}")
    print(f"   - Optional Actions: {len(batch2_summary['optional_actions'])}")
    
    # Get comprehensive summary (combines both batches)
    comprehensive = tp.get_comprehensive_summary(batch2_summary)
    
    print(f"\n🔄 COMPREHENSIVE SUMMARY (Both batches):")
    print(f"   - Required Actions: {len(comprehensive['required_actions'])}")
    print(f"   - Team Actions: {len(comprehensive['team_actions'])}")
    print(f"   - Optional Actions: {len(comprehensive['optional_actions'])}")
    
    # Save second batch
    tp.save_outstanding_tasks(batch2_summary, "2025-09-08 14:00:00")
    
    # Show updated statistics
    stats = tp.get_task_statistics()
    print(f"\n📊 After Batch 2:")
    print(f"   - Outstanding tasks: {stats['outstanding_total']}")
    print(f"   - Required actions: {stats['sections_breakdown']['required_actions']}")
    print(f"   - Team actions: {stats['sections_breakdown']['team_actions']}")
    print(f"   - Optional actions: {stats['sections_breakdown']['optional_actions']}")
    
    # Show detailed tasks
    outstanding = tp.load_outstanding_tasks()
    print(f"\n📋 DETAILED OUTSTANDING TASKS:")
    for section_key, tasks in outstanding.items():
        if tasks:
            print(f"\n   {section_key.replace('_', ' ').title()}:")
            for task in tasks:
                batch_count = task.get('batch_count', 1)
                task_id = task.get('task_id', 'N/A')
                print(f"   • [{batch_count}x batches] {task.get('subject', 'No subject')} (ID: {task_id})")
    
    # Demonstrate task completion
    print(f"\n✅ TASK COMPLETION DEMO:")
    
    # Get a task ID to mark complete
    security_task_id = None
    for task in outstanding.get('required_actions', []):
        if 'security training' in task.get('subject', '').lower():
            security_task_id = task.get('task_id')
            break
    
    if security_task_id:
        print(f"   Marking security training task (ID: {security_task_id}) as complete...")
        tp.mark_tasks_completed([security_task_id])
        
        # Show updated stats
        stats = tp.get_task_statistics()
        print(f"   Outstanding tasks after completion: {stats['outstanding_total']}")
        print(f"   Completed tasks: {stats['completed_total']}")
    
    print(f"\n🎯 FEATURE BENEFITS:")
    print(f"   • Tasks persist across email batches")
    print(f"   • Duplicate detection prevents task duplication")
    print(f"   • Batch counting shows task persistence")
    print(f"   • Task completion tracking and cleanup")
    print(f"   • Comprehensive view of all outstanding work")
    print(f"   • Statistics and aging alerts for old tasks")
    
    print(f"\n✨ Demo completed! Task persistence is working correctly.")

if __name__ == "__main__":
    demo_task_persistence()
