"""Email endpoints for FastAPI Email Helper API."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, BackgroundTasks
import logging
import time
from functools import wraps

from backend.services.email_provider import EmailProvider
from backend.core.dependencies import get_email_provider, get_ai_service
from backend.models.email import Email, EmailBatch, EmailBatchResult
from backend.models.email_requests import (
    EmailListResponse,
    EmailFolderResponse,
    EmailOperationResponse,
    UpdateClassificationRequest,
    CategoryFolderMapping,
    BulkApplyRequest,
    BulkApplyResponse,
    ConversationResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _diagnose_error(error: Exception, email_id: str, context: str = "processing") -> None:
    """Diagnose and log API/AI errors with specific error type identification.
    
    Args:
        error: The exception that occurred
        email_id: ID of the email being processed (truncated for logging)
        context: Description of what was being done (e.g., "action extraction", "classification")
    """
    error_type = type(error).__name__
    error_msg = str(error).lower()
    email_short = email_id[:30] if len(email_id) > 30 else email_id
    
    if 'content_filter' in error_msg or 'responsibleaipolicyviolation' in error_msg or 'content management policy' in error_msg:
        logger.warning(f"[Task Extraction] ⚠️ CONTENT FILTER blocked {context} for {email_short}: {error}")
    elif 'rate' in error_msg or 'quota' in error_msg or '429' in error_msg or 'throttl' in error_msg:
        logger.warning(f"[Task Extraction] ⏱️ RATE LIMIT hit during {context} for {email_short}: {error}")
    elif 'timeout' in error_msg or 'connection' in error_msg or 'network' in error_msg:
        logger.warning(f"[Task Extraction] 🔌 CONNECTION ERROR during {context} for {email_short}: {error}")
    elif 'badrequest' in error_msg or 'invalid' in error_msg:
        logger.warning(f"[Task Extraction] ⚠️ BAD REQUEST during {context} for {email_short}: {error}")
    else:
        logger.error(f"[Task Extraction] ❌ UNEXPECTED ERROR ({error_type}) during {context} for {email_short}: {error}")


def handle_errors(default_message: str = "Operation failed"):
    """Decorator to handle common error patterns in endpoints."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"{func.__name__} failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{default_message}: {str(e)}"
                )
        return wrapper
    return decorator


