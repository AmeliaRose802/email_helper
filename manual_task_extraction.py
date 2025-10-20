#!/usr/bin/env python3
"""Manually extract and create tasks from all classified emails."""
import asyncio
import sqlite3
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.services.task_service import TaskService
from backend.services.com_ai_service import COMAIService
from backend.models.task import TaskCreate, TaskPriority, TaskStatus
from backend.database.connection import db_manager

async def main():
    print("🚀 Manual Task Extraction Script")
    print("=" * 80)
    
    # Get all classified emails
    with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            SELECT id, subject, sender, body, ai_category 
            FROM emails 
            WHERE ai_category IS NOT NULL AND ai_category != ''
            ORDER BY date DESC
        """)
        emails = cursor.fetchall()
    
    print(f"Found {len(emails)} classified emails")
    
    # Define categories
    ACTIONABLE_CATEGORIES = ['required_action', 'team_action', 'optional_action', 'required_personal_action']
    JOB_CATEGORIES = ['job_listing']
    EVENT_CATEGORIES = ['optional_event']
    SUMMARY_CATEGORIES = ['fyi', 'newsletter']
    
    # Initialize services
    task_service = TaskService()
    ai_service = COMAIService()
    
    tasks_created = 0
    summaries_created = 0
    errors = 0
    
    for email_row in emails:
        email_id, subject, sender, body, ai_category = email_row
        ai_category = ai_category.lower() if ai_category else ''
        
        try:
            print(f"\nProcessing: {subject[:50]}... (Category: {ai_category})")
            
            if ai_category in ACTIONABLE_CATEGORIES:
                # Extract action items
                email_text = f"Subject: {subject}\nFrom: {sender}\n\n{body}"
                action_result = await ai_service.extract_action_items(email_text)
                
                if action_result and action_result.get('action_required'):
                    priority = 'high' if ai_category in ['required_action', 'required_personal_action'] else 'medium'
                    
                    # Parse due date
                    due_date_str = action_result.get('due_date')
                    due_date = None
                    if due_date_str and due_date_str not in [None, 'No specific deadline', '', 'Unknown']:
                        try:
                            from dateutil import parser
                            due_date = parser.parse(due_date_str)
                        except:
                            due_date = None
                    
                    # Build description
                    description_parts = [f"Action: {action_result.get('action_required', '')}"]
                    if action_result.get('explanation'):
                        description_parts.append(f"\nDetails: {action_result['explanation']}")
                    if action_result.get('relevance'):
                        description_parts.append(f"\nRelevance: {action_result['relevance']}")
                    if action_result.get('links'):
                        description_parts.append(f"\nLinks: {', '.join(action_result['links'])}")
                    description_parts.append(f"\nSender: {sender}")
                    
                    task_data = TaskCreate(
                        title=subject[:200] if subject else 'Action Required',
                        description='\n'.join(description_parts),
                        status=TaskStatus.TODO,
                        priority=TaskPriority(priority),
                        category=ai_category,
                        email_id=email_id,
                        due_date=due_date,
                        tags=[ai_category, 'action_item'],
                        metadata={'sender': sender, 'links': action_result.get('links', [])}
                    )
                    
                    created_task = await task_service.create_task(task_data, user_id=1)
                    tasks_created += 1
                    print(f"  ✅ Created action task #{created_task.id}")
                else:
                    print(f"  ⚠️  No action items found")
                    
            elif ai_category in JOB_CATEGORIES:
                # Create job listing task
                email_text = f"Subject: {subject}\nFrom: {sender}\n\n{body}"
                action_result = await ai_service.extract_action_items(email_text)
                
                description_parts = [f"Job Listing: {subject}"]
                if action_result.get('explanation'):
                    description_parts.append(f"\nQualification Match: {action_result['explanation']}")
                if action_result.get('relevance'):
                    description_parts.append(f"\nRelevance: {action_result['relevance']}")
                if action_result.get('links'):
                    description_parts.append(f"\nApply: {', '.join(action_result['links'])}")
                description_parts.append(f"\nFrom: {sender}")
                
                task_data = TaskCreate(
                    title=f"💼 {subject[:190]}" if subject else '💼 Job Listing',
                    description='\n'.join(description_parts),
                    status=TaskStatus.TODO,
                    priority=TaskPriority.MEDIUM,
                    category='job_listing',
                    email_id=email_id,
                    tags=['job_listing', 'opportunity'],
                    metadata={'sender': sender, 'links': action_result.get('links', [])}
                )
                
                created_task = await task_service.create_task(task_data, user_id=1)
                tasks_created += 1
                print(f"  ✅ Created job task #{created_task.id}")
                
            elif ai_category in EVENT_CATEGORIES:
                # Create optional event task
                email_text = f"Subject: {subject}\nFrom: {sender}\n\n{body}"
                action_result = await ai_service.extract_action_items(email_text)
                
                description_parts = [f"Optional Event: {subject}"]
                if action_result.get('relevance'):
                    description_parts.append(f"\nRelevance: {action_result['relevance']}")
                if action_result.get('explanation'):
                    description_parts.append(f"\nDetails: {action_result['explanation']}")
                if action_result.get('links'):
                    description_parts.append(f"\nRegister: {', '.join(action_result['links'])}")
                description_parts.append(f"\nFrom: {sender}")
                
                task_data = TaskCreate(
                    title=f"🎪 {subject[:190]}" if subject else '🎪 Optional Event',
                    description='\n'.join(description_parts),
                    status=TaskStatus.TODO,
                    priority=TaskPriority.LOW,
                    category='optional_event',
                    email_id=email_id,
                    tags=['optional_event', 'networking'],
                    metadata={'sender': sender, 'links': action_result.get('links', [])}
                )
                
                created_task = await task_service.create_task(task_data, user_id=1)
                summaries_created += 1
                print(f"  ✅ Created event task #{created_task.id}")
                
            elif ai_category in SUMMARY_CATEGORIES:
                # Create informational tasks for FYI and newsletters
                email_text = f"Subject: {subject}\nFrom: {sender}\n\n{body}"
                
                if ai_category == 'newsletter':
                    summary_result = await ai_service.generate_summary(email_text, summary_type='detailed')
                    summary_text = summary_result.get('summary', 'Newsletter content')
                    
                    description_parts = [f"📰 Newsletter Summary"]
                    description_parts.append(f"\n{summary_text}")
                    if summary_result.get('key_points'):
                        description_parts.append(f"\n\nKey Points:")
                        for point in summary_result['key_points']:
                            description_parts.append(f"• {point}")
                    description_parts.append(f"\n\nFrom: {sender}")
                    
                    task_data = TaskCreate(
                        title=f"📰 {subject[:190]}" if subject else '📰 Newsletter',
                        description='\n'.join(description_parts),
                        status=TaskStatus.TODO,
                        priority=TaskPriority.LOW,
                        category='newsletter',
                        email_id=email_id,
                        tags=['newsletter', 'reading'],
                        metadata={'sender': sender, 'key_points': summary_result.get('key_points', [])}
                    )
                else:  # fyi
                    summary_result = await ai_service.generate_summary(email_text, summary_type='fyi')
                    summary_text = summary_result.get('summary', 'FYI information')
                    
                    description_parts = [f"📋 FYI: {summary_text}"]
                    description_parts.append(f"\nFrom: {sender}")
                    
                    task_data = TaskCreate(
                        title=f"📋 {subject[:195]}" if subject else '📋 FYI',
                        description='\n'.join(description_parts),
                        status=TaskStatus.TODO,
                        priority=TaskPriority.LOW,
                        category='fyi',
                        email_id=email_id,
                        tags=['fyi', 'information'],
                        metadata={'sender': sender}
                    )
                
                created_task = await task_service.create_task(task_data, user_id=1)
                summaries_created += 1
                print(f"  ✅ Created {ai_category} task #{created_task.id}")
            else:
                print(f"  ⏭️  Skipping category: {ai_category}")
                
            # Small delay to avoid overwhelming
            await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            errors += 1
            continue
    
    print("\n" + "=" * 80)
    print(f"✅ Task Extraction Complete!")
    print(f"   Tasks created: {tasks_created}")
    print(f"   Summaries created: {summaries_created}")
    print(f"   Errors: {errors}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
