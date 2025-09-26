"""Email models for FastAPI Email Helper API."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class EmailBase(BaseModel):
    """Base email model."""
    subject: str
    sender: str
    recipient: Optional[str] = None
    content: Optional[str] = None
    received_date: Optional[datetime] = None


class EmailCreate(EmailBase):
    """Email creation model."""
    id: str  # Email ID from email provider


class EmailUpdate(BaseModel):
    """Email update model."""
    category: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class EmailInDB(EmailBase):
    """Email model as stored in database."""
    id: str
    category: Optional[str] = None
    confidence: Optional[float] = None
    processed_at: datetime
    user_id: Optional[int] = None

    model_config = {"from_attributes": True}


class Email(EmailBase):
    """Email model for API responses."""
    id: str
    category: Optional[str] = None
    confidence: Optional[float] = None
    processed_at: datetime

    model_config = {"from_attributes": True}


class EmailClassification(BaseModel):
    """Email classification result."""
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    action_items: List[str] = []
    priority: Optional[str] = None


class EmailBatch(BaseModel):
    """Batch email processing request."""
    emails: List[Dict[str, Any]]
    context: Optional[str] = None


class EmailBatchResult(BaseModel):
    """Batch email processing result."""  
    processed_count: int
    successful_count: int
    failed_count: int
    results: List[EmailClassification]
    errors: List[str] = []