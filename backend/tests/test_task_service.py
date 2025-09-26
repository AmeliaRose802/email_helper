"""Tests for task service layer."""

import pytest
import asyncio
from datetime import datetime, timedelta

from backend.services.task_service import TaskService, TaskListResponse
from backend.models.task import TaskCreate, TaskUpdate, TaskStatus, TaskPriority
from backend.database.connection import db_manager


class TestTaskService:
    """Test suite for TaskService."""
    
    @pytest.fixture
    def task_service(self):
        """Create task service instance."""
        return TaskService()
    
    @pytest.fixture
    def test_user_id(self):
        """Create a test user and return ID."""
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, email, hashed_password, is_active) VALUES (?, ?, ?, ?)",
                ("testuser_task", "test_task@example.com", "hashed_password", True)
            )
            conn.commit()
            user_id = cursor.lastrowid
            
            yield user_id
            
            # Cleanup - remove test user and their tasks
            conn.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
    
    @pytest.mark.asyncio
    async def test_create_task(self, task_service: TaskService, test_user_id: int):
        """Test task creation."""
        task_data = TaskCreate(
            title="Test Task",
            description="Test task description",
            priority=TaskPriority.HIGH,
            due_date=datetime.now() + timedelta(days=7)
        )
        
        result = await task_service.create_task(task_data, test_user_id)
        
        assert result.id is not None
        assert result.title == "Test Task"
        assert result.description == "Test task description"
        assert result.status == TaskStatus.PENDING
        assert result.priority == TaskPriority.HIGH
        assert result.due_date is not None
        assert result.created_at is not None
        assert result.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_get_task(self, task_service: TaskService, test_user_id: int):
        """Test getting a specific task."""
        # Create a task first
        task_data = TaskCreate(title="Get Test Task")
        created_task = await task_service.create_task(task_data, test_user_id)
        
        # Get the task
        result = await task_service.get_task(created_task.id, test_user_id)
        
        assert result is not None
        assert result.id == created_task.id
        assert result.title == "Get Test Task"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, task_service: TaskService, test_user_id: int):
        """Test getting a task that doesn't exist."""
        result = await task_service.get_task(99999, test_user_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_task(self, task_service: TaskService, test_user_id: int):
        """Test updating a task."""
        # Create a task first
        task_data = TaskCreate(title="Original Title")
        created_task = await task_service.create_task(task_data, test_user_id)
        
        # Update the task
        updates = TaskUpdate(
            title="Updated Title",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH
        )
        
        result = await task_service.update_task(created_task.id, updates, test_user_id)
        
        assert result is not None
        assert result.title == "Updated Title"
        assert result.status == TaskStatus.IN_PROGRESS
        assert result.priority == TaskPriority.HIGH
        assert result.updated_at > result.created_at
    
    @pytest.mark.asyncio
    async def test_delete_task(self, task_service: TaskService, test_user_id: int):
        """Test deleting a task."""
        # Create a task first
        task_data = TaskCreate(title="Task to Delete")
        created_task = await task_service.create_task(task_data, test_user_id)
        
        # Delete the task
        success = await task_service.delete_task(created_task.id, test_user_id)
        assert success is True
        
        # Verify it's gone
        result = await task_service.get_task(created_task.id, test_user_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_tasks_paginated(self, task_service: TaskService, test_user_id: int):
        """Test paginated task retrieval."""
        # Create multiple tasks
        tasks = []
        for i in range(5):
            task_data = TaskCreate(title=f"Task {i+1}")
            task = await task_service.create_task(task_data, test_user_id)
            tasks.append(task)
        
        # Get first page
        result = await task_service.get_tasks_paginated(
            user_id=test_user_id,
            page=1,
            limit=3
        )
        
        assert isinstance(result, TaskListResponse)
        assert len(result.tasks) == 3
        assert result.total_count == 5
        assert result.page == 1
        assert result.page_size == 3
        assert result.has_next is True
        
        # Get second page
        result_page2 = await task_service.get_tasks_paginated(
            user_id=test_user_id,
            page=2,
            limit=3
        )
        
        assert len(result_page2.tasks) == 2
        assert result_page2.has_next is False
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_status_filter(self, task_service: TaskService, test_user_id: int):
        """Test filtered task retrieval by status."""
        # Create tasks with different statuses
        task1_data = TaskCreate(title="Pending Task", status=TaskStatus.PENDING)
        task2_data = TaskCreate(title="In Progress Task", status=TaskStatus.IN_PROGRESS)
        
        await task_service.create_task(task1_data, test_user_id)
        await task_service.create_task(task2_data, test_user_id)
        
        # Filter by pending status
        result = await task_service.get_tasks_paginated(
            user_id=test_user_id,
            status="pending"
        )
        
        assert len(result.tasks) == 1
        assert result.tasks[0].status == TaskStatus.PENDING
        assert result.tasks[0].title == "Pending Task"
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_search(self, task_service: TaskService, test_user_id: int):
        """Test task search functionality."""
        # Create tasks with different titles
        task1_data = TaskCreate(title="Important meeting", description="Team sync")
        task2_data = TaskCreate(title="Review code", description="Important fixes")
        task3_data = TaskCreate(title="Random task", description="Other stuff")
        
        await task_service.create_task(task1_data, test_user_id)
        await task_service.create_task(task2_data, test_user_id)
        await task_service.create_task(task3_data, test_user_id)
        
        # Search for "important"
        result = await task_service.get_tasks_paginated(
            user_id=test_user_id,
            search="important"
        )
        
        assert len(result.tasks) == 2
        # Should find tasks containing "important" in title or description
    
    @pytest.mark.asyncio
    async def test_bulk_update_tasks(self, task_service: TaskService, test_user_id: int):
        """Test bulk task updates."""
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            task_data = TaskCreate(title=f"Bulk Task {i+1}")
            task = await task_service.create_task(task_data, test_user_id)
            task_ids.append(task.id)
        
        # Bulk update to completed status
        updates = TaskUpdate(status=TaskStatus.COMPLETED)
        results = await task_service.bulk_update_tasks(task_ids, updates, test_user_id)
        
        assert len(results) == 3
        for task in results:
            assert task.status == TaskStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_bulk_delete_tasks(self, task_service: TaskService, test_user_id: int):
        """Test bulk task deletion."""
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            task_data = TaskCreate(title=f"Delete Task {i+1}")
            task = await task_service.create_task(task_data, test_user_id)
            task_ids.append(task.id)
        
        # Bulk delete
        deleted_count = await task_service.bulk_delete_tasks(task_ids, test_user_id)
        
        assert deleted_count == 3
        
        # Verify all tasks are gone
        for task_id in task_ids:
            result = await task_service.get_task(task_id, test_user_id)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_link_email_to_task(self, task_service: TaskService, test_user_id: int):
        """Test linking an email to a task."""
        # Create a task
        task_data = TaskCreate(title="Task for Email Link")
        created_task = await task_service.create_task(task_data, test_user_id)
        
        # Link email to task
        email_id = "test-email-123"
        result = await task_service.link_email_to_task(created_task.id, email_id, test_user_id)
        
        assert result is not None
        assert result.email_id == email_id
    
    @pytest.mark.asyncio
    async def test_user_isolation(self, task_service: TaskService):
        """Test that users can only access their own tasks."""
        # Create two test users
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, email, hashed_password, is_active) VALUES (?, ?, ?, ?)",
                ("user1", "user1@example.com", "hashed_password", True)
            )
            conn.commit()
            user1_id = cursor.lastrowid
            
            cursor = conn.execute(
                "INSERT INTO users (username, email, hashed_password, is_active) VALUES (?, ?, ?, ?)",
                ("user2", "user2@example.com", "hashed_password", True)
            )
            conn.commit()
            user2_id = cursor.lastrowid
        
        try:
            # User 1 creates a task
            task_data = TaskCreate(title="User 1 Task")
            user1_task = await task_service.create_task(task_data, user1_id)
            
            # User 2 should not be able to access User 1's task
            result = await task_service.get_task(user1_task.id, user2_id)
            assert result is None
            
            # User 2 should not be able to update User 1's task
            updates = TaskUpdate(title="Hacked Task")
            result = await task_service.update_task(user1_task.id, updates, user2_id)
            assert result is None
            
            # User 2 should not be able to delete User 1's task
            success = await task_service.delete_task(user1_task.id, user2_id)
            assert success is False
            
        finally:
            # Cleanup
            with db_manager.get_connection() as conn:
                conn.execute("DELETE FROM tasks WHERE user_id IN (?, ?)", (user1_id, user2_id))
                conn.execute("DELETE FROM users WHERE id IN (?, ?)", (user1_id, user2_id))
                conn.commit()