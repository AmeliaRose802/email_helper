"""Manually trigger task extraction for classified emails."""
import sys
import asyncio
sys.path.insert(0, '.')

from backend.database.connection import get_database_manager
from backend.services.task_extraction_service import extract_tasks_from_emails
from backend.core.dependencies import get_com_ai_service, get_email_provider

async def main():
    # Get the classified email IDs
    db = get_database_manager()
    conn = db.get_connection_sync()
    cursor = conn.cursor()
    
    # Get newsletter and FYI emails
    cursor.execute('''
        SELECT id FROM emails 
        WHERE ai_category IN ('newsletter', 'fyi')
    ''')
    email_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print(f"Found {len(email_ids)} emails to extract tasks from")
    print("Email IDs:", email_ids[:3], "...")
    
    # Get service instances
    ai_service = get_com_ai_service()
    email_provider = get_email_provider()
    
    # Extract tasks
    print("\nExtracting tasks...")
    result = await extract_tasks_from_emails(email_ids, ai_service, email_provider)
    
    print("\n✅ Task extraction complete!")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
