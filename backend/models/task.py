"""Task models for FastAPI Email Helper API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskBase(BaseModel):
    """Base task model."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Task creation model."""
    email_id: Optional[str] = None


class TaskUpdate(BaseModel):
    """Task update model."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None


class TaskInDB(TaskBase):
    """Task model as stored in database."""
    id: int
    created_at: datetime
    updated_at: datetime
    email_id: Optional[str] = None
    user_id: Optional[int] = None

    model_config = {"from_attributes": True}


class Task(TaskBase):
    """Task model for API responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    email_id: Optional[str] = None

    model_config = {"from_attributes": True}