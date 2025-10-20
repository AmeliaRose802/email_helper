"""Task models for FastAPI Email Helper API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""
    TODO = "todo"
    PENDING = "pending"
    IN_PROGRESS = "in-progress" 
    REVIEW = "review"
    DONE = "done"
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
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    category: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict] = None


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
    email_id: Optional[str] = None


class TaskListResponse(BaseModel):
    """Response model for paginated task lists."""
    tasks: list["Task"]
    total_count: int
    page: int
    page_size: int
    has_next: bool


class BulkTaskUpdate(BaseModel):
    """Model for bulk task updates."""
    task_ids: list[int]
    updates: TaskUpdate


class BulkTaskDelete(BaseModel):
    """Model for bulk task deletion."""
    task_ids: list[int]


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
    id: str  # String for frontend compatibility
    created_at: datetime
    updated_at: datetime
    email_id: Optional[str] = None

    model_config = {"from_attributes": True}