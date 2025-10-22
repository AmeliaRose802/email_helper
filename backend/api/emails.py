"""Email endpoints for FastAPI Email Helper API."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
import logging
from datetime import datetime
import time

from backend.services.email_provider import EmailProvider
from backend.core.dependencies import get_email_provider, get_ai_service
from backend.api.auth import get_current_user
from backend.models.user import UserInDB
from backend.models.email import Email, EmailBatch, EmailBatchResult

router = APIRouter()
logger = logging.getLogger(__name__)


class EmailListResponse(BaseModel):
    """Response model for email list endpoint."""
    emails: List[Dict[str, Any]]
    total: int
    offset: int
    limit: int
    has_more: bool


class EmailFolderResponse(BaseModel):
    """Response model for email folders endpoint."""
    folders: List[Dict[str, str]]
    total: int


class EmailOperationResponse(BaseModel):
    """Response model for email operations."""
    success: bool
    message: str
    email_id: Optional[str] = None


class UpdateClassificationRequest(BaseModel):
    """Request model for updating email classification."""
    category: str
    apply_to_outlook: bool = True


class CategoryFolderMapping(BaseModel):
    """Category to folder mapping."""
    category: str
    folder_name: str
    stays_in_inbox: bool


class BulkApplyRequest(BaseModel):
    """Request model for bulk applying classifications to Outlook."""
    email_ids: List[str]
    apply_to_outlook: bool = True


class BulkApplyResponse(BaseModel):
    """Response model for bulk apply operation."""
    success: bool
    processed: int
    successful: int
    failed: int
    errors: List[str] = []


class ConversationResponse(BaseModel):
    """Response model for conversation thread."""
    conversation_id: str
    emails: List[Dict[str, Any]]
    total: int


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
    import logging
    logger = logging.getLogger(__name__)
    
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
            except:
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
    When they match, the AI was correct. When they differ, the AI was wrong.
    
    Returns:
        Dictionary with overall and per-category accuracy statistics including:
        - total emails analyzed
        - overall accuracy percentage
        - per-category stats (total, correct, accuracy, precision, recall, f1)
    """
    import logging
    from backend.database.connection import db_manager
    from collections import defaultdict
    
    logger = logging.getLogger(__name__)
    
    try:
        with db_manager.get_connection() as conn:
            # Get all emails with both AI and user categories
            cursor = conn.execute("""
                SELECT ai_category, category
                FROM emails
                WHERE ai_category IS NOT NULL 
                  AND ai_category != ''
                  AND category IS NOT NULL
                  AND category != ''
            """)
            
            rows = cursor.fetchall()
            
        if not rows:
            return {
                "overall_accuracy": 0,
                "total_emails": 0,
                "categories": []
            }
        
        # Calculate per-category statistics
        category_stats = defaultdict(lambda: {
            'total': 0,
            'correct': 0,
            'true_positives': 0,
            'false_positives': 0,
            'false_negatives': 0
        })
        
        total_emails = len(rows)
        total_correct = 0
        
        # First pass: count totals and correct classifications
        for ai_cat, user_cat in rows:
            ai_cat = ai_cat.lower()
            user_cat = user_cat.lower()
            
            category_stats[ai_cat]['total'] += 1
            
            if ai_cat == user_cat:
                category_stats[ai_cat]['correct'] += 1
                category_stats[ai_cat]['true_positives'] += 1
                total_correct += 1
        
        # Second pass: calculate false positives and false negatives
        for ai_cat, user_cat in rows:
            ai_cat = ai_cat.lower()
            user_cat = user_cat.lower()
            
            if ai_cat != user_cat:
                # AI predicted ai_cat but user corrected to user_cat
                category_stats[ai_cat]['false_positives'] += 1
                category_stats[user_cat]['false_negatives'] += 1
        
        # Calculate metrics for each category
        categories = []
        for cat, stats in category_stats.items():
            total = stats['total']
            correct = stats['correct']
            tp = stats['true_positives']
            fp = stats['false_positives']
            fn = stats['false_negatives']
            
            accuracy = (correct / total * 100) if total > 0 else 0
            precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0
            recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
            
            # Format category name nicely
            cat_display = cat.replace('_', ' ').title()
            
            categories.append({
                'category': cat_display,
                'total': total,
                'correct': correct,
                'accuracy': round(accuracy, 1),
                'precision': round(precision, 1),
                'recall': round(recall, 1),
                'f1': round(f1, 1),
                'truePositives': tp,
                'falsePositives': fp,
                'falseNegatives': fn
            })
        
        # Sort by total (most common categories first)
        categories.sort(key=lambda x: x['total'], reverse=True)
        
        overall_accuracy = (total_correct / total_emails * 100) if total_emails > 0 else 0
        
        return {
            "overall_accuracy": round(overall_accuracy, 1),
            "total_emails": total_emails,
            "total_correct": total_correct,
            "categories": categories
        }
        
    except Exception as e:
        logger.error(f"[Accuracy Stats] Failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate accuracy stats: {str(e)}"
        )


