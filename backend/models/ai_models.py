"""AI processing models for FastAPI Email Helper API."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class EmailClassificationRequest(BaseModel):
    """Request model for email classification."""
    subject: str = Field(..., description="Email subject line")
    content: str = Field(..., description="Email body content")
    sender: str = Field(..., description="Email sender address")
    context: Optional[str] = Field(None, description="Additional context for classification")


class EmailClassificationResponse(BaseModel):
    """Response model for email classification."""
    category: str = Field(..., description="Classified email category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score")
    reasoning: str = Field(..., description="Explanation for the classification")
    alternative_categories: List[str] = Field(default=[], description="Alternative category suggestions")
    processing_time: float = Field(..., description="Processing time in seconds")


class ActionItemRequest(BaseModel):
    """Request model for action item extraction."""
    email_content: str = Field(..., description="Full email content for analysis")
    context: Optional[str] = Field(None, description="Additional context for extraction")


class ActionItemResponse(BaseModel):
    """Response model for action item extraction."""
    action_items: List[str] = Field(default=[], description="Extracted action items")
    urgency: str = Field(..., description="Urgency level of action items")
    deadline: Optional[str] = Field(None, description="Deadline if detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence score")
    due_date: Optional[str] = Field(None, description="Due date in readable format")
    action_required: Optional[str] = Field(None, description="Primary action required")
    explanation: Optional[str] = Field(None, description="Explanation of action requirements")
    relevance: Optional[str] = Field(None, description="Relevance to user context")
    links: List[str] = Field(default=[], description="Relevant links from email")


class SummaryRequest(BaseModel):
    """Request model for email summarization."""
    email_content: str = Field(..., description="Email content to summarize")
    summary_type: str = Field(default="brief", description="Type of summary: brief or detailed")


class SummaryResponse(BaseModel):
    """Response model for email summarization."""
    summary: str = Field(..., description="Generated email summary")
    key_points: List[str] = Field(default=[], description="Key points extracted from email")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Summary quality confidence")
    processing_time: float = Field(..., description="Processing time in seconds")


class AIErrorResponse(BaseModel):
    """Error response model for AI processing failures."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class AvailableTemplatesResponse(BaseModel):
    """Response model for available prompt templates."""
    templates: List[str] = Field(..., description="List of available template names")
    descriptions: Dict[str, str] = Field(default={}, description="Template descriptions")