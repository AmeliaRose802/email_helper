"""Integration tests for Task Management API.

This module tests the complete task management workflow from creation
to completion, demonstrating all API features working together.
"""

import pytest
import time
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


@pytest.mark.skip(reason="Authentication removed - tests require auth endpoints")
def test_complete_task_workflow():
    """Test the complete task management workflow."""
    
    # Create a unique test user
    timestamp = str(int(time.time()))
    test_user = {
        "username": f"integration_user_{timestamp}",
        "email": f"integration_{timestamp}@example.com",
        "password": "integrationtest123"
    }
    
    # 1. Register user
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["username"] == test_user["username"]
    
    # 2. Login and get token
    login_response = client.post("/auth/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Create multiple tasks
    tasks_created = []
    task_data_list = [
        {
            "title": "Review pull request #123",
            "description": "Code review for new feature implementation",
            "priority": "high",
            "email_id": "outlook-email-pr123"
        },
        {
            "title": "Update documentation",
            "description": "Add API documentation for new endpoints",
            "priority": "medium"
        },
        {
            "title": "Fix bug in authentication",
            "description": "Resolve token expiration issue",
            "priority": "urgent"
        },
        {
            "title": "Team meeting preparation",
            "description": "Prepare agenda for sprint planning",
            "priority": "low"
        }
    ]
    
    for task_data in task_data_list:
        response = client.post("/api/tasks", json=task_data, headers=headers)
        assert response.status_code == 201
        tasks_created.append(response.json())
    
    # 4. Verify all tasks were created
    response = client.get("/api/tasks", headers=headers)
    assert response.status_code == 200
    all_tasks = response.json()
    assert len(all_tasks["tasks"]) == 4
    assert all_tasks["total_count"] == 4
    
    # 5. Test pagination
    response = client.get("/api/tasks?page=1&limit=2", headers=headers)
    assert response.status_code == 200
    page1_data = response.json()
    assert len(page1_data["tasks"]) == 2
    assert page1_data["has_next"] is True
    
    response = client.get("/api/tasks?page=2&limit=2", headers=headers)
    assert response.status_code == 200
    page2_data = response.json()
    assert len(page2_data["tasks"]) == 2
    assert page2_data["has_next"] is False
    
    # 6. Test filtering by priority
    response = client.get("/api/tasks?priority=high", headers=headers)
    assert response.status_code == 200
    high_priority_tasks = response.json()
    assert len(high_priority_tasks["tasks"]) == 1
    assert high_priority_tasks["tasks"][0]["title"] == "Review pull request #123"
    
    # 7. Test search functionality
    response = client.get("/api/tasks?search=authentication", headers=headers)
    assert response.status_code == 200
    search_results = response.json()
    assert len(search_results["tasks"]) == 1
    assert "authentication" in search_results["tasks"][0]["title"]
    
    # 8. Update a task
    task_to_update = tasks_created[0]
    update_data = {
        "status": "in_progress",
        "description": "Started code review - looks good so far"
    }
    response = client.put(f"/api/tasks/{task_to_update['id']}", json=update_data, headers=headers)
    assert response.status_code == 200
    updated_task = response.json()
    assert updated_task["status"] == "in_progress"
    assert "Started code review" in updated_task["description"]
    
    # 9. Test bulk operations - mark multiple tasks as completed
    task_ids_to_complete = [tasks_created[1]["id"], tasks_created[2]["id"]]
    bulk_update_data = {
        "task_ids": task_ids_to_complete,
        "updates": {"status": "completed"}
    }
    response = client.post("/api/tasks/bulk-update", json=bulk_update_data, headers=headers)
    assert response.status_code == 200
    bulk_updated = response.json()
    assert len(bulk_updated) == 2
    assert all(task["status"] == "completed" for task in bulk_updated)
    
    # 10. Verify filtering by status
    response = client.get("/api/tasks?status=completed", headers=headers)
    assert response.status_code == 200
    completed_tasks = response.json()
    assert len(completed_tasks["tasks"]) == 2
    
    # 11. Test email linking
    task_to_link = tasks_created[3]
    email_id = "important-email-456"
    response = client.post(f"/api/tasks/{task_to_link['id']}/link-email?email_id={email_id}", headers=headers)
    assert response.status_code == 200
    link_result = response.json()
    assert link_result["task"]["email_id"] == email_id
    
    # 12. Test bulk deletion
    task_to_delete = tasks_created[3]["id"]
    bulk_delete_data = {"task_ids": [task_to_delete]}
    response = client.post("/api/tasks/bulk-delete", json=bulk_delete_data, headers=headers)
    assert response.status_code == 200
    delete_result = response.json()
    assert delete_result["deleted_count"] == 1
    
    # 13. Verify task was deleted
    response = client.get(f"/api/tasks/{task_to_delete}", headers=headers)
    assert response.status_code == 404
    
    # 14. Final verification - should have 3 tasks remaining
    response = client.get("/api/tasks", headers=headers)
    assert response.status_code == 200
    final_tasks = response.json()
    assert final_tasks["total_count"] == 3
    
    print("✅ Complete task workflow integration test passed!")
    print(f"✅ Created {len(task_data_list)} tasks")
    print("✅ Tested pagination, filtering, search")
    print("✅ Tested task updates and bulk operations")
    print("✅ Tested email linking")
    print("✅ Tested task deletion")
    print("✅ All operations working correctly!")


@pytest.mark.skip(reason="Authentication removed - user isolation no longer applicable")
def test_user_isolation_in_workflow():
    """Test that users cannot interfere with each other's tasks."""
    
    timestamp = str(int(time.time()))
    
    # Create two users
    user1 = {
        "username": f"user1_isolation_{timestamp}",
        "email": f"user1_isolation_{timestamp}@example.com",
        "password": "testpass123"
    }
    
    user2 = {
        "username": f"user2_isolation_{timestamp}",  
        "email": f"user2_isolation_{timestamp}@example.com",
        "password": "testpass123"
    }
    
    # Register both users
    client.post("/auth/register", json=user1)
    client.post("/auth/register", json=user2)
    
    # Get tokens for both users
    token1 = client.post("/auth/login", json={
        "username": user1["username"], 
        "password": user1["password"]
    }).json()["access_token"]
    
    token2 = client.post("/auth/login", json={
        "username": user2["username"],
        "password": user2["password"]
    }).json()["access_token"]
    
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # User 1 creates tasks
    task1_data = {"title": "User 1 Private Task", "priority": "high"}
    response = client.post("/api/tasks", json=task1_data, headers=headers1)
    assert response.status_code == 201
    user1_task = response.json()
    
    # User 2 creates tasks
    task2_data = {"title": "User 2 Private Task", "priority": "low"}
    response = client.post("/api/tasks", json=task2_data, headers=headers2)
    assert response.status_code == 201
    user2_task = response.json()
    
    # User 1 should only see their own tasks
    response = client.get("/api/tasks", headers=headers1)
    assert response.status_code == 200
    user1_tasks = response.json()
    assert len(user1_tasks["tasks"]) == 1
    assert user1_tasks["tasks"][0]["title"] == "User 1 Private Task"
    
    # User 2 should only see their own tasks
    response = client.get("/api/tasks", headers=headers2)
    assert response.status_code == 200
    user2_tasks = response.json()
    assert len(user2_tasks["tasks"]) == 1
    assert user2_tasks["tasks"][0]["title"] == "User 2 Private Task"
    
    # User 2 should not be able to access User 1's task
    response = client.get(f"/api/tasks/{user1_task['id']}", headers=headers2)
    assert response.status_code == 404
    
    # User 2 should not be able to update User 1's task
    response = client.put(f"/api/tasks/{user1_task['id']}", 
                         json={"title": "Hacked Task"}, headers=headers2)
    assert response.status_code == 404
    
    # User 2 should not be able to delete User 1's task
    response = client.delete(f"/api/tasks/{user1_task['id']}", headers=headers2)
    assert response.status_code == 404
    
    print("✅ User isolation test passed!")
    print("✅ Users can only access their own tasks")
    print("✅ Cross-user task access properly blocked")