@router.get("/emails", response_model=EmailListResponse)
async def get_emails(
    folder: str = Query("Inbox", description="Email folder name"),
    limit: int = Query(50000, ge=1, le=50000, description="Number of emails to retrieve"),
    offset: int = Query(0, ge=0, description="Number of emails to skip"),
    category: Optional[str] = Query(None, description="Filter by AI category"),
    source: str = Query("outlook", description="Data source: 'outlook' or 'database'"),
    provider: EmailProvider = Depends(get_email_provider)
):
    """Get paginated list of emails from specified source.
    
    Args:
        folder: Name of the email folder (default: Inbox) - for Outlook source
        limit: Maximum number of emails to return
        offset: Number of emails to skip for pagination
        category: Filter by AI category (only for database source)
        source: Data source - 'outlook' for live Outlook emails, 'database' for classified emails
        provider: Email provider instance
    
    Returns:
        Paginated list of emails with metadata
    """
    try:
        if source == "database":
            # Get emails from database with AI classifications
            from backend.database.connection import db_manager
            
            with db_manager.get_connection() as conn:
                # Build query with optional category filter
                where_clause = "WHERE 1=1"
                params = []
                
                if category:
                    where_clause += " AND ai_category = ?"
                    params.append(category)
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM emails {where_clause}"
                cursor = conn.execute(count_query, params)
                total = cursor.fetchone()[0]
                
                # Get emails
                query = f"""
                    SELECT id, subject, sender, recipient, body, content, date, received_date,
                           ai_category, ai_confidence, ai_reasoning, one_line_summary,
                           conversation_id
                    FROM emails
                    {where_clause}
                    ORDER BY date DESC
                    LIMIT ? OFFSET ?
                """
                params.extend([limit, offset])
                cursor = conn.execute(query, params)
                
                rows = cursor.fetchall()
                emails = []
                for row in rows:
                    row_dict = dict(row)
                    # Ensure required fields exist
                    email = {
                        'id': row_dict.get('id'),
                        'subject': row_dict.get('subject'),
                        'sender': row_dict.get('sender'),
                        'recipient': row_dict.get('recipient'),
                        'body': row_dict.get('body') or row_dict.get('content'),
                        'received_time': row_dict.get('date') or row_dict.get('received_date'),
                        'date': row_dict.get('date') or row_dict.get('received_date'),
                        'ai_category': row_dict.get('ai_category'),
                        'ai_confidence': row_dict.get('ai_confidence'),
                        'ai_reasoning': row_dict.get('ai_reasoning'),
                        'one_line_summary': row_dict.get('one_line_summary'),
                        'conversation_id': row_dict.get('conversation_id'),
                        'is_read': True,  # Assume read if in database
                        'has_attachments': False,
                        'importance': 'Normal',
                        'categories': []
                    }
                    emails.append(email)
                
                return EmailListResponse(
                    emails=emails,
                    total=total,
                    offset=offset,
                    limit=limit,
                    has_more=(offset + len(emails)) < total
                )
        else:
            # Get emails from Outlook
            emails = provider.get_emails(
                folder_name=folder,
                count=limit,
                offset=offset
            )
            
            # Calculate conversation counts by grouping emails
            conversation_counts = {}
            for email in emails:
                conv_id = email.get('conversation_id')
                if conv_id:
                    conversation_counts[conv_id] = conversation_counts.get(conv_id, 0) + 1
            
            # Add conversation_count to each email
            for email in emails:
                conv_id = email.get('conversation_id')
                if conv_id and conv_id in conversation_counts:
                    email['conversation_count'] = conversation_counts[conv_id]
                else:
                    email['conversation_count'] = 1  # Single email, not part of thread
            
            # Calculate if there are more emails
            has_more = len(emails) == limit
            
            return EmailListResponse(
                emails=emails,
                total=len(emails),
                offset=offset,
                limit=limit,
                has_more=has_more
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve emails: {str(e)}"
        )


@router.get("/emails/search", response_model=EmailListResponse)
async def search_emails(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    provider: EmailProvider = Depends(get_email_provider)
):
    """Search emails by query string.
    
    Args:
        q: Search query text
        page: Page number for pagination
        per_page: Number of results per page
        provider: Email provider instance
    
    Returns:
        Search results with pagination metadata
    """
    try:
        # Calculate offset from page number
        offset = (page - 1) * per_page
        
        # Get all emails and filter by search query
        # Note: This is a simplified implementation. In production, you'd want
        # to use a proper search index or database query
        all_emails = provider.get_emails(folder_name="Inbox", count=500)
        
        # Simple search: check if query appears in subject, sender, or body
        query_lower = q.lower()
        filtered_emails = [
            email for email in all_emails
            if (query_lower in email.get('subject', '').lower() or
                query_lower in email.get('sender', '').lower() or
                query_lower in email.get('body', '').lower())
        ]
        
        # Apply pagination
        total_results = len(filtered_emails)
        paginated_emails = filtered_emails[offset:offset + per_page]
        has_more = (offset + per_page) < total_results
        
        return EmailListResponse(
            emails=paginated_emails,
            total=total_results,
            offset=offset,
            limit=per_page,
            has_more=has_more
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search emails: {str(e)}"
        )


