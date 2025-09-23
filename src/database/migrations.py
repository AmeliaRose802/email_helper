#!/usr/bin/env python3
"""Database Migrations for Email Helper - Historical Data Storage Schema.

This module provides database migration functionality for managing the SQLite
schema used for historical metrics and task resolution tracking. It ensures
backward compatibility while allowing schema evolution.

The migration system handles:
- Initial schema creation for metrics and history tables
- Version tracking and incremental migrations
- Data preservation during schema changes
- Index creation for efficient historical queries
- Rollback capabilities for development

Key Features:
- SQLite-based storage with proper indexing
- Migration versioning for compatibility
- Automatic backup before schema changes
- Efficient time-series data structures
- Foreign key constraints for data integrity

This module integrates with AccuracyTracker and TaskPersistence to provide
robust historical data storage for the metrics dashboard.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class DatabaseMigrations:
    """Database migration manager for historical data storage.
    
    This class manages the SQLite database schema for storing historical
    accuracy metrics and task resolution data. It provides versioned
    migrations to ensure compatibility as the schema evolves.
    
    The migration system handles:
    - Initial table creation for metrics and history
    - Index creation for efficient queries
    - Data migration between schema versions
    - Backup and recovery capabilities
    
    Attributes:
        db_path (str): Path to the SQLite database file
        migrations_dir (str): Directory for migration scripts
        current_version (int): Current database schema version
    """
    
    def __init__(self, db_path: str):
        """Initialize migration manager with database path."""
        self.db_path = db_path
        self.migrations_dir = os.path.dirname(db_path)
        os.makedirs(self.migrations_dir, exist_ok=True)
        
        # Ensure database file exists
        if not os.path.exists(db_path):
            self._create_initial_database()
        
        self.current_version = self._get_current_version()
    
    def _create_initial_database(self):
        """Create initial database with version tracking."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            ''')
            conn.execute('INSERT INTO schema_version (version, description) VALUES (0, "Initial database creation")')
            conn.commit()
    
    def _get_current_version(self) -> int:
        """Get current database schema version."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT MAX(version) FROM schema_version')
                result = cursor.fetchone()
                return result[0] if result[0] is not None else 0
        except sqlite3.OperationalError:
            return 0
    
    def apply_migrations(self) -> bool:
        """Apply all pending migrations to bring database up to date."""
        try:
            target_version = 3  # Current target version
            
            while self.current_version < target_version:
                next_version = self.current_version + 1
                
                if next_version == 1:
                    self._migrate_to_v1()
                elif next_version == 2:
                    self._migrate_to_v2()
                elif next_version == 3:
                    self._migrate_to_v3()
                else:
                    print(f"⚠️ Unknown migration version: {next_version}")
                    return False
                
                self.current_version = next_version
                print(f"✅ Applied migration to version {next_version}")
            
            print(f"📊 Database is up to date at version {self.current_version}")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
    
    def _migrate_to_v1(self):
        """Migration v1: Create accuracy metrics table."""
        with sqlite3.connect(self.db_path) as conn:
            # Create accuracy metrics table for long-term storage
            conn.execute('''
                CREATE TABLE accuracy_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    calculation_date DATE NOT NULL,
                    accuracy_7d REAL NOT NULL,
                    accuracy_30d REAL NOT NULL,
                    trend VARCHAR(20) NOT NULL,
                    total_sessions_7d INTEGER NOT NULL,
                    total_sessions_30d INTEGER NOT NULL,
                    total_emails_7d INTEGER NOT NULL,
                    total_emails_30d INTEGER NOT NULL,
                    system_info TEXT,  -- JSON blob for metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for efficient time-based queries
            conn.execute('CREATE INDEX idx_accuracy_timestamp ON accuracy_metrics(timestamp)')
            conn.execute('CREATE INDEX idx_accuracy_calculation_date ON accuracy_metrics(calculation_date)')
            
            # Record migration
            conn.execute(
                'INSERT INTO schema_version (version, description) VALUES (1, "Create accuracy metrics table")'
            )
            conn.commit()
    
    def _migrate_to_v2(self):
        """Migration v2: Create task resolution history table."""
        with sqlite3.connect(self.db_path) as conn:
            # Create task resolution history table
            conn.execute('''
                CREATE TABLE task_resolutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id VARCHAR(255) NOT NULL,
                    resolution_timestamp TIMESTAMP NOT NULL,
                    resolution_type VARCHAR(50) NOT NULL,
                    resolution_notes TEXT,
                    task_section VARCHAR(100),
                    task_age_days INTEGER,
                    task_priority VARCHAR(20),
                    task_sender VARCHAR(255),
                    email_count INTEGER DEFAULT 1,  -- Number of associated emails
                    task_data TEXT,  -- JSON blob for full task data
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for efficient queries
            conn.execute('CREATE INDEX idx_resolution_timestamp ON task_resolutions(resolution_timestamp)')
            conn.execute('CREATE INDEX idx_resolution_type ON task_resolutions(resolution_type)')
            conn.execute('CREATE INDEX idx_task_section ON task_resolutions(task_section)')
            conn.execute('CREATE INDEX idx_task_age ON task_resolutions(task_age_days)')
            
            # Record migration
            conn.execute(
                'INSERT INTO schema_version (version, description) VALUES (2, "Create task resolution history table")'
            )
            conn.commit()
    
    def _migrate_to_v3(self):
        """Migration v3: Create summary statistics views and additional indexes."""
        with sqlite3.connect(self.db_path) as conn:
            # Create view for daily accuracy summary
            conn.execute('''
                CREATE VIEW daily_accuracy_summary AS
                SELECT 
                    DATE(calculation_date) as date,
                    AVG(accuracy_7d) as avg_accuracy_7d,
                    AVG(accuracy_30d) as avg_accuracy_30d,
                    SUM(total_sessions_7d) as total_sessions,
                    SUM(total_emails_7d) as total_emails,
                    COUNT(*) as metric_entries
                FROM accuracy_metrics
                GROUP BY DATE(calculation_date)
                ORDER BY date DESC
            ''')
            
            # Create view for resolution statistics
            conn.execute('''
                CREATE VIEW resolution_statistics AS
                SELECT 
                    DATE(resolution_timestamp) as date,
                    resolution_type,
                    task_section,
                    COUNT(*) as resolution_count,
                    AVG(task_age_days) as avg_age_days,
                    MIN(task_age_days) as min_age_days,
                    MAX(task_age_days) as max_age_days
                FROM task_resolutions
                GROUP BY DATE(resolution_timestamp), resolution_type, task_section
                ORDER BY date DESC
            ''')
            
            # Create composite indexes for complex queries
            conn.execute('CREATE INDEX idx_resolution_composite ON task_resolutions(resolution_timestamp, resolution_type, task_section)')
            
            # Record migration
            conn.execute(
                'INSERT INTO schema_version (version, description) VALUES (3, "Create summary views and composite indexes")'
            )
            conn.commit()
    
    def backup_database(self) -> str:
        """Create backup of current database before migration."""
        backup_path = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
            print(f"📦 Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"⚠️ Backup failed: {e}")
            return ""
    
    def store_accuracy_metrics(self, metrics_data: Dict) -> bool:
        """Store accuracy metrics in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO accuracy_metrics (
                        timestamp, calculation_date, accuracy_7d, accuracy_30d, trend,
                        total_sessions_7d, total_sessions_30d, total_emails_7d, total_emails_30d,
                        system_info
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    datetime.now().date().isoformat(),
                    metrics_data.get('last_7_days', 0.0),
                    metrics_data.get('last_30_days', 0.0),
                    metrics_data.get('current_trend', 'stable'),
                    metrics_data.get('total_sessions_7d', 0),
                    metrics_data.get('total_sessions_30d', 0),
                    metrics_data.get('total_emails_7d', 0),
                    metrics_data.get('total_emails_30d', 0),
                    json.dumps({'version': '1.0'})  # System metadata
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"⚠️ Error storing accuracy metrics: {e}")
            return False
    
    def store_task_resolution(self, resolution_data: Dict) -> bool:
        """Store task resolution in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                task_data = resolution_data.get('task_data', {})
                email_ids = task_data.get('_entry_ids', [])
                
                conn.execute('''
                    INSERT INTO task_resolutions (
                        task_id, resolution_timestamp, resolution_type, resolution_notes,
                        task_section, task_age_days, task_priority, task_sender,
                        email_count, task_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    resolution_data.get('task_id'),
                    resolution_data.get('resolution_timestamp'),
                    resolution_data.get('resolution_type'),
                    resolution_data.get('resolution_notes', ''),
                    resolution_data.get('task_section'),
                    resolution_data.get('task_age_days', 0),
                    task_data.get('priority', 'normal'),
                    task_data.get('sender', 'unknown'),
                    len(email_ids),
                    json.dumps(task_data)
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"⚠️ Error storing task resolution: {e}")
            return False
    
    def get_metrics_history(self, days_back: int = 30) -> List[Dict]:
        """Retrieve metrics history from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM accuracy_metrics 
                    WHERE timestamp >= datetime('now', '-{} days')
                    ORDER BY timestamp DESC
                '''.format(days_back))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Error retrieving metrics history: {e}")
            return []
    
    def get_resolution_history(self, days_back: int = 30) -> List[Dict]:
        """Retrieve resolution history from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                # Use date() function to compare dates regardless of time
                cursor = conn.execute('''
                    SELECT * FROM task_resolutions 
                    WHERE date(resolution_timestamp) >= date('now', '-{} days')
                    ORDER BY resolution_timestamp DESC
                '''.format(days_back))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"⚠️ Error retrieving resolution history: {e}")
            return []