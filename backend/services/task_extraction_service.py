"""Task extraction service for processing emails and creating tasks.

This service handles the extraction of tasks from classified emails,
including action items, job listings, events, and summaries.
"""

import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


async def extract_tasks_from_emails(
    email_ids: List[str],
    ai_service,
    provider
) -> Dict[str, Any]:
    """Extract tasks and summaries from emails asynchronously.

    This function processes emails to:
    1. Extract action items from actionable emails (required_action, team_action, etc.)
    2. Generate summaries for FYI items and newsletters
    3. Assess relevance for optional events and job listings
    4. Create task records in the database progressively with proper metadata

    Args:
        email_ids: List of email IDs to process
        ai_service: AI service instance for classification and extraction
        provider: Email provider instance

    Returns:
        Dictionary with processing status, counts, and timestamp
    """
    from backend.services.task_service import get_task_service

    # Categories that should generate tasks
    ACTIONABLE_CATEGORIES = ['required_personal_action', 'team_action', 'optional_action']
    JOB_CATEGORIES = ['job_listing']
    EVENT_CATEGORIES = ['optional_event']
    SUMMARY_CATEGORIES = ['fyi', 'newsletter']

    task_service_instance = get_task_service()
    tasks_created = 0
    summaries_created = 0

    logger.info(f"[Task Extraction] Starting background processing for {len(email_ids)} emails")

    # Perform holistic analysis first
    holistic_reclassifications = await _perform_holistic_analysis(email_ids, ai_service)

    # Process each email individually
    for email_id in email_ids:
        try:
            # Get email data from database
            email = await _get_email_from_db(email_id)
            if not email:
                continue

            # Apply holistic reclassification or use existing category
            ai_category = await _get_or_classify_email(
                email, email_id, holistic_reclassifications, ai_service
            )

            # Process based on category
            if ai_category in ACTIONABLE_CATEGORIES:
                if await _create_action_task(email, email_id, ai_service, task_service_instance):
                    tasks_created += 1

            elif ai_category in JOB_CATEGORIES:
                if await _create_job_listing_task(email, email_id, ai_service, task_service_instance):
                    tasks_created += 1

            elif ai_category in EVENT_CATEGORIES:
                if await _create_event_task(email, email_id, ai_service, task_service_instance):
                    summaries_created += 1

            elif ai_category in SUMMARY_CATEGORIES:
                if await _create_summary_task(email, email_id, ai_category, ai_service, task_service_instance):
                    summaries_created += 1

            # Rate limiting between emails
            await asyncio.sleep(2.0)

        except Exception as e:
            from backend.api.emails import _diagnose_error
            _diagnose_error(e, email_id, "email processing")
            continue

    logger.info(f"[Task Extraction] Completed: {tasks_created} tasks, {summaries_created} summaries created")

    return {
        "status": "completed",
        "message": f"Task extraction completed for {len(email_ids)} emails.",
        "email_count": len(email_ids),
        "tasks_created": tasks_created,
        "summaries_created": summaries_created,
        "timestamp": datetime.now().isoformat()
    }


