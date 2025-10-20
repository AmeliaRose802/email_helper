import sqlite3

conn = sqlite3.connect('./runtime_data/database/email_helper.db')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print('Tables:', tables)

# Check tasks table schema
if 'tasks' in tables:
    cursor = conn.execute("PRAGMA table_info(tasks)")
    columns = cursor.fetchall()
    print('\nTasks table columns:')
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Count rows
    cursor = conn.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    print(f"\nTotal tasks: {count}")
else:
    print('\nTasks table does NOT exist!')

conn.close()
