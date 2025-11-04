"""Tests for database connection and management."""

import os
import time
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


def test_database_email_operations():
    """Test email table CRUD operations."""
    timestamp = str(int(time.time()))
    manager = DatabaseManager()

    with manager.get_connection() as conn:
        # Insert test email
        email_id = f"test_email_{timestamp}"
        conn.execute(
            """
            INSERT INTO emails (id, subject, sender, recipient, content, category, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (email_id, "Test Subject", "sender@example.com", "recipient@example.com",
             "Test content", "work_relevant", 0.95)
        )
        conn.commit()

        # Retrieve email
        cursor = conn.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
        email = cursor.fetchone()
        assert email is not None
        assert email["subject"] == "Test Subject"
        assert email["category"] == "work_relevant"
        assert email["confidence"] == 0.95

        # Update email category
        conn.execute(
            "UPDATE emails SET category = ?, confidence = ? WHERE id = ?",
            ("fyi", 0.85, email_id)
        )
        conn.commit()

        # Verify update
        cursor = conn.execute("SELECT category, confidence FROM emails WHERE id = ?", (email_id,))
        updated = cursor.fetchone()
        assert updated["category"] == "fyi"
        assert updated["confidence"] == 0.85

        # Delete email
        conn.execute("DELETE FROM emails WHERE id = ?", (email_id,))
        conn.commit()

        # Verify deletion
        cursor = conn.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
        assert cursor.fetchone() is None


def test_database_task_operations():
    """Test task table CRUD operations."""
    timestamp = str(int(time.time()))
    manager = DatabaseManager()

    with manager.get_connection() as conn:
        # Insert test task
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, status, priority, category)
            VALUES (?, ?, ?, ?, ?)
            """,
            (f"Test Task {timestamp}", "Test description", "todo", "high", "work")
        )
        conn.commit()
        task_id = cursor.lastrowid

        # Retrieve task
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        assert task is not None
        assert task["title"] == f"Test Task {timestamp}"
        assert task["status"] == "todo"
        assert task["priority"] == "high"

        # Update task status
        conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            ("in_progress", task_id)
        )
        conn.commit()

        # Verify update
        cursor = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
        updated = cursor.fetchone()
        assert updated["status"] == "in_progress"

        # Delete task
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

        # Verify deletion
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        assert cursor.fetchone() is None


def test_database_indexes_exist():
    """Test that performance indexes are created."""
    manager = DatabaseManager()

    with manager.get_connection() as conn:
        # Check for email indexes
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_emails%'"
        )
        email_indexes = cursor.fetchall()
        assert len(email_indexes) >= 4  # Should have category, received_date, user_id, sender indexes

        # Check for task indexes
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_tasks%'"
        )
        task_indexes = cursor.fetchall()
        assert len(task_indexes) >= 6  # Should have status, priority, due_date, etc.

        # Check for user indexes
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_users%'"
        )
        user_indexes = cursor.fetchall()
        assert len(user_indexes) >= 2  # Should have username and email indexes


def test_database_transaction_rollback():
    """Test transaction rollback on error."""
    timestamp = str(int(time.time()))
    manager = DatabaseManager()

    with manager.get_connection() as conn:
        try:
            # Start a transaction
            email_id = f"test_rollback_{timestamp}"
            conn.execute(
                "INSERT INTO emails (id, subject, sender) VALUES (?, ?, ?)",
                (email_id, "Test", "test@example.com")
            )

            # Intentionally cause an error (duplicate primary key)
            conn.execute(
                "INSERT INTO emails (id, subject, sender) VALUES (?, ?, ?)",
                (email_id, "Test2", "test2@example.com")  # Same ID
            )

            conn.commit()
        except Exception:
            conn.rollback()

        # Verify rollback - email should not exist
        cursor = conn.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
        assert cursor.fetchone() is None


def test_database_foreign_key_constraints():
    """Test foreign key relationships between tables."""
    timestamp = str(int(time.time()))
    manager = DatabaseManager()

    with manager.get_connection() as conn:
        # Create a test user
        cursor = conn.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
            (f"fk_test_{timestamp}", f"fk_{timestamp}@example.com", "hash")
        )
        conn.commit()
        user_id = cursor.lastrowid

        # Create an email with user_id
        email_id = f"fk_email_{timestamp}"
        conn.execute(
            "INSERT INTO emails (id, subject, sender, user_id) VALUES (?, ?, ?, ?)",
            (email_id, "FK Test", "test@example.com", user_id)
        )
        conn.commit()

        # Create a task linked to the email
        cursor = conn.execute(
            "INSERT INTO tasks (title, email_id, user_id) VALUES (?, ?, ?)",
            (f"FK Task {timestamp}", email_id, user_id)
        )
        conn.commit()
        task_id = cursor.lastrowid

        # Verify relationships
        cursor = conn.execute(
            """
            SELECT t.title, e.subject, u.username 
            FROM tasks t
            JOIN emails e ON t.email_id = e.id
            JOIN users u ON t.user_id = u.id
            WHERE t.id = ?
            """,
            (task_id,)
        )
        result = cursor.fetchone()
        assert result is not None
        assert result["title"] == f"FK Task {timestamp}"
        assert result["subject"] == "FK Test"
        assert result["username"] == f"fk_test_{timestamp}"

        # Clean up
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.execute("DELETE FROM emails WHERE id = ?", (email_id,))
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


def test_get_connection_sync():
    """Test synchronous database connection."""
    manager = DatabaseManager()
    conn = manager.get_connection_sync()

    try:
        cursor = conn.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
    finally:
        conn.close()


def test_row_factory_dict_access():
    """Test that row_factory allows dict-style access."""
    timestamp = str(int(time.time()))
    manager = DatabaseManager()

    with manager.get_connection() as conn:
        # Insert test email
        email_id = f"dict_test_{timestamp}"
        conn.execute(
            "INSERT INTO emails (id, subject, sender) VALUES (?, ?, ?)",
            (email_id, "Dict Test", "dict@example.com")
        )
        conn.commit()

        # Retrieve and test dict access
        cursor = conn.execute("SELECT id, subject, sender FROM emails WHERE id = ?", (email_id,))
        row = cursor.fetchone()

        # Test column name access
        assert row["id"] == email_id
        assert row["subject"] == "Dict Test"
        assert row["sender"] == "dict@example.com"

        # Clean up
        conn.execute("DELETE FROM emails WHERE id = ?", (email_id,))
        conn.commit()