@router.get("/emails/stats")
async def get_email_stats(
    limit: int = Query(100, ge=10, le=1000, description="Number of emails to process for stats"),
    provider: EmailProvider = Depends(get_email_provider)
):
    """Get email statistics for the current user.
    
    Args:
        limit: Maximum number of emails to process (10-1000, default: 100)
    """
    try:
        logger.info("Getting email stats for localhost user (limit: %d)", limit)
        
        # Get emails from inbox to calculate stats
        emails = provider.get_emails(folder_name="Inbox", count=limit)
        logger.info("Retrieved %d emails from inbox", len(emails))
        
        total_emails = len(emails)
        unread_emails = sum(1 for email in emails if not email.get("is_read", False))
        
        # Get folder counts (simplified)
        folders = provider.get_folders()
        emails_by_folder = {}
        for folder in folders[:5]:  # Limit to top 5 folders
            folder_name = folder.get("name", "Unknown")
            try:
                folder_emails = provider.get_emails(folder_name=folder_name, count=100)
                emails_by_folder[folder_name] = len(folder_emails)
            except Exception:
                emails_by_folder[folder_name] = 0
        
        # Count by sender (top 5)
        sender_counts = {}
        for email in emails[:100]:  # Limit to recent 100 emails
            sender = email.get("sender", "Unknown")
            sender_counts[sender] = sender_counts.get(sender, 0) + 1
        
        # Get top 5 senders
        emails_by_sender = dict(
            sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        )
        
        logger.info("Email stats calculated successfully")
        return {
            "total_emails": total_emails,
            "unread_emails": unread_emails,
            "emails_by_folder": emails_by_folder,
            "emails_by_sender": emails_by_sender
        }
    except Exception as e:
        # Log the error but don't crash the app
        logger.error("Failed to get email stats: %s", str(e), exc_info=True)
        # Return empty stats instead of raising error
        return {
            "total_emails": 0,
            "unread_emails": 0,
            "emails_by_folder": {},
            "emails_by_sender": {},
            "error": str(e)  # Include error in response for debugging
        }


@router.get("/emails/category-mappings", response_model=List[CategoryFolderMapping])
async def get_category_mappings():
    """Get the mapping of AI categories to Outlook folders.
    
    Returns:
        List of category mappings with folder names and inbox status
    """
    # Import categories from com_email_provider to ensure consistency
    from backend.services.com_email_provider import INBOX_CATEGORIES, NON_INBOX_CATEGORIES
    
    mappings = []
    for category, folder_name in INBOX_CATEGORIES.items():
        mappings.append(CategoryFolderMapping(
            category=category,
            folder_name=folder_name,
            stays_in_inbox=True
        ))
    
    for category, folder_name in NON_INBOX_CATEGORIES.items():
        mappings.append(CategoryFolderMapping(
            category=category,
            folder_name=folder_name,
            stays_in_inbox=False
        ))
    
    return mappings


@router.get("/emails/accuracy-stats")
async def get_accuracy_stats(
    provider: EmailProvider = Depends(get_email_provider)
):
    """Get AI classification accuracy statistics.
    
    Calculates accuracy metrics by comparing ai_category with category (user-corrected).
    
    Returns:
        Dictionary with overall and per-category accuracy statistics including:
        - total emails analyzed
        - overall accuracy percentage
        - per-category stats (total, correct, accuracy, precision, recall, f1)
    """
    from backend.services.accuracy_service import calculate_accuracy_stats
    
    try:
        return calculate_accuracy_stats()
    except Exception as e:
        logger.error(f"[Accuracy Stats] Failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate accuracy stats: {str(e)}"
        )


@router.post("/emails/prefetch")
async def prefetch_emails(
    email_ids: List[str] = Body(...),
    provider: EmailProvider = Depends(get_email_provider)
):
    """Prefetch multiple emails by their IDs for background loading.
    
    This endpoint fetches the full content of multiple emails in one request,
    useful for prefetching the next page of emails in the background.
    
    Args:
        email_ids: List of email IDs to prefetch
        provider: Email provider instance
    
    Returns:
        Dictionary with fetched emails and success/error counts
    """
    try:
        emails = []
        success_count = 0
        error_count = 0
        errors = []
        
        for email_id in email_ids:
            try:
                email = await provider.get_email_content(email_id)
                if email:
                    emails.append(email)
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"Email {email_id} not found")
            except Exception as e:
                error_count += 1
                errors.append(f"Failed to fetch email {email_id}: {str(e)}")
                logger.error(f"Error prefetching email {email_id}: {e}")
        
        return {
            "emails": emails,
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors if errors else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to prefetch emails: {str(e)}"
        )


