"""Email endpoints for FastAPI Email Helper API."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.services.email_provider import EmailProvider, get_email_provider
from backend.api.auth import get_current_user
from backend.models.user import UserInDB
from backend.models.email import Email, EmailBatch, EmailBatchResult

router = APIRouter()


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


class ConversationResponse(BaseModel):
    """Response model for conversation thread."""
    conversation_id: str
    emails: List[Dict[str, Any]]
    total: int


@router.get("/emails", response_model=EmailListResponse)
async def get_emails(
    folder: str = Query("Inbox", description="Email folder name"),
    limit: int = Query(50, ge=1, le=100, description="Number of emails to retrieve"),
    offset: int = Query(0, ge=0, description="Number of emails to skip"),
    current_user: UserInDB = Depends(get_current_user),
    provider: EmailProvider = Depends(get_email_provider)
):
    """Get paginated list of emails from specified folder.
    
    Args:
        folder: Name of the email folder (default: Inbox)
        limit: Maximum number of emails to return (1-100)
        offset: Number of emails to skip for pagination
        current_user: Authenticated user
        provider: Email provider instance
    
    Returns:
        Paginated list of emails with metadata
    """
    try:
        emails = provider.get_emails(
            folder_name=folder,
            count=limit,
            offset=offset
        )
        
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


@router.get("/emails/{email_id}", response_model=Dict[str, Any])
async def get_email(
    email_id: str,
    current_user: UserInDB = Depends(get_current_user),
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
    try:
        email = provider.get_email_content(email_id)
        
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


@router.post("/emails/{email_id}/mark-read", response_model=EmailOperationResponse)
async def mark_email_as_read(
    email_id: str,
    current_user: UserInDB = Depends(get_current_user),
    provider: EmailProvider = Depends(get_email_provider)
):
    """Mark email as read.
    
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
    current_user: UserInDB = Depends(get_current_user),
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
    current_user: UserInDB = Depends(get_current_user),
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
    current_user: UserInDB = Depends(get_current_user),
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


@router.post("/emails/batch-process", response_model=EmailBatchResult)
async def batch_process_emails(
    batch_request: EmailBatch,
    current_user: UserInDB = Depends(get_current_user),
    provider: EmailProvider = Depends(get_email_provider)
):
    """Batch process multiple emails for classification and analysis.
    
    Args:
        batch_request: Batch of emails to process
        current_user: Authenticated user
        provider: Email provider instance
    
    Returns:
        Batch processing results
    """
    try:
        # Get email content for each email ID in the batch
        processed_emails = []
        errors = []
        
        for email_data in batch_request.emails:
            try:
                if isinstance(email_data, dict) and "id" in email_data:
                    email_id = email_data["id"]
                    email_content = provider.get_email_content(email_id)
                    if email_content:
                        processed_emails.append(email_content)
                elif isinstance(email_data, dict):
                    # Already has email content
                    processed_emails.append(email_data)
                else:
                    errors.append(f"Invalid email data format: {email_data}")
            except Exception as e:
                errors.append(f"Failed to process email: {str(e)}")
        
        # TODO: Integrate with AI processing for classification
        # For now, return basic results
        results = []
        for email in processed_emails:
            results.append({
                "category": "unclassified",
                "confidence": 0.5,
                "reasoning": "Basic classification - AI integration pending",
                "action_items": [],
                "priority": "normal"
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