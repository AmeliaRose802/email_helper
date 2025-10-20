import sqlite3

conn = sqlite3.connect('./runtime_data/database/email_helper.db')

# Check current schema
cursor = conn.execute("PRAGMA table_info(tasks)")
columns = cursor.fetchall()
print('Current tasks table columns:')
column_names = []
for col in columns:
    print(f"  {col[1]} ({col[2]})")
    column_names.append(col[1])

# Add missing columns if they don't exist
if 'category' not in column_names:
    print('\nAdding category column...')
    conn.execute('ALTER TABLE tasks ADD COLUMN category TEXT')
    print('✓ category column added')
else:
    print('\n✓ category column already exists')

if 'tags' not in column_names:
    print('\nAdding tags column...')
    conn.execute('ALTER TABLE tasks ADD COLUMN tags TEXT')
    print('✓ tags column added')
else:
    print('\n✓ tags column already exists')

if 'metadata' not in column_names:
    print('\nAdding metadata column...')
    conn.execute('ALTER TABLE tasks ADD COLUMN metadata TEXT')
    print('✓ metadata column added')
else:
    print('\n✓ metadata column already exists')

conn.commit()

# Verify
cursor = conn.execute("PRAGMA table_info(tasks)")
columns = cursor.fetchall()
print('\nFinal tasks table columns:')
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
print('\nDatabase schema update complete!')
