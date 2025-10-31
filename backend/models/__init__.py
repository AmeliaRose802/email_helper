"""Pydantic models for FastAPI Email Helper API."""

from .email import Email, EmailCreate, EmailUpdate, EmailInDB, EmailClassification, EmailBatch, EmailBatchResult
from .task import Task, TaskCreate, TaskUpdate, TaskInDB
from .ai_models import (
    EmailClassificationRequest, EmailClassificationResponse,
    ActionItemRequest, ActionItemResponse,
    SummaryRequest, SummaryResponse,
    AIErrorResponse, AvailableTemplatesResponse
)

__all__ = [
    "Email", "EmailCreate", "EmailUpdate", "EmailInDB", 
    "EmailClassification", "EmailBatch", "EmailBatchResult",
    "Task", "TaskCreate", "TaskUpdate", "TaskInDB",
    "EmailClassificationRequest", "EmailClassificationResponse",
    "ActionItemRequest", "ActionItemResponse",
    "SummaryRequest", "SummaryResponse",
    "AIErrorResponse", "AvailableTemplatesResponse"
]