@router.get("/emails/{email_id}", response_model=Dict[str, Any])
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
    
    try:
        email = await provider.get_email_content(email_id)
        
        elapsed = time.time() - start_time
        if elapsed > 1.0:  # Log if slower than 1 second
            print(f"⚠️ Slow email fetch: {email_id} took {elapsed:.2f}s")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Email with ID '{email_id}' not found"
            )
        
        return email
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve email: {str(e)}"
        )


@router.put("/emails/{email_id}/read", response_model=EmailOperationResponse)
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
    try:
        if read:
            success = provider.mark_as_read(email_id)
            message = "Email marked as read successfully" if success else "Failed to mark email as read"
        else:
            success = provider.mark_as_unread(email_id) if hasattr(provider, 'mark_as_unread') else False
            message = "Email marked as unread successfully" if success else "Failed to mark email as unread"
        
        if success:
            return EmailOperationResponse(
                success=True,
                message=message,
                email_id=email_id
            )
        else:
            return EmailOperationResponse(
                success=False,
                message=message,
                email_id=email_id
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update email read status: {str(e)}"
        )


@router.post("/emails/{email_id}/mark-read", response_model=EmailOperationResponse)
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
    try:
        success = provider.mark_as_read(email_id)
        
        if success:
            return EmailOperationResponse(
                success=True,
                message="Email marked as read successfully",
                email_id=email_id
            )
        else:
            return EmailOperationResponse(
                success=False,
                message="Failed to mark email as read",
                email_id=email_id
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark email as read: {str(e)}"
        )


@router.post("/emails/{email_id}/move", response_model=EmailOperationResponse)
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
    try:
        success = provider.move_email(email_id, destination_folder)
        
        if success:
            return EmailOperationResponse(
                success=True,
                message=f"Email moved to '{destination_folder}' successfully",
                email_id=email_id
            )
        else:
            return EmailOperationResponse(
                success=False,
                message=f"Failed to move email to '{destination_folder}'",
                email_id=email_id
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move email: {str(e)}"
        )


