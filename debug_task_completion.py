#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))
from task_persistence import TaskPersistence

# Create test data like in the test
tp = TaskPersistence(os.path.join('test', 'test_data', 'debug_task_ids'))
os.makedirs(os.path.join('test', 'test_data', 'debug_task_ids'), exist_ok=True)

test_data = {
    'optional_actions': [
        {'task_id': 'opt1', 'subject': 'Test Optional Action', 'sender': 'test@example.com'}
    ]
}

tp.save_outstanding_tasks(test_data, '2025-01-01 12:00:00')
outstanding = tp.load_outstanding_tasks()
print('Outstanding tasks:')
for task in outstanding['optional_actions']:
    task_id = task.get('task_id')
    subject = task.get('subject')
    print(f'  Task ID: {task_id}, Subject: {subject}')

# Try to mark it complete
print('\nMarking task complete...')
tp.mark_tasks_completed(['opt1'])

outstanding_after = tp.load_outstanding_tasks()
print(f'Tasks after completion: {len(outstanding_after["optional_actions"])}')

if outstanding_after["optional_actions"]:
    print("Remaining task:")
    for task in outstanding_after["optional_actions"]:
        print(f'  Task ID: {task.get("task_id")}, Subject: {task.get("subject")}')