async def _perform_holistic_analysis(email_ids: List[str], ai_service) -> Dict[str, str]:
    """Perform holistic analysis to detect expired items and superseded actions."""
    from backend.database.connection import db_manager

    holistic_reclassifications = {}

    try:
        # Fetch all emails for holistic analysis
        emails_for_analysis = []
        with db_manager.get_connection() as conn:
            placeholders = ','.join('?' * len(email_ids))
            cursor = conn.execute(
                f"SELECT id, subject, sender, body, date, ai_category FROM emails WHERE id IN ({placeholders})",
                email_ids
            )
            for row in cursor.fetchall():
                emails_for_analysis.append({
                    'id': row[0],
                    'subject': row[1],
                    'sender': row[2],
                    'body': row[3],
                    'date': row[4],
                    'ai_category': row[5]
                })

        if emails_for_analysis:
            logger.info(f"[Holistic Analysis] Analyzing {len(emails_for_analysis)} emails")
            holistic_result = await ai_service.analyze_holistically(emails_for_analysis)

            # Process expired items
            for expired in holistic_result.get('expired_items', []):
                email_id = expired.get('email_id')
                reason = expired.get('reason', 'Past deadline or event occurred')
                if email_id:
                    holistic_reclassifications[email_id] = 'spam_to_delete'
                    logger.info(f"[Holistic] 🗑️ Marking expired: {email_id[:30]}... - {reason}")

            # Process superseded actions
            for superseded in holistic_result.get('superseded_actions', []):
                original_id = superseded.get('original_email_id')
                if original_id:
                    holistic_reclassifications[original_id] = 'work_relevant'
                    logger.info(f"[Holistic] ♻️ Marking superseded: {original_id[:30]}...")

            # Process duplicates
            for dup_group in holistic_result.get('duplicate_groups', []):
                keep_id = dup_group.get('keep_email_id')
                archive_ids = dup_group.get('archive_email_ids', [])
                for archive_id in archive_ids:
                    if archive_id and archive_id != keep_id:
                        holistic_reclassifications[archive_id] = 'spam_to_delete'
                        logger.info(f"[Holistic] 📋 Archiving duplicate: {archive_id[:30]}...")

            logger.info(f"[Holistic Analysis] Complete: {len(holistic_reclassifications)} emails reclassified")
    except Exception as e:
        logger.warning(f"[Holistic Analysis] Failed (continuing with individual processing): {e}")

    return holistic_reclassifications


async def _get_email_from_db(email_id: str) -> Dict[str, Any]:
    """Fetch email data from database."""
    from backend.database.connection import db_manager

    with db_manager.get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, subject, sender, body, ai_category FROM emails WHERE id = ?",
            (email_id,)
        )
        row = cursor.fetchone()

    if not row:
        logger.warning(f"[Task Extraction] Email {email_id} not found in database")
        return None

    return {
        'id': row[0],
        'subject': row[1],
        'sender': row[2],
        'body': row[3],
        'ai_category': row[4]
    }


async def _get_or_classify_email(
    email: Dict[str, Any],
    email_id: str,
    holistic_reclassifications: Dict[str, str],
    ai_service
) -> str:
    """Get email category from holistic analysis, existing classification, or classify now."""
    from backend.database.connection import db_manager

    # Apply holistic reclassification if available
    if email_id in holistic_reclassifications:
        ai_category = holistic_reclassifications[email_id].lower()
        logger.info(f"[Holistic Override] Email {email_id[:30]}... reclassified to: {ai_category}")

        # Update database
        with db_manager.get_connection() as conn:
            conn.execute(
                "UPDATE emails SET ai_category = ? WHERE id = ?",
                (ai_category, email_id)
            )
            conn.commit()
        return ai_category

    # Use existing category
    ai_category = email.get('ai_category', '').lower()
    if ai_category:
        return ai_category

    # Classify now
    try:
        await asyncio.sleep(1.0)  # Rate limiting
        email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('body', '')}"
        classification_result = await ai_service.classify_email(email_content=email_text)
        return classification_result.get('category', '').lower()
    except Exception as e:
        logger.error(f"[Task Extraction] Failed to classify email {email_id}: {e}")
        return ''


def _is_fallback_response(action_result: Dict[str, Any]) -> bool:
    """Check if AI response is a fallback/error response."""
    if not action_result:
        return True

    action_text = action_result.get('action_required', '')
    if not action_text:
        return True

    fallback_phrases = [
        'unable to extract action items',
        'review email content',
        'unable to parse structured response',
        'ai processing unavailable',
        'content filter blocked'
    ]

    return any(phrase in action_text.lower() for phrase in fallback_phrases) or ('error' in action_result)