@router.get("/folders", response_model=EmailFolderResponse)
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
    try:
        folders = provider.get_folders()
        
        return EmailFolderResponse(
            folders=folders,
            total=len(folders)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve folders: {str(e)}"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
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
    try:
        emails = provider.get_conversation_thread(conversation_id)
        
        return ConversationResponse(
            conversation_id=conversation_id,
            emails=emails,
            total=len(emails)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}"
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
    import logging
    logger = logging.getLogger(__name__)
    
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


@router.post("/emails/extract-tasks")
async def extract_tasks_from_emails(
    request: BulkApplyRequest = Body(...),
    background_tasks: BackgroundTasks = None,
    provider: EmailProvider = Depends(get_email_provider),
    ai_service = Depends(get_ai_service)
):
    """Extract tasks and summaries from emails asynchronously in background.
    
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
    """
    import logging
    import asyncio
    from backend.services.task_service import get_task_service
    from backend.models.task import TaskCreate, TaskPriority, TaskStatus
    
    logger = logging.getLogger(__name__)
    
    if not request.email_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email IDs provided"
        )
    
    # Categories that should generate tasks
    ACTIONABLE_CATEGORIES = ['required_personal_action', 'team_action', 'optional_action']
    JOB_CATEGORIES = ['job_listing']
    EVENT_CATEGORIES = ['optional_event']
    SUMMARY_CATEGORIES = ['fyi', 'newsletter']
    
    async def process_emails_background():
        """Background task to process emails and create tasks."""
        from backend.database.connection import db_manager
        
        task_service_instance = get_task_service()
        tasks_created = 0
        summaries_created = 0
        
        logger.info(f"[Task Extraction] Starting background processing for {len(request.email_ids)} emails")
        
        # ===== HOLISTIC ANALYSIS: Detect expired events and superseded actions =====
        holistic_reclassifications = {}  # Map email_id -> new category
        
        try:
            # Fetch all emails for holistic analysis
            emails_for_analysis = []
            with db_manager.get_connection() as conn:
                placeholders = ','.join('?' * len(request.email_ids))
                cursor = conn.execute(
                    f"SELECT id, subject, sender, body, date, ai_category FROM emails WHERE id IN ({placeholders})",
                    request.email_ids
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
                logger.info(f"[Holistic Analysis] Analyzing {len(emails_for_analysis)} emails for expired items and superseded actions")
                holistic_result = await ai_service.analyze_holistically(emails_for_analysis)
                
                # Process expired items - reclassify to spam_to_delete
                for expired in holistic_result.get('expired_items', []):
                    email_id = expired.get('email_id')
                    reason = expired.get('reason', 'Past deadline or event occurred')
                    if email_id:
                        holistic_reclassifications[email_id] = 'spam_to_delete'
                        logger.info(f"[Holistic] 🗑️ Marking expired: {email_id[:30]}... - {reason}")
                
                # Process superseded actions - reclassify to work_relevant or fyi
                for superseded in holistic_result.get('superseded_actions', []):
                    original_id = superseded.get('original_email_id')
                    superseded_by = superseded.get('superseded_by_email_id')
                    reason = superseded.get('reason', 'Superseded by newer email')
                    if original_id:
                        holistic_reclassifications[original_id] = 'work_relevant'
                        logger.info(f"[Holistic] ♻️ Marking superseded: {original_id[:30]}... by {superseded_by[:30]}... - {reason}")
                
                # Process duplicates - keep canonical, archive others
                for dup_group in holistic_result.get('duplicate_groups', []):
                    keep_id = dup_group.get('keep_email_id')
                    archive_ids = dup_group.get('archive_email_ids', [])
                    topic = dup_group.get('topic', 'Duplicate')
                    for archive_id in archive_ids:
                        if archive_id and archive_id != keep_id:
                            holistic_reclassifications[archive_id] = 'spam_to_delete'
                            logger.info(f"[Holistic] 📋 Archiving duplicate: {archive_id[:30]}... (keeping {keep_id[:30]}...) - {topic}")
                
                logger.info(f"[Holistic Analysis] Complete: {len(holistic_reclassifications)} emails reclassified")
        except Exception as e:
            logger.warning(f"[Holistic Analysis] Failed (continuing with individual processing): {e}")
        # ===== END HOLISTIC ANALYSIS =====
        
        for email_id in request.email_ids:
            try:
                # Get email data from DATABASE (not Outlook - it's already synced)
                with db_manager.get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT id, subject, sender, body, ai_category FROM emails WHERE id = ?",
                        (email_id,)
                    )
                    row = cursor.fetchone()
                    
                if not row:
                    logger.warning(f"[Task Extraction] Email {email_id} not found in database")
                    continue
                
                # Convert to dict
                email = {
                    'id': row[0],
                    'subject': row[1],
                    'sender': row[2],
                    'body': row[3],
                    'ai_category': row[4]
                }
                
                # Apply holistic reclassification if available (overrides original AI category)
                if email_id in holistic_reclassifications:
                    ai_category = holistic_reclassifications[email_id].lower()
                    logger.info(f"[Holistic Override] Email {email_id[:30]}... reclassified to: {ai_category}")
                    
                    # Update database with new classification
                    with db_manager.get_connection() as conn:
                        conn.execute(
                            "UPDATE emails SET ai_category = ? WHERE id = ?",
                            (ai_category, email_id)
                        )
                        conn.commit()
                else:
                    # Get AI category
                    ai_category = email.get('ai_category', '').lower()
                
                if not ai_category:
                    # Classify if needed (with rate limiting delay)
                    try:
                        # ⏱️ RATE LIMITING: Wait 1 second before classification to avoid Azure OpenAI throttling
                        await asyncio.sleep(1.0)
                        
                        email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('body', '')}"
                        classification_result = await ai_service.classify_email(
                            email_content=email_text
                        )
                        ai_category = classification_result.get('category', '').lower()
                    except Exception as e:
                        logger.error(f"[Task Extraction] Failed to classify email {email_id}: {e}")
                        continue
                
                # Process based on category
                if ai_category in ACTIONABLE_CATEGORIES:
                    # Extract action items and create tasks
                    try:
                        # ⏱️ RATE LIMITING: Wait 1.5 seconds before action extraction
                        await asyncio.sleep(1.5)
                        
                        email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('body', '')}"
                        action_result = await ai_service.extract_action_items(email_text)
                        
                        # Filter out fallback/error responses that shouldn't create tasks
                        # IMPORTANT: Match EXACT error phrases generated by AI service
                        action_text = action_result.get('action_required', '') if action_result else ''
                        is_fallback = any(phrase in action_text.lower() for phrase in [
                            'unable to extract action items',  # From async wrapper error
                            'review email content',  # From JSON parse failure fallback
                            'unable to parse structured response',  # From explanation field
                            'ai processing unavailable',  # Generic AI error
                            'content filter blocked'  # Azure content policy
                        ])
                        
                        # Also check for error flag in result
                        if action_result and 'error' in action_result:
                            is_fallback = True
                        
                        if action_result and action_text and not is_fallback:
                            logger.info(f"[Task Extraction] ✅ Successfully extracted action: '{action_text[:80]}...' from {email_id[:30]}")
                            
                            # Determine priority
                            priority = 'high' if 'urgent' in email.get('subject', '').lower() else 'medium'
                            priority = 'high' if 'urgent' in email.get('subject', '').lower() else 'medium'
                            if ai_category == 'required_personal_action':
                                priority = 'high'
                            
                            # Parse due date
                            due_date_str = action_result.get('due_date')
                            due_date = None
                            if due_date_str and due_date_str not in [None, 'No specific deadline', '', 'Unknown']:
                                try:
                                    from dateutil import parser
                                    due_date = parser.parse(due_date_str)
                                except:
                                    due_date = None
                            
                            # Build description with all relevant info
                            description_parts = [f"Action: {action_result.get('action_required', '')}"]
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
                            
                            # Create task in database
                            created_task = await task_service_instance.create_task(task_data, user_id=1)
                            tasks_created += 1
                            logger.info(f"[Task Extraction] Created task #{created_task.id} for email {email_id[:20]}...")
                        else:
                            if is_fallback:
                                logger.info(f"[Task Extraction] ⏭️ Skipped: Fallback response detected for {email_id[:30]} - '{action_text[:60]}'")
                            elif not action_text:
                                logger.info(f"[Task Extraction] ⏭️ Skipped: No action required for {email_id[:30]}")
                            
                    except Exception as task_error:
                        error_type = type(task_error).__name__
                        error_msg = str(task_error).lower()
                        
                        # Detailed error diagnosis
                        if 'content_filter' in error_msg or 'responsibleaipolicyviolation' in error_msg:
                            logger.warning(f"[Task Extraction] ⚠️ CONTENT FILTER blocked action extraction for email {email_id[:30]}: {task_error}")
                        elif 'rate' in error_msg or 'quota' in error_msg or '429' in error_msg:
                            logger.warning(f"[Task Extraction] ⏱️ RATE LIMIT hit during action extraction for email {email_id[:30]}: {task_error}")
                        elif 'timeout' in error_msg or 'connection' in error_msg:
                            logger.warning(f"[Task Extraction] 🔌 CONNECTION ERROR during action extraction for email {email_id[:30]}: {task_error}")
                        else:
                            logger.error(f"[Task Extraction] ❌ UNKNOWN ERROR ({error_type}) creating task for email {email_id[:30]}: {task_error}")
                
                elif ai_category in JOB_CATEGORIES:
                    # Create job listing task
                    try:
                        # ⏱️ RATE LIMITING: Wait 1.5 seconds before job listing extraction
                        await asyncio.sleep(1.5)
                        
                        email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('body', '')}"
                        action_result = await ai_service.extract_action_items(email_text)
                        
                        # Filter out fallback responses for job listings too
                        action_text = action_result.get('action_required', '') if action_result else ''
                        is_fallback = any(phrase in action_text.lower() for phrase in [
                            'unable to extract action items',
                            'review email content',
                            'unable to parse structured response',
                            'ai processing unavailable',
                            'content filter blocked'
                        ]) or ('error' in action_result)
                        
                        if is_fallback:
                            logger.info(f"[Task Extraction] Skipping job listing due to fallback response: {email_id[:30]}")
                            continue
                        
                        description_parts = [f"Job Listing: {email.get('subject', '')}"]
                        if action_result.get('explanation'):
                            description_parts.append(f"\nQualification Match: {action_result['explanation']}")
                        if action_result.get('relevance'):
                            description_parts.append(f"\nRelevance: {action_result['relevance']}")
                        if action_result.get('links'):
                            description_parts.append(f"\nApply: {', '.join(action_result['links'])}")
                        description_parts.append(f"\nFrom: {email.get('sender', '')}")
                        
                        # Parse due date
                        due_date = None
                        if action_result.get('due_date') and action_result['due_date'] not in ['No specific deadline', '', 'Unknown']:
                            try:
                                from dateutil import parser
                                due_date = parser.parse(action_result['due_date'])
                            except:
                                due_date = None
                        
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
                        
                        created_task = await task_service_instance.create_task(task_data, user_id=1)
                        tasks_created += 1
                        logger.info(f"[Task Extraction] Created job listing task for email {email_id[:20]}...")
                        
                    except Exception as job_error:
                        error_type = type(job_error).__name__
                        error_msg = str(job_error).lower()
                        
                        if 'content_filter' in error_msg or 'responsibleaipolicyviolation' in error_msg:
                            logger.warning(f"[Task Extraction] ⚠️ CONTENT FILTER blocked job listing extraction for email {email_id[:30]}: {job_error}")
                        elif 'rate' in error_msg or 'quota' in error_msg or '429' in error_msg:
                            logger.warning(f"[Task Extraction] ⏱️ RATE LIMIT hit during job listing extraction for email {email_id[:30]}: {job_error}")
                        else:
                            logger.error(f"[Task Extraction] ❌ ERROR ({error_type}) creating job listing for email {email_id[:30]}: {job_error}")
                
                elif ai_category in EVENT_CATEGORIES:
                    # Create optional event task
                    try:
                        # ⏱️ RATE LIMITING: Wait 1.5 seconds before event extraction
                        await asyncio.sleep(1.5)
                        
                        email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('body', '')}"
                        action_result = await ai_service.extract_action_items(email_text)
                        
                        # Filter out fallback responses for events too
                        action_text = action_result.get('action_required', '') if action_result else ''
                        is_fallback = any(phrase in action_text.lower() for phrase in [
                            'unable to extract action items',
                            'review email content',
                            'unable to parse structured response',
                            'ai processing unavailable',
                            'content filter blocked'
                        ]) or ('error' in action_result)
                        
                        if is_fallback:
                            logger.info(f"[Task Extraction] Skipping event due to fallback response: {email_id[:30]}")
                            continue
                        
                        description_parts = [f"Optional Event: {email.get('subject', '')}"]
                        if action_result.get('relevance'):
                            description_parts.append(f"\nRelevance: {action_result['relevance']}")
                        if action_result.get('explanation'):
                            description_parts.append(f"\nDetails: {action_result['explanation']}")
                        if action_result.get('links'):
                            description_parts.append(f"\nRegister: {', '.join(action_result['links'])}")
                        description_parts.append(f"\nFrom: {email.get('sender', '')}")
                        
                        # Try to parse event date
                        event_date = None
                        if action_result.get('due_date') and action_result['due_date'] not in ['No specific deadline', '', 'Unknown']:
                            try:
                                from dateutil import parser
                                event_date = parser.parse(action_result['due_date'])
                            except:
                                event_date = None
                        
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
                        
                        created_task = await task_service_instance.create_task(task_data, user_id=1)
                        summaries_created += 1
                        logger.info(f"[Task Extraction] Created event task for email {email_id[:20]}...")
                        
                    except Exception as event_error:
                        error_type = type(event_error).__name__
                        error_msg = str(event_error).lower()
                        
                        if 'content_filter' in error_msg or 'responsibleaipolicyviolation' in error_msg:
                            logger.warning(f"[Task Extraction] ⚠️ CONTENT FILTER blocked event extraction for email {email_id[:30]}: {event_error}")
                        elif 'rate' in error_msg or 'quota' in error_msg or '429' in error_msg:
                            logger.warning(f"[Task Extraction] ⏱️ RATE LIMIT hit during event extraction for email {email_id[:30]}: {event_error}")
                        else:
                            logger.error(f"[Task Extraction] ❌ ERROR ({error_type}) creating event task for email {email_id[:30]}: {event_error}")
                
                elif ai_category in SUMMARY_CATEGORIES:
                    # Create informational tasks for FYI and newsletters
                    try:
                        # ⏱️ RATE LIMITING: Wait 1.5 seconds before summary generation
                        await asyncio.sleep(1.5)
                        
                        email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('body', '')}"
                        
                        # Get AI summary/analysis using category-specific prompts
                        if ai_category == 'newsletter':
                            # Use newsletter_summary.prompty for detailed newsletter analysis
                            summary_result = await ai_service.generate_summary(email_text, summary_type='detailed')
                            summary_text = summary_result.get('summary', 'Newsletter content')
                            
                            description_parts = [f"📰 Newsletter Summary"]
                            description_parts.append(f"\n{summary_text}")
                            if summary_result.get('key_points'):
                                description_parts.append(f"\n\nKey Points:")
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
                            # Use fyi_summary.prompty for concise FYI bullet point
                            summary_result = await ai_service.generate_summary(email_text, summary_type='fyi')
                            summary_text = summary_result.get('summary', 'FYI information')
                            
                            description_parts = [f"📋 FYI: {summary_text}"]
                            description_parts.append(f"\nFrom: {email.get('sender', '')}")
                            
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
                        
                        created_task = await task_service_instance.create_task(task_data, user_id=1)
                        summaries_created += 1
                        logger.info(f"[Task Extraction] Created {ai_category} summary for email {email_id[:20]}...")
                        
                    except Exception as summary_error:
                        error_type = type(summary_error).__name__
                        error_msg = str(summary_error).lower()
                        
                        if 'content_filter' in error_msg or 'responsibleaipolicyviolation' in error_msg:
                            logger.warning(f"[Task Extraction] ⚠️ CONTENT FILTER blocked {ai_category} summary for email {email_id[:30]}: {summary_error}")
                        elif 'rate' in error_msg or 'quota' in error_msg or '429' in error_msg:
                            logger.warning(f"[Task Extraction] ⏱️ RATE LIMIT hit during {ai_category} summary for email {email_id[:30]}: {summary_error}")
                        else:
                            logger.error(f"[Task Extraction] ❌ ERROR ({error_type}) creating {ai_category} summary for email {email_id[:30]}: {summary_error}")
                
                # ⏱️ RATE LIMITING: 2-second delay between emails to prevent Azure OpenAI throttling
                # This ensures we stay well under rate limits and reduces "AI service unavailable" errors
                await asyncio.sleep(2.0)
                
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e).lower()
                
                # 🔍 TOP-LEVEL ERROR DIAGNOSIS - Shows exact failure reason
                if 'content_filter' in error_msg or 'responsibleaipolicyviolation' in error_msg or 'content management policy' in error_msg:
                    logger.warning(f"[Task Extraction] ⚠️ CONTENT FILTER: Email {email_id[:30]} blocked by Azure content policy. Email contains flagged content.")
                elif 'rate' in error_msg or 'quota' in error_msg or '429' in error_msg or 'throttl' in error_msg:
                    logger.warning(f"[Task Extraction] ⏱️ RATE LIMIT: Throttled while processing email {email_id[:30]}. Azure OpenAI rate limit exceeded. Error: {e}")
                elif 'timeout' in error_msg or 'connection' in error_msg or 'network' in error_msg:
                    logger.warning(f"[Task Extraction] 🔌 CONNECTION: Network issue processing email {email_id[:30]}. Error: {e}")
                elif 'badrequest' in error_msg or 'invalid' in error_msg:
                    logger.warning(f"[Task Extraction] ⚠️ BAD REQUEST: Invalid data in email {email_id[:30]}. Error: {e}")
                else:
                    logger.error(f"[Task Extraction] ❌ UNEXPECTED ERROR ({error_type}) processing email {email_id[:30]}: {e}")
                continue
        
        logger.info(f"[Task Extraction] Completed: {tasks_created} tasks, {summaries_created} summaries created")
    
    # Run synchronously for now to catch errors (can move to background later once working)
    try:
        await process_emails_background()
        logger.info(f"[Task Extraction] Processing completed successfully")
    except Exception as e:
        logger.error(f"[Task Extraction] CRITICAL ERROR in background task: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Task extraction failed: {str(e)}"
        )
    
    return {
        "status": "completed",
        "message": f"Task extraction completed for {len(request.email_ids)} emails.",
        "email_count": len(request.email_ids),
        "timestamp": datetime.now().isoformat()
    }


