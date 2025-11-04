"""Email analysis and sync endpoints for FastAPI Email Helper API."""

from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks
import logging

from backend.services.email_provider import EmailProvider
from backend.core.dependencies import get_email_provider, get_ai_service
from backend.models.email_requests import BulkApplyRequest, SyncEmailRequest

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post('/emails/extract-tasks')
async def extract_tasks_from_emails(
    request: BulkApplyRequest = Body(...),
    background_tasks: BackgroundTasks = None,
    provider: EmailProvider = Depends(get_email_provider),
    ai_service = Depends(get_ai_service)
):
    '''Extract tasks and summaries from emails asynchronously in background.

    This endpoint triggers background processing to:
    1. Extract action items from actionable emails (required_action, team_action, etc.)
    2. Generate summaries for FYI items and newsletters
    3. Assess relevance for optional events and job listings
    4. Create task records in the database progressively with proper metadata

    This runs asynchronously so users can continue working while tasks are extracted.

    Args:
        request: Request with email IDs to process
        provider: Email provider instance
        ai_service: AI service instance

    Returns:
        Status message indicating background processing has started
    '''
    from backend.services.task_extraction_service import extract_tasks_from_emails as extract_tasks

    if not request.email_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No email IDs provided'
        )

    try:
        result = await extract_tasks(request.email_ids, ai_service, provider)
        logger.info('[Task Extraction] Completed successfully')
        return result
    except Exception as e:
        logger.error(f'[Task Extraction] CRITICAL ERROR: {e}', exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f'Task extraction failed: {str(e)}'
        )


@router.post('/emails/sync-to-database')
async def sync_emails_to_database(
    request: SyncEmailRequest,
    provider: EmailProvider = Depends(get_email_provider)
):
    '''Sync classified emails from frontend to database.

    This stores classified emails in the database so they can be used for
    task extraction, analytics, and persistence.

    Args:
        request: List of classified emails with AI categories
        provider: Email provider instance

    Returns:
        Status of sync operation
    '''
    from backend.database.connection import db_manager

    if not request.emails:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No emails provided'
        )

    try:
        synced_count = 0
        errors = []

        with db_manager.get_connection() as conn:
            # Add columns if they don't exist
            try:
                conn.execute('ALTER TABLE emails ADD COLUMN ai_category TEXT')
                conn.execute('ALTER TABLE emails ADD COLUMN ai_confidence REAL')
                conn.execute('ALTER TABLE emails ADD COLUMN ai_reasoning TEXT')
                conn.execute('ALTER TABLE emails ADD COLUMN one_line_summary TEXT')
                conn.execute('ALTER TABLE emails ADD COLUMN body TEXT')
                conn.execute('ALTER TABLE emails ADD COLUMN date TIMESTAMP')
                conn.execute('ALTER TABLE emails ADD COLUMN conversation_id TEXT')
                conn.commit()
                logger.info('[DB] Added AI classification columns to emails table')
            except Exception:
                pass

            for email_data in request.emails:
                try:
                    email_id = email_data.get('id')
                    if not email_id:
                        continue

                    cursor = conn.execute('SELECT id FROM emails WHERE id = ?', (email_id,))
                    exists = cursor.fetchone() is not None

                    if exists:
                        conn.execute(
                            '''
                            UPDATE emails 
                            SET ai_category = ?, 
                                ai_confidence = ?, 
                                ai_reasoning = ?,
                                one_line_summary = ?,
                                processed_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                            ''',
                            (
                                email_data.get('ai_category'),
                                email_data.get('ai_confidence'),
                                email_data.get('ai_reasoning'),
                                email_data.get('one_line_summary'),
                                email_id
                            )
                        )
                    else:
                        conn.execute(
                            '''
                            INSERT INTO emails (
                                id, subject, sender, recipient, content, body, 
                                received_date, date, category, ai_category, 
                                confidence, ai_confidence, ai_reasoning, 
                                one_line_summary, conversation_id, user_id, processed_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            ''',
                            (
                                email_id,
                                email_data.get('subject', ''),
                                email_data.get('sender', ''),
                                email_data.get('recipient', ''),
                                email_data.get('body', ''),
                                email_data.get('body', ''),
                                email_data.get('date'),
                                email_data.get('date'),
                                email_data.get('ai_category'),
                                email_data.get('ai_category'),
                                email_data.get('ai_confidence', 0.0),
                                email_data.get('ai_confidence', 0.0),
                                email_data.get('ai_reasoning', ''),
                                email_data.get('one_line_summary', ''),
                                email_data.get('conversation_id'),
                                1
                            )
                        )

                    synced_count += 1

                except Exception as e:
                    error_msg = f"Failed to sync email {email_data.get('id', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            conn.commit()

        return {
            'success': True,
            'message': f'Synced {synced_count} emails to database',
            'synced_count': synced_count,
            'failed_count': len(errors),
            'errors': errors if errors else None
        }

    except Exception as e:
        logger.error(f'[Sync] Failed to sync emails: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to sync emails: {str(e)}'
        )


@router.post('/emails/analyze-holistically')
async def analyze_holistically(
    request: SyncEmailRequest,
    ai_service = Depends(get_ai_service)
):
    '''Perform holistic analysis across multiple emails.

    This endpoint analyzes all provided emails together to identify:
    - Truly relevant actions that require attention
    - Superseded actions that have been resolved by newer emails
    - Duplicate email groups
    - Expired items past their deadline

    Args:
        request: List of emails to analyze holistically
        ai_service: AI service instance

    Returns:
        Holistic analysis results with categorized emails
    '''
    if not request.emails:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No emails provided'
        )

    try:
        logger.info(f'[Holistic Analysis] Starting analysis for {len(request.emails)} emails')

        analysis_result = await ai_service.analyze_holistically(request.emails)

        logger.info('[Holistic Analysis] Completed successfully')
        logger.debug(f'[Holistic Analysis] Results: {analysis_result}')

        return analysis_result

    except Exception as e:
        logger.error(f'[Holistic Analysis] Failed: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to perform holistic analysis: {str(e)}'
        )