@router.get("/emails/{email_id}", response_model=Dict[str, Any])
@handle_errors("Failed to retrieve email")
async def get_email(
    email_id: str,
    provider: EmailProvider = Depends(get_email_provider)
):
    """Get specific email by ID with full content.
    
    Args:
        email_id: Unique email identifier
        current_user: Authenticated user
        provider: Email provider instance
    
    Returns:
        Full email data including body content
    """
    import time
    start_time = time.time()
    
    email = provider.get_email_content(email_id)
    
    elapsed = time.time() - start_time
    if elapsed > 1.0:  # Log if slower than 1 second
        print(f"⚠️ Slow email fetch: {email_id} took {elapsed:.2f}s")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email with ID '{email_id}' not found"
        )
    
    return email


@router.put("/emails/{email_id}/read", response_model=EmailOperationResponse)
@handle_errors("Failed to update email read status")
async def update_email_read_status(
    email_id: str,
    read: bool = Query(True, description="Read status to set"),
    provider: EmailProvider = Depends(get_email_provider)
):
    """Update email read status.
    
    Args:
        email_id: Unique email identifier
        read: True to mark as read, False to mark as unread
        provider: Email provider instance
    
    Returns:
        Operation result
    """
    if read:
        success = provider.mark_as_read(email_id)
        message = "Email marked as read successfully" if success else "Failed to mark email as read"
    else:
        success = provider.mark_as_unread(email_id) if hasattr(provider, 'mark_as_unread') else False
        message = "Email marked as unread successfully" if success else "Failed to mark email as unread"
    
    return EmailOperationResponse(
        success=success,
        message=message,
        email_id=email_id
    )


@router.post("/emails/{email_id}/mark-read", response_model=EmailOperationResponse)
@handle_errors("Failed to mark email as read")
async def mark_email_as_read(
    email_id: str,
    provider: EmailProvider = Depends(get_email_provider)
):
    """Mark email as read (deprecated - use PUT /emails/{email_id}/read instead).
    
    Args:
        email_id: Unique email identifier
        current_user: Authenticated user
        provider: Email provider instance
    
    Returns:
        Operation result
    """
    success = provider.mark_as_read(email_id)
    
    return EmailOperationResponse(
        success=success,
        message="Email marked as read successfully" if success else "Failed to mark email as read",
        email_id=email_id
    )


@router.post("/emails/{email_id}/move", response_model=EmailOperationResponse)
@handle_errors("Failed to move email")
async def move_email(
    email_id: str,
    destination_folder: str = Query(..., description="Destination folder name"),
    provider: EmailProvider = Depends(get_email_provider)
):
    """Move email to another folder.
    
    Args:
        email_id: Unique email identifier
        destination_folder: Name of destination folder
        current_user: Authenticated user
        provider: Email provider instance
    
    Returns:
        Operation result
    """
    success = provider.move_email(email_id, destination_folder)
    
    return EmailOperationResponse(
        success=success,
        message=f"Email moved to '{destination_folder}' successfully" if success else f"Failed to move email to '{destination_folder}'",
        email_id=email_id
    )


