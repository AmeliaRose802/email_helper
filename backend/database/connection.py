"""Database connection management for FastAPI Email Helper API.

This module provides database connection management using existing database
patterns while integrating with FastAPI's dependency injection system.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from backend.core.config import get_database_path


class DatabaseManager:
    """Database connection manager for FastAPI application."""
    
    def __init__(self):
        self.db_path = get_database_path()
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database exists and is properly initialized."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Create basic database structure
        self._create_basic_structure()
    
    def _create_basic_structure(self):
        """Create basic database structure if migrations are not available."""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS emails (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    recipient TEXT,
                    content TEXT,
                    received_date TIMESTAMP,
                    category TEXT,
                    confidence REAL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'todo',
                    priority TEXT DEFAULT 'medium',
                    category TEXT,
                    due_date TIMESTAMP,
                    tags TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    email_id TEXT,
                    user_id INTEGER,
                    FOREIGN KEY (email_id) REFERENCES emails (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 🚀 PERFORMANCE OPTIMIZATION: Add indexes for common query patterns
            # These indexes significantly speed up filtering, sorting, and joins
            
            # Email indexes - speeds up category filtering and date sorting
            conn.execute('CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_emails_received_date ON emails(received_date DESC)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_emails_user_id ON emails(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender)')
            
            # Task indexes - speeds up status filtering, priority sorting, and due date queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_email_id ON tasks(email_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC)')
            
            # Composite index for common task queries (status + user_id)
            conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status)')
            
            # User index - speeds up username lookups during authentication
            conn.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
            
            conn.commit()
            print("[DB] Basic database structure verified with performance indexes", flush=True)
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def get_connection_sync(self) -> sqlite3.Connection:
        """Get synchronous database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn


# Global database manager instance
db_manager = DatabaseManager()


def get_database() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency for database connection."""
    with db_manager.get_connection() as conn:
        yield conn


def get_database_manager() -> DatabaseManager:
    """FastAPI dependency for database manager."""
    return db_manager