async def _create_action_task(
    email: Dict[str, Any],
    email_id: str,
    ai_service,
    task_service
) -> bool:
    """Create action item task from email."""
    from backend.models.task import TaskCreate, TaskPriority, TaskStatus
    from backend.api.emails import _diagnose_error

    try:
        await asyncio.sleep(1.5)  # Rate limiting

        email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('body', '')}"
        action_result = await ai_service.extract_action_items(email_text)

        if _is_fallback_response(action_result):
            logger.info(f"[Task Extraction] ⏭️ Skipped: Fallback response for {email_id[:30]}")
            return False

        action_text = action_result.get('action_required', '')
        logger.info(f"[Task Extraction] ✅ Extracted action: '{action_text[:80]}...' from {email_id[:30]}")

        # Determine priority
        priority = 'high' if 'urgent' in email.get('subject', '').lower() else 'medium'
        ai_category = email.get('ai_category', '')
        if ai_category == 'required_personal_action':
            priority = 'high'

        # Parse due date
        due_date = _parse_due_date(action_result.get('due_date'))

        # Build description
        description_parts = [f"Action: {action_text}"]
        if action_result.get('explanation'):
            description_parts.append(f"\nDetails: {action_result['explanation']}")
        if action_result.get('relevance'):
            description_parts.append(f"\nRelevance: {action_result['relevance']}")
        if action_result.get('links'):
            description_parts.append(f"\nLinks: {', '.join(action_result['links'])}")
        description_parts.append(f"\nSender: {email.get('sender', '')}")

        task_data = TaskCreate(
            title=email.get('subject', 'Action Required')[:200],
            description='\n'.join(description_parts),
            status=TaskStatus.TODO,
            priority=TaskPriority(priority),
            category=ai_category,
            email_id=email_id,
            due_date=due_date,
            tags=[ai_category, 'action_item'],
            metadata={'sender': email.get('sender', ''), 'links': action_result.get('links', [])}
        )

        created_task = await task_service.create_task(task_data, user_id=1)
        logger.info(f"[Task Extraction] Created task #{created_task.id} for email {email_id[:20]}...")
        return True

    except Exception as task_error:
        _diagnose_error(task_error, email_id, "action extraction")
        return False


async def _create_job_listing_task(
    email: Dict[str, Any],
    email_id: str,
    ai_service,
    task_service
) -> bool:
    """Create job listing task from email."""
    from backend.models.task import TaskCreate, TaskPriority, TaskStatus
    from backend.api.emails import _diagnose_error

    try:
        await asyncio.sleep(1.5)  # Rate limiting

        email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('body', '')}"
        action_result = await ai_service.extract_action_items(email_text)

        if _is_fallback_response(action_result):
            logger.info(f"[Task Extraction] Skipping job listing due to fallback: {email_id[:30]}")
            return False

        description_parts = [f"Job Listing: {email.get('subject', '')}"]
        if action_result.get('explanation'):
            description_parts.append(f"\nQualification Match: {action_result['explanation']}")
        if action_result.get('relevance'):
            description_parts.append(f"\nRelevance: {action_result['relevance']}")
        if action_result.get('links'):
            description_parts.append(f"\nApply: {', '.join(action_result['links'])}")
        description_parts.append(f"\nFrom: {email.get('sender', '')}")

        due_date = _parse_due_date(action_result.get('due_date'))

        task_data = TaskCreate(
            title=f"💼 {email.get('subject', 'Job Listing')[:190]}",
            description='\n'.join(description_parts),
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            category='job_listing',
            email_id=email_id,
            due_date=due_date,
            tags=['job_listing', 'opportunity'],
            metadata={'sender': email.get('sender', ''), 'links': action_result.get('links', [])}
        )

        await task_service.create_task(task_data, user_id=1)
        logger.info(f"[Task Extraction] Created job listing task for email {email_id[:20]}...")
        return True

    except Exception as job_error:
        _diagnose_error(job_error, email_id, "job listing extraction")
        return False