class SyncEmailRequest(BaseModel):
    """Request model for syncing emails to database."""
    emails: List[Dict[str, Any]]


@router.post("/emails/sync-to-database")
async def sync_emails_to_database(
    request: SyncEmailRequest,
    provider: EmailProvider = Depends(get_email_provider)
):
    """Sync classified emails from frontend to database.
    
    This stores classified emails in the database so they can be used for
    task extraction, analytics, and persistence.
    
    Args:
        request: List of classified emails with AI categories
        provider: Email provider instance
    
    Returns:
        Status of sync operation
    """
    import logging
    from backend.database.connection import db_manager
    
    logger = logging.getLogger(__name__)
    
    if not request.emails:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No emails provided"
        )
    
    try:
        synced_count = 0
        errors = []
        
        # Ensure emails table has all necessary columns
        with db_manager.get_connection() as conn:
            # Add ai_category column if it doesn't exist
            try:
                conn.execute("ALTER TABLE emails ADD COLUMN ai_category TEXT")
                conn.execute("ALTER TABLE emails ADD COLUMN ai_confidence REAL")
                conn.execute("ALTER TABLE emails ADD COLUMN ai_reasoning TEXT")
                conn.execute("ALTER TABLE emails ADD COLUMN one_line_summary TEXT")
                conn.execute("ALTER TABLE emails ADD COLUMN body TEXT")
                conn.execute("ALTER TABLE emails ADD COLUMN date TIMESTAMP")
                conn.execute("ALTER TABLE emails ADD COLUMN conversation_id TEXT")
                conn.commit()
                logger.info("[DB] Added AI classification columns to emails table")
            except Exception:
                # Columns might already exist
                pass
            
            # Insert or update emails
            for email_data in request.emails:
                try:
                    email_id = email_data.get('id')
                    if not email_id:
                        continue
                    
                    # Check if email already exists
                    cursor = conn.execute(
                        "SELECT id FROM emails WHERE id = ?",
                        (email_id,)
                    )
                    exists = cursor.fetchone() is not None
                    
                    if exists:
                        # Update existing email with AI classification
                        conn.execute(
                            """
                            UPDATE emails 
                            SET ai_category = ?, 
                                ai_confidence = ?, 
                                ai_reasoning = ?,
                                one_line_summary = ?,
                                processed_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                            """,
                            (
                                email_data.get('ai_category'),
                                email_data.get('ai_confidence'),
                                email_data.get('ai_reasoning'),
                                email_data.get('one_line_summary'),
                                email_id
                            )
                        )
                    else:
                        # Insert new email
                        conn.execute(
                            """
                            INSERT INTO emails (
                                id, subject, sender, recipient, content, body, 
                                received_date, date, category, ai_category, 
                                confidence, ai_confidence, ai_reasoning, 
                                one_line_summary, conversation_id, user_id, processed_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            """,
                            (
                                email_id,
                                email_data.get('subject', ''),
                                email_data.get('sender', ''),
                                email_data.get('recipient', ''),
                                email_data.get('body', ''),
                                email_data.get('body', ''),
                                email_data.get('date'),
                                email_data.get('date'),
                                email_data.get('ai_category'),  # Legacy category field
                                email_data.get('ai_category'),
                                email_data.get('ai_confidence', 0.0),
                                email_data.get('ai_confidence', 0.0),
                                email_data.get('ai_reasoning', ''),
                                email_data.get('one_line_summary', ''),
                                email_data.get('conversation_id'),
                                1  # Default user_id
                            )
                        )
                    
                    synced_count += 1
                    
                except Exception as e:
                    error_msg = f"Failed to sync email {email_data.get('id', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            conn.commit()
        
        return {
            "success": True,
            "message": f"Synced {synced_count} emails to database",
            "synced_count": synced_count,
            "failed_count": len(errors),
            "errors": errors if errors else None
        }
        
    except Exception as e:
        logger.error(f"[Sync] Failed to sync emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync emails: {str(e)}"
        )


@router.post("/emails/analyze-holistically")
async def analyze_holistically(
    request: SyncEmailRequest,
    ai_service = Depends(get_ai_service)
):
    """Perform holistic analysis across multiple emails.
    
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
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not request.emails:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No emails provided"
        )
    
    try:
        logger.info(f"[Holistic Analysis] Starting analysis for {len(request.emails)} emails")
        
        # Perform holistic analysis
        analysis_result = await ai_service.analyze_holistically(request.emails)
        
        logger.info(f"[Holistic Analysis] Completed successfully")
        logger.debug(f"[Holistic Analysis] Results: {analysis_result}")
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"[Holistic Analysis] Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform holistic analysis: {str(e)}"
        )

