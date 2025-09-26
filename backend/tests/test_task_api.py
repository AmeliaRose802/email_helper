"""Tests for task API endpoints."""

import pytest
import time
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import db_manager

client = TestClient(app)


@pytest.fixture
def test_user():
    """Test user data with unique timestamp."""
    timestamp = str(int(time.time()))
    return {
        "username": f"taskuser_{timestamp}",
        "email": f"task_{timestamp}@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for test user."""
    # Register user
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 201
    
    # Login user
    login_response = client.post("/auth/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert login_response.status_code == 200
    
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestTaskAPI:
    """Test suite for Task API endpoints."""
    
    def test_create_task(self, auth_headers):
        """Test task creation endpoint."""
        task_data = {
            "title": "API Test Task",
            "description": "Test task via API",
            "priority": "high"
        }
        
        response = client.post("/api/tasks", json=task_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == "API Test Task"
        assert data["description"] == "Test task via API"
        assert data["status"] == "pending"
        assert data["priority"] == "high"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_task_minimal(self, auth_headers):
        """Test creating task with minimal data."""
        task_data = {
            "title": "Minimal Task"
        }
        
        response = client.post("/api/tasks", json=task_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == "Minimal Task"
        assert data["status"] == "pending"
        assert data["priority"] == "medium"  # Default values
    
    def test_create_task_with_email_link(self, auth_headers):
        """Test creating task with email association."""
        task_data = {
            "title": "Email-linked Task",
            "email_id": "test-email-123"
        }
        
        response = client.post("/api/tasks", json=task_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["email_id"] == "test-email-123"
    
    def test_create_task_invalid_data(self, auth_headers):
        """Test task creation with invalid data."""
        task_data = {
            "title": "",  # Empty title should fail
            "priority": "invalid_priority"
        }
        
        response = client.post("/api/tasks", json=task_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error
    
    def test_get_tasks_paginated(self, auth_headers):
        """Test getting paginated tasks."""
        # Create some tasks first
        for i in range(5):
            task_data = {"title": f"Pagination Test Task {i+1}"}
            response = client.post("/api/tasks", json=task_data, headers=auth_headers)
            assert response.status_code == 201
        
        # Get first page
        response = client.get("/api/tasks?page=1&limit=3", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["tasks"]) == 3
        assert data["total_count"] >= 5
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert data["has_next"] is True
        
        # Get second page
        response = client.get("/api/tasks?page=2&limit=3", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["tasks"]) >= 2
    
    def test_get_tasks_with_filters(self, auth_headers):
        """Test getting tasks with filters."""
        # Create tasks with different properties
        high_priority_task = {"title": "High Priority Task", "priority": "high"}
        pending_task = {"title": "Pending Task", "status": "pending"}
        
        client.post("/api/tasks", json=high_priority_task, headers=auth_headers)
        client.post("/api/tasks", json=pending_task, headers=auth_headers)
        
        # Filter by priority
        response = client.get("/api/tasks?priority=high", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["tasks"]) >= 1
        assert all(task["priority"] == "high" for task in data["tasks"])
        
        # Filter by status
        response = client.get("/api/tasks?status=pending", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert all(task["status"] == "pending" for task in data["tasks"])
    
    def test_get_tasks_with_search(self, auth_headers):
        """Test task search functionality."""
        # Create tasks with searchable content
        searchable_task = {
            "title": "Important Meeting",
            "description": "Team sync discussion"
        }
        other_task = {
            "title": "Random Task",
            "description": "Other work"
        }
        
        client.post("/api/tasks", json=searchable_task, headers=auth_headers)
        client.post("/api/tasks", json=other_task, headers=auth_headers)
        
        # Search for "important"
        response = client.get("/api/tasks?search=important", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["tasks"]) >= 1
        # Should find the task with "Important" in title
    
    def test_get_specific_task(self, auth_headers):
        """Test getting a specific task by ID."""
        # Create a task first
        task_data = {"title": "Specific Task Test"}
        create_response = client.post("/api/tasks", json=task_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        task_id = create_response.json()["id"]
        
        # Get the specific task
        response = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Specific Task Test"
    
    def test_get_nonexistent_task(self, auth_headers):
        """Test getting a task that doesn't exist."""
        response = client.get("/api/tasks/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_task(self, auth_headers):
        """Test updating a task."""
        # Create a task first
        task_data = {"title": "Original Title"}
        create_response = client.post("/api/tasks", json=task_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        task_id = create_response.json()["id"]
        
        # Update the task
        update_data = {
            "title": "Updated Title",
            "status": "in_progress",
            "priority": "high"
        }
        
        response = client.put(f"/api/tasks/{task_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "in_progress"
        assert data["priority"] == "high"
    
    def test_update_nonexistent_task(self, auth_headers):
        """Test updating a task that doesn't exist."""
        update_data = {"title": "Updated Title"}
        response = client.put("/api/tasks/99999", json=update_data, headers=auth_headers)
        assert response.status_code == 404
    
    def test_delete_task(self, auth_headers):
        """Test deleting a task."""
        # Create a task first
        task_data = {"title": "Task to Delete"}
        create_response = client.post("/api/tasks", json=task_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        task_id = create_response.json()["id"]
        
        # Delete the task
        response = client.delete(f"/api/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        
        # Verify it's gone
        get_response = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_task(self, auth_headers):
        """Test deleting a task that doesn't exist."""
        response = client.delete("/api/tasks/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_bulk_update_tasks(self, auth_headers):
        """Test bulk task updates."""
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            task_data = {"title": f"Bulk Update Task {i+1}"}
            response = client.post("/api/tasks", json=task_data, headers=auth_headers)
            assert response.status_code == 201
            task_ids.append(response.json()["id"])
        
        # Bulk update
        bulk_data = {
            "task_ids": task_ids,
            "updates": {
                "status": "completed",
                "priority": "high"
            }
        }
        
        response = client.post("/api/tasks/bulk-update", json=bulk_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        for task in data:
            assert task["status"] == "completed"
            assert task["priority"] == "high"
    
    def test_bulk_delete_tasks(self, auth_headers):
        """Test bulk task deletion."""
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            task_data = {"title": f"Bulk Delete Task {i+1}"}
            response = client.post("/api/tasks", json=task_data, headers=auth_headers)
            assert response.status_code == 201
            task_ids.append(response.json()["id"])
        
        # Bulk delete
        bulk_data = {"task_ids": task_ids}
        
        response = client.post("/api/tasks/bulk-delete", json=bulk_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["deleted_count"] == 3
        
        # Verify all tasks are gone
        for task_id in task_ids:
            get_response = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
            assert get_response.status_code == 404
    
    def test_link_email_to_task(self, auth_headers):
        """Test linking an email to a task."""
        # Create a task first
        task_data = {"title": "Task for Email Link"}
        create_response = client.post("/api/tasks", json=task_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        task_id = create_response.json()["id"]
        email_id = "test-email-456"
        
        # Link email to task
        response = client.post(f"/api/tasks/{task_id}/link-email?email_id={email_id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["task"]["email_id"] == email_id
    
    def test_unauthorized_access(self):
        """Test accessing endpoints without authentication."""
        # Try to create task without auth
        task_data = {"title": "Unauthorized Task"}
        response = client.post("/api/tasks", json=task_data)
        assert response.status_code == 403
        
        # Try to get tasks without auth
        response = client.get("/api/tasks")
        assert response.status_code == 403
        
        # Try to get specific task without auth
        response = client.get("/api/tasks/1")
        assert response.status_code == 403
    
    def test_user_isolation(self):
        """Test that users can only access their own tasks."""
        # Create two users
        user1 = {
            "username": f"user1_{int(time.time())}",
            "email": f"user1_{int(time.time())}@example.com",
            "password": "password123"
        }
        user2 = {
            "username": f"user2_{int(time.time())}",
            "email": f"user2_{int(time.time())}@example.com",
            "password": "password123"
        }
        
        # Register both users
        client.post("/auth/register", json=user1)
        client.post("/auth/register", json=user2)
        
        # Login both users
        login1_response = client.post("/auth/login", json={
            "username": user1["username"],
            "password": user1["password"]
        })
        login2_response = client.post("/auth/login", json={
            "username": user2["username"],
            "password": user2["password"]
        })
        
        token1 = login1_response.json()["access_token"]
        token2 = login2_response.json()["access_token"]
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # User 1 creates a task
        task_data = {"title": "User 1 Task"}
        create_response = client.post("/api/tasks", json=task_data, headers=headers1)
        assert create_response.status_code == 201
        
        task_id = create_response.json()["id"]
        
        # User 2 should not be able to access User 1's task
        response = client.get(f"/api/tasks/{task_id}", headers=headers2)
        assert response.status_code == 404
        
        # User 2 should not be able to update User 1's task
        update_data = {"title": "Hacked Task"}
        response = client.put(f"/api/tasks/{task_id}", json=update_data, headers=headers2)
        assert response.status_code == 404
        
        # User 2 should not be able to delete User 1's task
        response = client.delete(f"/api/tasks/{task_id}", headers=headers2)
        assert response.status_code == 404