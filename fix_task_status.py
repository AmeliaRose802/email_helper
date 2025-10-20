"""Fix task status from pending to todo."""
import sqlite3

# Connect to database
conn = sqlite3.connect('runtime_data/email_helper_history.db')
cursor = conn.cursor()

# Check current tasks
cursor.execute('SELECT id, title, status FROM tasks')
tasks = cursor.fetchall()
print(f"Found {len(tasks)} tasks:")
for task in tasks:
    print(f"  ID={task[0]}, Title={task[1]}, Status={task[2]}")

# Update pending to todo
cursor.execute('UPDATE tasks SET status = ? WHERE status = ?', ('todo', 'pending'))
conn.commit()
print(f"\nUpdated {cursor.rowcount} tasks from 'pending' to 'todo'")

# Verify update
cursor.execute('SELECT id, title, status FROM tasks')
tasks = cursor.fetchall()
print(f"\nTasks after update:")
for task in tasks:
    print(f"  ID={task[0]}, Title={task[1]}, Status={task[2]}")

conn.close()
print("\nDone!")
