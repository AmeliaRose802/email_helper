"""Task service layer for Email Helper API.

This module provides the business logic layer for task management operations,
serving as an async wrapper around the existing TaskPersistence system while
providing additional database integration for user-scoped operations.
"""

import asyncio
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any

from backend.database.connection import db_manager
from backend.models.task import Task, TaskCreate, TaskUpdate, TaskStatus, TaskPriority
from backend.core.domain.task_persistence import TaskPersistence


class TaskListResponse:
    """Response model for paginated task lists."""

    def __init__(
        self,
        tasks: List[Task],
        total_count: int,
        page: int,
        page_size: int,
        has_next: bool
    ):
        self.tasks = tasks
        self.total_count = total_count
        self.page = page
        self.page_size = page_size
        self.has_next = has_next


class TaskService:
    """Service layer for task management operations."""

    def __init__(self):
        """Initialize the task service."""
        self.task_persistence = TaskPersistence()

    async def create_task(self, task_data: TaskCreate, user_id: int) -> Task:
        """Create a new task."""
        loop = asyncio.get_event_loop()

        def _create_task_sync():
            import json
            current_time = datetime.now()

            # Serialize tags and metadata to JSON
            tags_json = json.dumps(task_data.tags if task_data.tags else [])
            metadata_json = json.dumps(task_data.metadata if task_data.metadata else {})

            with db_manager.get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO tasks (title, description, status, priority, category, 
                                     due_date, tags, metadata, created_at, updated_at, 
                                     email_id, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_data.title,
                        task_data.description,
                        task_data.status.value,
                        task_data.priority.value,
                        task_data.category,
                        task_data.due_date,
                        tags_json,
                        metadata_json,
                        current_time,
                        current_time,
                        task_data.email_id,
                        user_id
                    )
                )

                task_id = cursor.lastrowid
                conn.commit()

                # Retrieve the created task
                cursor = conn.execute(
                    "SELECT * FROM tasks WHERE id = ?",
                    (task_id,)
                )

                row = cursor.fetchone()
                if not row:
                    raise ValueError("Failed to create task")

                return self._row_to_task(row)

        return await loop.run_in_executor(None, _create_task_sync)

    async def get_task(self, task_id: int, user_id: int) -> Optional[Task]:
        """Get a specific task by ID."""
        loop = asyncio.get_event_loop()

        def _get_task_sync():
            with db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
                    (task_id, user_id)
                )

                row = cursor.fetchone()
                if not row:
                    return None

                return self._row_to_task(row)

        return await loop.run_in_executor(None, _get_task_sync)

    async def update_task(self, task_id: int, updates: TaskUpdate, user_id: int) -> Optional[Task]:
        """Update a specific task."""
        loop = asyncio.get_event_loop()

        def _update_task_sync():
            # Build dynamic update query
            update_fields = []
            update_values = []

            if updates.title is not None:
                update_fields.append("title = ?")
                update_values.append(updates.title)

            if updates.description is not None:
                update_fields.append("description = ?")
                update_values.append(updates.description)

            if updates.status is not None:
                update_fields.append("status = ?")
                update_values.append(updates.status.value)

            if updates.priority is not None:
                update_fields.append("priority = ?")
                update_values.append(updates.priority.value)

            if updates.due_date is not None:
                update_fields.append("due_date = ?")
                update_values.append(updates.due_date)

            if updates.email_id is not None:
                update_fields.append("email_id = ?")
                update_values.append(updates.email_id)

            if not update_fields:
                # No updates provided, return current task
                with db_manager.get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
                        (task_id, user_id)
                    )
                    row = cursor.fetchone()
                    return self._row_to_task(row) if row else None

            # Always update the updated_at timestamp
            update_fields.append("updated_at = ?")
            update_values.append(datetime.now())

            # Add WHERE clause values
            update_values.extend([task_id, user_id])

            query = f"""
            UPDATE tasks 
            SET {', '.join(update_fields)}
            WHERE id = ? AND user_id = ?
            """

            with db_manager.get_connection() as conn:
                cursor = conn.execute(query, update_values)
                conn.commit()

                if cursor.rowcount == 0:
                    return None  # Task not found or not owned by user

                # Return updated task
                cursor = conn.execute(
                    "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
                    (task_id, user_id)
                )
                row = cursor.fetchone()
                return self._row_to_task(row) if row else None

        return await loop.run_in_executor(None, _update_task_sync)

    async def delete_task(self, task_id: int, user_id: int) -> bool:
        """Delete a specific task."""
        loop = asyncio.get_event_loop()

        def _delete_task_sync():
            with db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM tasks WHERE id = ? AND user_id = ?",
                    (task_id, user_id)
                )
                conn.commit()
                return cursor.rowcount > 0

        return await loop.run_in_executor(None, _delete_task_sync)

    async def get_tasks_paginated(
        self,
        user_id: int,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None
    ) -> TaskListResponse:
        """Get paginated list of tasks with filtering."""
        loop = asyncio.get_event_loop()

        def _get_tasks_sync():
            # Build WHERE clause
            where_conditions = ["user_id = ?"]
            where_values = [user_id]

            if status:
                where_conditions.append("status = ?")
                where_values.append(status)

            if priority:
                where_conditions.append("priority = ?")
                where_values.append(priority)

            if search:
                where_conditions.append("(title LIKE ? OR description LIKE ?)")
                search_term = f"%{search}%"
                where_values.extend([search_term, search_term])

            where_clause = " AND ".join(where_conditions)

            # Calculate offset
            offset = (page - 1) * limit

            with db_manager.get_connection() as conn:
                # Get total count
                count_query = f"SELECT COUNT(*) FROM tasks WHERE {where_clause}"
                cursor = conn.execute(count_query, where_values)
                total_count = cursor.fetchone()[0]

                # Get paginated results
                tasks_query = f"""
                SELECT id, title, description, status, priority, category,
                       due_date, tags, metadata, created_at, updated_at, email_id
                FROM tasks 
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """

                cursor = conn.execute(
                    tasks_query,
                    where_values + [limit, offset]
                )

                rows = cursor.fetchall()
                tasks = [self._row_to_task(row) for row in rows]

                # Calculate if there are more pages
                has_next = (page * limit) < total_count

                return TaskListResponse(
                    tasks=tasks,
                    total_count=total_count,
                    page=page,
                    page_size=limit,
                    has_next=has_next
                )

        return await loop.run_in_executor(None, _get_tasks_sync)

    async def bulk_update_tasks(
        self,
        task_ids: List[int],
        updates: TaskUpdate,
        user_id: int
    ) -> List[Task]:
        """Update multiple tasks at once."""
        results = []
        for task_id in task_ids:
            updated_task = await self.update_task(task_id, updates, user_id)
            if updated_task:
                results.append(updated_task)
        return results

    async def bulk_delete_tasks(self, task_ids: List[int], user_id: int) -> int:
        """Delete multiple tasks at once."""
        loop = asyncio.get_event_loop()

        def _bulk_delete_sync():
            if not task_ids:
                return 0

            placeholders = ", ".join("?" for _ in task_ids)
            query = f"DELETE FROM tasks WHERE id IN ({placeholders}) AND user_id = ?"

            with db_manager.get_connection() as conn:
                cursor = conn.execute(query, task_ids + [user_id])
                conn.commit()
                return cursor.rowcount

        return await loop.run_in_executor(None, _bulk_delete_sync)

    async def link_email_to_task(self, task_id: int, email_id: str, user_id: int) -> Optional[Task]:
        """Link an email to a task."""
        updates = TaskUpdate(email_id=email_id)
        return await self.update_task(task_id, updates, user_id)

    async def get_task_stats(self, user_id: int) -> Dict[str, Any]:
        """Get task statistics for a user."""
        loop = asyncio.get_event_loop()

        def _get_stats_sync():
            with db_manager.get_connection() as conn:
                # Total tasks
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM tasks WHERE user_id = ?",
                    (user_id,)
                )
                total_tasks = cursor.fetchone()[0]

                # Pending tasks (not completed)
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status != 'done'",
                    (user_id,)
                )
                pending_tasks = cursor.fetchone()[0]

                # Completed tasks
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'done'",
                    (user_id,)
                )
                completed_tasks = cursor.fetchone()[0]

                # Overdue tasks
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM tasks 
                    WHERE user_id = ? 
                    AND status != 'done' 
                    AND due_date IS NOT NULL 
                    AND due_date < datetime('now')
                    """,
                    (user_id,)
                )
                overdue_tasks = cursor.fetchone()[0]

                # Tasks by priority
                cursor = conn.execute(
                    """
                    SELECT priority, COUNT(*) 
                    FROM tasks 
                    WHERE user_id = ? 
                    GROUP BY priority
                    """,
                    (user_id,)
                )
                tasks_by_priority = {row[0]: row[1] for row in cursor.fetchall()}

                # Tasks by category (if category column exists)
                try:
                    cursor = conn.execute(
                        """
                        SELECT status, COUNT(*) 
                        FROM tasks 
                        WHERE user_id = ? 
                        GROUP BY status
                        """,
                        (user_id,)
                    )
                    tasks_by_category = {row[0]: row[1] for row in cursor.fetchall()}
                except sqlite3.OperationalError:
                    tasks_by_category = {}

                return {
                    "total_tasks": total_tasks,
                    "pending_tasks": pending_tasks,
                    "completed_tasks": completed_tasks,
                    "overdue_tasks": overdue_tasks,
                    "tasks_by_priority": tasks_by_priority,
                    "tasks_by_category": tasks_by_category
                }

        return await loop.run_in_executor(None, _get_stats_sync)

    def _row_to_task(self, row) -> Task:
        """Convert database row to Task model."""
        import json

        # Convert sqlite3.Row to dict for easier access
        row_dict = dict(row)

        # Parse JSON fields safely
        tags = []
        metadata = {}

        try:
            tags_str = row_dict.get("tags")
            if tags_str:
                tags = json.loads(tags_str)
        except (json.JSONDecodeError, TypeError, AttributeError):
            tags = []

        try:
            metadata_str = row_dict.get("metadata")
            if metadata_str:
                metadata = json.loads(metadata_str)
        except (json.JSONDecodeError, TypeError, AttributeError):
            metadata = {}

        return Task(
            id=str(row_dict["id"]),  # Convert to string for frontend compatibility
            title=row_dict["title"],
            description=row_dict.get("description") or "",
            status=TaskStatus(row_dict["status"]),
            priority=TaskPriority(row_dict["priority"]),
            category=row_dict.get("category"),
            due_date=row_dict.get("due_date"),
            tags=tags,
            metadata=metadata,
            created_at=row_dict["created_at"],
            updated_at=row_dict["updated_at"],
            email_id=row_dict.get("email_id")
        )


# Dependency for FastAPI
def get_task_service() -> TaskService:
    """FastAPI dependency for task service."""
    return TaskService()
