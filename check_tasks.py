"""Quick script to check task categories in database."""
import sys
sys.path.insert(0, '.')
from backend.database.connection import get_database_manager

db_manager = get_database_manager()
conn = db_manager.get_connection_sync()
cursor = conn.cursor()

# Check for newsletter tasks
cursor.execute('SELECT COUNT(*) FROM tasks WHERE category = ?', ('newsletter',))
newsletter_count = cursor.fetchone()[0]
print(f'Newsletter tasks: {newsletter_count}')

# Check for FYI tasks
cursor.execute('SELECT COUNT(*) FROM tasks WHERE category = ?', ('fyi',))
fyi_count = cursor.fetchone()[0]
print(f'FYI tasks: {fyi_count}')

# Check all categories
cursor.execute('SELECT category, COUNT(*) FROM tasks GROUP BY category')
categories = cursor.fetchall()
print('\nAll categories:')
for cat, count in categories:
    print(f'  - {cat if cat else "(null)"}: {count}')

# Show sample tasks
print('\nSample tasks:')
cursor.execute('SELECT id, title, category, status FROM tasks LIMIT 10')
tasks = cursor.fetchall()
for task in tasks:
    print(f'  Task {task[0]}: {task[1][:50]} | category={task[2]} | status={task[3]}')

conn.close()
