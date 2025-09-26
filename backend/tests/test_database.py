"""Tests for database connection and management."""

import pytest
import tempfile
import os
from backend.database.connection import DatabaseManager, get_database


def test_database_manager_initialization():
    """Test database manager initialization."""
    manager = DatabaseManager()
    assert manager.db_path is not None
    assert os.path.exists(manager.db_path) or os.path.exists(os.path.dirname(manager.db_path))


def test_database_connection():
    """Test database connection context manager."""
    manager = DatabaseManager()
    
    with manager.get_connection() as conn:
        cursor = conn.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1


def test_database_structure():
    """Test that required database tables exist."""
    manager = DatabaseManager()
    
    with manager.get_connection() as conn:
        # Check if users table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        assert cursor.fetchone() is not None
        
        # Check if emails table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='emails'"
        )
        assert cursor.fetchone() is not None
        
        # Check if tasks table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
        )
        assert cursor.fetchone() is not None


def test_database_user_operations():
    """Test basic user database operations."""
    import time
    timestamp = str(int(time.time()))
    
    manager = DatabaseManager()
    
    with manager.get_connection() as conn:
        # Insert test user with unique email
        cursor = conn.execute(
            """
            INSERT INTO users (username, email, hashed_password, is_active)
            VALUES (?, ?, ?, ?)
            """,
            (f"testuser_{timestamp}", f"test_{timestamp}@example.com", "hashed_password", True)
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        # Retrieve user
        cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        assert user is not None
        assert user["username"] == f"testuser_{timestamp}"
        assert user["email"] == f"test_{timestamp}@example.com"
        assert user["is_active"] == 1  # SQLite stores boolean as integer
        
        # Clean up
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()


def test_get_database_dependency():
    """Test the FastAPI database dependency."""
    db_gen = get_database()
    conn = next(db_gen)
    
    # Test connection works
    cursor = conn.execute("SELECT 1")
    result = cursor.fetchone()
    assert result[0] == 1
    
    # Close the generator
    try:
        next(db_gen)
    except StopIteration:
        pass  # Expected behavior