@router.get("/folders", response_model=EmailFolderResponse)
@handle_errors("Failed to retrieve folders")
async def get_folders(
    provider: EmailProvider = Depends(get_email_provider)
):
    """Get list of available email folders.
    
    Args:
        current_user: Authenticated user
        provider: Email provider instance
    
    Returns:
        List of available folders with metadata
    """
    folders = provider.get_folders()
    
    return EmailFolderResponse(
        folders=folders,
        total=len(folders)
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
@handle_errors("Failed to retrieve conversation")
async def get_conversation_thread(
    conversation_id: str,
    provider: EmailProvider = Depends(get_email_provider)
):
    """Get all emails in a conversation thread.
    
    Args:
        conversation_id: Unique conversation identifier
        current_user: Authenticated user
        provider: Email provider instance
    
    Returns:
        All emails in the conversation thread
    """
    emails = provider.get_conversation_thread(conversation_id)
    
    return ConversationResponse(
        conversation_id=conversation_id,
        emails=emails,
        total=len(emails)
    )


@router.put("/emails/{email_id}/classification", response_model=EmailOperationResponse)
async def update_email_classification(
    email_id: str,
    request: UpdateClassificationRequest,
    provider: EmailProvider = Depends(get_email_provider)
):
    """Update email classification and optionally apply to Outlook.
    
    Args:
        email_id: Unique email identifier
        request: Classification update request with category and apply_to_outlook flag
        provider: Email provider instance
    
    Returns:
        Operation result with success status and message
    """
    try:
        from backend.database.connection import db_manager
        from backend.services.com_email_provider import INBOX_CATEGORIES, NON_INBOX_CATEGORIES
        
        category = request.category.lower()
        folder_name = None
        
        # Find the appropriate folder for this category
        all_categories = {**INBOX_CATEGORIES, **NON_INBOX_CATEGORIES}
        if category in all_categories:
            folder_name = all_categories[category]
        else:
            folder_name = 'Work Relevant'  # Default fallback
        
        # CRITICAL: Store user correction in database for accuracy tracking
        # This allows us to compare ai_category (original AI) vs category (user-corrected)
        with db_manager.get_connection() as conn:
            # Update the user-corrected category in the database
            conn.execute("""
                UPDATE emails 
                SET category = ? 
                WHERE id = ?
            """, (category, email_id))
            conn.commit()
        
        if request.apply_to_outlook and folder_name:
            # Move email to the category folder
            success = provider.move_email(email_id, folder_name)
            
            if success:
                return EmailOperationResponse(
                    success=True,
                    message=f"Email classified as '{request.category}' and moved to '{folder_name}'",
                    email_id=email_id
                )
            else:
                return EmailOperationResponse(
                    success=False,
                    message=f"Failed to move email to '{folder_name}'",
                    email_id=email_id
                )
        else:
            # Just update classification without moving
            return EmailOperationResponse(
                success=True,
                message=f"Email classified as '{request.category}' (stored in database)",
                email_id=email_id
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update classification: {str(e)}"
        )


@router.post("/emails/bulk-apply-to-outlook", response_model=BulkApplyResponse)
async def bulk_apply_to_outlook(
    request: BulkApplyRequest = Body(...),
    provider: EmailProvider = Depends(get_email_provider),
    ai_service = Depends(get_ai_service)
):
    """Bulk apply AI classifications to Outlook folders.
    
    This endpoint:
    1. Classifies all selected emails using AI (if not already classified)
    2. Moves emails to appropriate Outlook folders based on their category
    3. Returns detailed results about the operation
    
    Note: Task extraction happens separately via /api/emails/extract-tasks endpoint
    
    Args:
        request: Bulk apply request with email IDs and options
        provider: Email provider instance
        ai_service: AI service instance
    
    Returns:
        Results of the bulk apply operation
    """
    try:
        if not request.email_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No email IDs provided"
            )
        
        successful = 0
        failed = 0
        errors = []
        
        # Category mappings from Python version
        from backend.services.com_email_provider import INBOX_CATEGORIES, NON_INBOX_CATEGORIES
        
        for email_id in request.email_ids:
            try:
                # Get email data
                email = provider.get_email_by_id(email_id)
                if not email:
                    # Skip emails that can't be found (might have been moved/deleted)
                    logger.warning(f"[Bulk Apply] Email {email_id[:20]}... not found, skipping")
                    continue
                
                # Get or determine AI category
                ai_category = email.get('ai_category')
                
                if not ai_category:
                    # Classify the email first
                    email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('body', '')}"
                    
                    try:
                        classification_result = await ai_service.classify_email(
                            email_content=email_text,
                            context=None
                        )
                        ai_category = classification_result.get('category', 'work_relevant')
                    except Exception as classify_error:
                        errors.append(f"Failed to classify email {email_id}: {str(classify_error)}")
                        ai_category = 'work_relevant'  # Fallback category
                
                # Apply to Outlook if requested
                if request.apply_to_outlook:
                    # Determine folder name based on category
                    all_categories = {**INBOX_CATEGORIES, **NON_INBOX_CATEGORIES}
                    folder_name = all_categories.get(ai_category.lower())
                    
                    logger.info(f"[Bulk Apply] Email {email_id[:20]}... -> Category: '{ai_category}' -> Folder: '{folder_name}'")
                    
                    if folder_name:
                        # Move email to appropriate folder
                        move_success = provider.move_email(email_id, folder_name)
                        
                        if move_success:
                            successful += 1
                            logger.info(f"[Bulk Apply] [OK] Successfully moved to {folder_name}")
                        else:
                            error_msg = f"Failed to move email {email_id} to {folder_name}"
                            errors.append(error_msg)
                            logger.error(f"[Bulk Apply] [FAIL] {error_msg}")
                            failed += 1
                    else:
                        # Category doesn't require folder move (stays in inbox)
                        logger.info(f"[Bulk Apply] Category '{ai_category}' has no folder mapping, skipping move")
                        successful += 1
                else:
                    # Just classification without moving
                    successful += 1
                    
            except Exception as e:
                errors.append(f"Error processing email {email_id}: {str(e)}")
                failed += 1
        
        return BulkApplyResponse(
            success=failed == 0,
            processed=len(request.email_ids),
            successful=successful,
            failed=failed,
            errors=errors
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk apply classifications: {str(e)}"
        )


