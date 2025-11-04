"""Check which emails are ready for task extraction."""
import sys
sys.path.insert(0, '.')
from backend.database.connection import get_database_manager

db_manager = get_database_manager()
conn = db_manager.get_connection_sync()
cursor = conn.cursor()

# Check for emails with AI categories that could generate tasks
print("=== Emails categorized as NEWSLETTER ===")
cursor.execute('''
    SELECT id, subject, sender, ai_category 
    FROM emails 
    WHERE ai_category = 'newsletter' 
    LIMIT 5
''')
newsletters = cursor.fetchall()
print(f"Found {len(newsletters)} newsletter emails")
for email in newsletters:
    print(f"  {email[0][:20]}... | {email[1][:40]} | {email[2][:30]}")

print("\n=== Emails categorized as FYI ===")
cursor.execute('''
    SELECT id, subject, sender, ai_category 
    FROM emails 
    WHERE ai_category = 'fyi' 
    LIMIT 5
''')
fyis = cursor.fetchall()
print(f"Found {len(fyis)} FYI emails")
for email in fyis:
    print(f"  {email[0][:20]}... | {email[1][:40]} | {email[2][:30]}")

print("\n=== All AI categories in database ===")
cursor.execute('''
    SELECT ai_category, COUNT(*) 
    FROM emails 
    WHERE ai_category IS NOT NULL AND ai_category != ''
    GROUP BY ai_category
''')
categories = cursor.fetchall()
for cat, count in categories:
    print(f"  {cat}: {count}")

print("\n=== Total emails with AI categories ===")
cursor.execute('''
    SELECT COUNT(*) 
    FROM emails 
    WHERE ai_category IS NOT NULL AND ai_category != ''
''')
total = cursor.fetchone()[0]
print(f"Total: {total}")

conn.close()
