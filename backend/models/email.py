"""Email models for FastAPI Email Helper API."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class EmailBase(BaseModel):
    """Base email model with standardized field names.
    
    Field Naming Standards:
    - content (not body): Email content/body text
    - received_time (not date/received_date): When email was received
    - ai_category (not category): AI-assigned category
    
    For backward compatibility, use model_computed_fields or serialize methods
    to include deprecated field names during transition period.
    """
    subject: str
    sender: str
    recipient: Optional[str] = None
    content: Optional[str] = None  # Standardized: 'content' (not 'body')
    received_time: Optional[datetime] = None  # Standardized: 'received_time' (not 'date' or 'received_date')


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
    ai_category: Optional[str] = None  # Standardized: 'ai_category' (AI classification)
    category: Optional[str] = None  # User-corrected category (for accuracy tracking)
    confidence: Optional[float] = None
    processed_at: datetime
    user_id: Optional[int] = None

    model_config = {"from_attributes": True}


class Email(EmailBase):
    """Email model for API responses with backward compatibility.
    
    Returns both new standardized fields and deprecated fields during transition.
    """
    id: str
    ai_category: Optional[str] = None  # Standardized: AI classification
    category: Optional[str] = None  # User-corrected category
    confidence: Optional[float] = None
    processed_at: datetime

    model_config = {"from_attributes": True}
    
    def model_post_init(self, __context) -> None:
        """Add backward compatibility aliases after initialization."""
        # Backward compatibility: Ensure both field names work
        if hasattr(self, 'content') and self.content is not None:
            object.__setattr__(self, 'body', self.content)
        if hasattr(self, 'received_time') and self.received_time is not None:
            object.__setattr__(self, 'date', self.received_time)
            object.__setattr__(self, 'received_date', self.received_time)


class EmailClassification(BaseModel):
    """Email classification result.
    
    Uses standardized field naming: ai_category (not category).
    """
    ai_category: str  # Standardized field name
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    action_items: List[str] = []
    priority: Optional[str] = None
    
    # Backward compatibility alias
    @property
    def category(self) -> str:
        """Deprecated: Use ai_category instead. Kept for backward compatibility."""
        return self.ai_category


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
