"""Task management API endpoints for Email Helper."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.models.task import (
    Task, TaskCreate, TaskUpdate, TaskListResponse, 
    BulkTaskUpdate, BulkTaskDelete
)
from backend.models.user import UserInDB
from backend.services.task_service import TaskService, get_task_service

router = APIRouter()

# Default localhost user ID for development
LOCALHOST_USER_ID = 1


@router.post("/tasks", response_model=Task, status_code=201)
async def create_task(
    task: TaskCreate,
    task_service: TaskService = Depends(get_task_service)
):
    """Create a new task."""
    try:
        result = await task_service.create_task(task, LOCALHOST_USER_ID)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create task")


@router.get("/tasks", response_model=TaskListResponse)
async def get_tasks(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by task status"),
    priority: Optional[str] = Query(None, description="Filter by task priority"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    task_service: TaskService = Depends(get_task_service)
):
    """Get paginated list of tasks with filtering."""
    try:
        result = await task_service.get_tasks_paginated(
            user_id=LOCALHOST_USER_ID,
            page=page,
            limit=limit,
            status=status,
            priority=priority,
            search=search
        )
        
        return TaskListResponse(
            tasks=result.tasks,
            total_count=result.total_count,
            page=result.page,
            page_size=result.page_size,
            has_next=result.has_next
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")


@router.get("/tasks/stats")
async def get_task_stats(
    task_service: TaskService = Depends(get_task_service)
):
    """Get task statistics for the current user."""
    try:
        stats = await task_service.get_task_stats(LOCALHOST_USER_ID)
        return stats
    except Exception as e:
        # Return mock stats if there's an error
        return {
            "total_tasks": 0,
            "pending_tasks": 0,
            "completed_tasks": 0,
            "overdue_tasks": 0,
            "tasks_by_priority": {},
            "tasks_by_category": {}
        }


@router.get("/tasks/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
):
    """Get a specific task by ID."""
    task = await task_service.get_task(int(task_id), LOCALHOST_USER_ID)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    updates: TaskUpdate,
    task_service: TaskService = Depends(get_task_service)
):
    """Update a specific task."""
    try:
        result = await task_service.update_task(int(task_id), updates, LOCALHOST_USER_ID)
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update task")


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
):
    """Delete a specific task."""
    try:
        success = await task_service.delete_task(int(task_id), LOCALHOST_USER_ID)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete task")


@router.post("/tasks/bulk-update", response_model=List[Task])
async def bulk_update_tasks(
    bulk_update: BulkTaskUpdate,
    task_service: TaskService = Depends(get_task_service)
):
    """Update multiple tasks at once."""
    try:
        results = await task_service.bulk_update_tasks(
            bulk_update.task_ids,
            bulk_update.updates,
            LOCALHOST_USER_ID
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to bulk update tasks")


@router.post("/tasks/bulk-delete")
async def bulk_delete_tasks(
    bulk_delete: BulkTaskDelete,
    task_service: TaskService = Depends(get_task_service)
):
    """Delete multiple tasks at once."""
    try:
        deleted_count = await task_service.bulk_delete_tasks(
            bulk_delete.task_ids,
            LOCALHOST_USER_ID
        )
        return {
            "message": f"Successfully deleted {deleted_count} tasks",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to bulk delete tasks")


@router.put("/tasks/{task_id}/status", response_model=Task)
async def update_task_status(
    task_id: str,
    status: str = Query(..., description="New task status"),
    task_service: TaskService = Depends(get_task_service)
):
    """Update task status (for drag-and-drop operations)."""
    try:
        updates = TaskUpdate(status=TaskStatus(status))
        result = await task_service.update_task(int(task_id), updates, LOCALHOST_USER_ID)
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid status: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update task status")


@router.post("/tasks/{task_id}/link-email")
async def link_email_to_task(
    task_id: str,
    email_id: str,
    task_service: TaskService = Depends(get_task_service)
):
    """Link an email to a task."""
    try:
        # Create an update with the email_id
        updates = TaskUpdate(email_id=email_id)
        result = await task_service.update_task(int(task_id), updates, LOCALHOST_USER_ID)
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Email linked to task successfully", "task": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to link email to task")

