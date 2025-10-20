import sqlite3
from datetime import datetime

conn = sqlite3.connect('./runtime_data/database/email_helper.db')

# Create default localhost user
conn.execute('''
    INSERT OR IGNORE INTO users (id, username, email, hashed_password, created_at, is_active)
    VALUES (1, 'localhost', 'localhost@email-helper.local', 'hashed_password', ?, 1)
''', (datetime.now(),))

conn.commit()

# Verify
cursor = conn.execute('SELECT id, username, email FROM users')
users = cursor.fetchall()
print(f'Users in database: {len(users)}')
for user in users:
    print(f'  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}')

conn.close()
