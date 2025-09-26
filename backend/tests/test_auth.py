"""Tests for authentication endpoints."""

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
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "testpassword123"
    }


def test_user_registration(test_user):
    """Test user registration."""
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 201
    
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert "id" in data
    assert "created_at" in data
    assert data["is_active"] is True


def test_duplicate_user_registration(test_user):
    """Test duplicate user registration fails."""
    # Register first user
    client.post("/auth/register", json=test_user)
    
    # Try to register same user again
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 400
    # Check that error message contains "already registered"
    response_data = response.json()
    assert "already registered" in response_data.get("message", response_data.get("detail", ""))


def test_user_login(test_user):
    """Test user login."""
    # Register user first
    client.post("/auth/register", json=test_user)
    
    # Login
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data
    assert "refresh_token" in data
    assert "expires_in" in data


def test_invalid_login():
    """Test login with invalid credentials."""
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401


def test_get_current_user(test_user):
    """Test getting current user information."""
    # Register and login user
    client.post("/auth/register", json=test_user)
    login_response = client.post("/auth/login", json={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current user
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    
    user_data = response.json()
    assert user_data["username"] == test_user["username"]
    assert user_data["email"] == test_user["email"]


def test_unauthorized_access():
    """Test accessing protected endpoint without token."""
    response = client.get("/auth/me")
    assert response.status_code == 403  # FastAPI security returns 403 for missing auth


def test_invalid_token():
    """Test accessing protected endpoint with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401