async def _create_event_task(
    email: Dict[str, Any],
    email_id: str,
    ai_service,
    task_service
) -> bool:
    """Create optional event task from email."""
    from backend.models.task import TaskCreate, TaskPriority, TaskStatus
    from backend.api.emails import _diagnose_error

    try:
        await asyncio.sleep(1.5)  # Rate limiting

        email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('body', '')}"
        action_result = await ai_service.extract_action_items(email_text)

        if _is_fallback_response(action_result):
            logger.info(f"[Task Extraction] Skipping event due to fallback: {email_id[:30]}")
            return False

        description_parts = [f"Optional Event: {email.get('subject', '')}"]
        if action_result.get('relevance'):
            description_parts.append(f"\nRelevance: {action_result['relevance']}")
        if action_result.get('explanation'):
            description_parts.append(f"\nDetails: {action_result['explanation']}")
        if action_result.get('links'):
            description_parts.append(f"\nRegister: {', '.join(action_result['links'])}")
        description_parts.append(f"\nFrom: {email.get('sender', '')}")

        event_date = _parse_due_date(action_result.get('due_date'))

        task_data = TaskCreate(
            title=f"🎪 {email.get('subject', 'Optional Event')[:190]}",
            description='\n'.join(description_parts),
            status=TaskStatus.TODO,
            priority=TaskPriority.LOW,
            category='optional_event',
            email_id=email_id,
            due_date=event_date,
            tags=['optional_event', 'networking'],
            metadata={'sender': email.get('sender', ''), 'links': action_result.get('links', [])}
        )

        await task_service.create_task(task_data, user_id=1)
        logger.info(f"[Task Extraction] Created event task for email {email_id[:20]}...")
        return True

    except Exception as event_error:
        _diagnose_error(event_error, email_id, "event extraction")
        return False


async def _create_summary_task(
    email: Dict[str, Any],
    email_id: str,
    ai_category: str,
    ai_service,
    task_service
) -> bool:
    """Create informational task for FYI or newsletter."""
    from backend.models.task import TaskCreate, TaskPriority, TaskStatus
    from backend.api.emails import _diagnose_error

    try:
        await asyncio.sleep(1.5)  # Rate limiting

        email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('body', '')}"

        if ai_category == 'newsletter':
            summary_result = await ai_service.generate_summary(email_text, summary_type='detailed')
            summary_text = summary_result.get('summary', 'Newsletter content')

            description_parts = ["📰 Newsletter Summary", f"\n{summary_text}"]
            if summary_result.get('key_points'):
                description_parts.append("\n\nKey Points:")
                for point in summary_result['key_points']:
                    description_parts.append(f"• {point}")
            description_parts.append(f"\n\nFrom: {email.get('sender', '')}")

            task_data = TaskCreate(
                title=f"📰 {email.get('subject', 'Newsletter')[:190]}",
                description='\n'.join(description_parts),
                status=TaskStatus.TODO,
                priority=TaskPriority.LOW,
                category='newsletter',
                email_id=email_id,
                tags=['newsletter', 'reading'],
                metadata={'sender': email.get('sender', ''), 'key_points': summary_result.get('key_points', [])}
            )
        else:  # fyi
            summary_result = await ai_service.generate_summary(email_text, summary_type='fyi')
            summary_text = summary_result.get('summary', 'FYI information')

            description_parts = [f"📋 FYI: {summary_text}", f"\nFrom: {email.get('sender', '')}"]

            task_data = TaskCreate(
                title=f"📋 {email.get('subject', 'FYI')[:195]}",
                description='\n'.join(description_parts),
                status=TaskStatus.TODO,
                priority=TaskPriority.LOW,
                category='fyi',
                email_id=email_id,
                tags=['fyi', 'information'],
                metadata={'sender': email.get('sender', '')}
            )

        await task_service.create_task(task_data, user_id=1)
        logger.info(f"[Task Extraction] Created {ai_category} summary for email {email_id[:20]}...")
        return True

    except Exception as summary_error:
        _diagnose_error(summary_error, email_id, f"{ai_category} summary generation")
        return False


def _parse_due_date(due_date_str: str):
    """Parse due date string into datetime object."""
    if not due_date_str or due_date_str in ['No specific deadline', '', 'Unknown']:
        return None

    try:
        from dateutil import parser
        return parser.parse(due_date_str)
    except Exception:
        return None
