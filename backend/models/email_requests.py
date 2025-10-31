"""Request and response models for email API endpoints."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


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


class SyncEmailRequest(BaseModel):
    """Request model for syncing emails to database."""
    emails: List[Dict[str, Any]]