@router.post("/emails/batch-process", response_model=EmailBatchResult)
async def batch_process_emails(
    batch_request: EmailBatch,
    provider: EmailProvider = Depends(get_email_provider),
    ai_service = Depends(get_ai_service)
):
    """Batch process multiple emails for classification and analysis.
    
    Uses AI service to classify each email and extract action items in batch.
    Optimized for processing multiple emails efficiently.
    
    Args:
        batch_request: Batch of emails to process
        provider: Email provider instance
        ai_service: AI service for classification
    
    Returns:
        Batch processing results with AI classifications
    """
    try:
        # Get email content for each email ID in the batch
        processed_emails = []
        errors = []
        
        for email_data in batch_request.emails:
            try:
                if isinstance(email_data, dict) and "id" in email_data:
                    email_id = email_data["id"]
                    email_content = await provider.get_email_content(email_id)
                    if email_content:
                        processed_emails.append(email_content)
                elif isinstance(email_data, dict):
                    # Already has email content
                    processed_emails.append(email_data)
                else:
                    errors.append(f"Invalid email data format: {email_data}")
            except Exception as e:
                errors.append(f"Failed to process email: {str(e)}")
        
        # 🤖 AI INTEGRATION: Classify and extract action items from each email
        results = []
        for email in processed_emails:
            try:
                # Format email content for AI processing
                email_text = f"Subject: {email.get('subject', 'No subject')}\n"
                email_text += f"From: {email.get('sender', 'Unknown')}\n\n"
                email_text += email.get('body', email.get('content', ''))
                
                # Classify email
                classification = await ai_service.classify_email(email_text)
                
                # Extract action items if actionable
                action_items = []
                if classification.get('category') in ['required_personal_action', 'actionable']:
                    action_result = await ai_service.extract_action_items(email_text)
                    if action_result.get('action_items'):
                        action_items = action_result['action_items']
                
                # Determine priority based on classification
                priority = "high" if classification.get('category') == 'required_personal_action' else "normal"
                if classification.get('category') in ['spam_to_delete', 'fyi']:
                    priority = "low"
                
                results.append({
                    "email_id": email.get('id'),
                    "category": classification.get('category', 'unclassified'),
                    "confidence": classification.get('confidence', 0.5),
                    "reasoning": classification.get('reasoning', ''),
                    "action_items": action_items,
                    "priority": priority
                })
                
            except Exception as e:
                logger.error(f"AI processing failed for email: {e}")
                # Return fallback result for this email
                results.append({
                    "email_id": email.get('id'),
                    "category": "unclassified",
                    "confidence": 0.0,
                    "reasoning": f"AI processing error: {str(e)}",
                    "action_items": [],
                    "priority": "normal",
                    "error": str(e)
                })
        
        return EmailBatchResult(
            processed_count=len(batch_request.emails),
            successful_count=len(processed_emails),
            failed_count=len(errors),
            results=results,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch process emails: {str(e)}"
        )

