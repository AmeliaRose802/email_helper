"""Email synchronization service for database operations.

This service handles syncing emails between Outlook and the database,
managing conversation counts, and ensuring database schema integrity.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.database.connection import db_manager


# Configure module logger
logger = logging.getLogger(__name__)


class EmailSyncError(Exception):
    """Base exception for email sync errors."""
    pass


class DatabaseError(EmailSyncError):
    """Raised when database operations fail."""
    pass


class EmailSyncService:
    """Service for email-database synchronization operations."""
    
    def __init__(self):
        """Initialize the email sync service."""
        pass
    
    async def get_emails_from_database(
        self,
        limit: int = 50000,
        offset: int = 0,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get emails from database with optional filtering.
        
        Args:
            limit: Maximum number of emails to return
            offset: Number of emails to skip
            category: Filter by category (optional)
            search: Search term for subject/sender/body (optional)
            
        Returns:
            Dictionary containing emails list and total count
            
        Raises:
            DatabaseError: If database query fails
        """
        try:
            loop = asyncio.get_event_loop()
            
            def _get_emails_sync():
                with db_manager.get_connection() as conn:
                    # Build query with filters
                    query = "SELECT * FROM emails WHERE 1=1"
                    params = []
                    
                    if category:
                        query += " AND category = ?"
                        params.append(category)
                    
                    if search:
                        query += """ AND (
                            subject LIKE ? OR 
                            sender LIKE ? OR 
                            body LIKE ?
                        )"""
                        search_param = f"%{search}%"
                        params.extend([search_param, search_param, search_param])
                    
                    # Get total count
                    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
                    cursor = conn.execute(count_query, params)
                    total = cursor.fetchone()[0]
                    
                    # Get paginated results
                    query += " ORDER BY received_at DESC LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                    
                    cursor = conn.execute(query, params)
                    columns = [description[0] for description in cursor.description]
                    rows = cursor.fetchall()
                    
                    emails = [dict(zip(columns, row)) for row in rows]
                    
                    return {
                        'emails': emails,
                        'total': total
                    }
            
            return await loop.run_in_executor(None, _get_emails_sync)
            
        except Exception as e:
            logger.error(f"[EmailSync] Failed to get emails from database: {e}")
            raise DatabaseError(f"Database query failed: {str(e)}")
    
    async def sync_emails_to_database(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync emails from Outlook to SQLite database.
        
        Args:
            emails: List of email dictionaries to sync
            
        Returns:
            Dictionary with sync statistics
            
        Raises:
            DatabaseError: If database operations fail
        """
        if not emails:
            return {
                'success': True,
                'inserted': 0,
                'updated': 0,
                'total': 0
            }
        
        try:
            logger.info(f"[EmailSync] Starting sync of {len(emails)} emails to database")
            
            loop = asyncio.get_event_loop()
            
            def _sync_emails_sync():
                with db_manager.get_connection() as conn:
                    # Ensure schema exists
                    self._ensure_email_schema(conn)
                    
                    inserted = 0
                    updated = 0
                    
                    for email in emails:
                        email_id = email.get('id')
                        if not email_id:
                            continue
                        
                        # Check if email exists
                        cursor = conn.execute(
                            "SELECT id FROM emails WHERE id = ?",
                            (email_id,)
                        )
                        exists = cursor.fetchone()
                        
                        # Prepare email data
                        email_data = {
                            'id': email_id,
                            'subject': email.get('subject', ''),
                            'sender': email.get('sender', ''),
                            'received_at': email.get('received_at', ''),
                            'body': email.get('body', ''),
                            'conversation_id': email.get('conversation_id'),
                            'category': email.get('category'),
                            'ai_category': email.get('ai_category'),
                            'is_read': email.get('is_read', False),
                            'has_attachments': email.get('has_attachments', False),
                            'importance': email.get('importance', 'normal'),
                            'folder_name': email.get('folder_name', 'Inbox'),
                            'synced_at': datetime.now().isoformat()
                        }
                        
                        if exists:
                            # Update existing email
                            conn.execute("""
                                UPDATE emails 
                                SET subject = ?, sender = ?, received_at = ?, 
                                    body = ?, conversation_id = ?, category = ?,
                                    ai_category = ?, is_read = ?, has_attachments = ?,
                                    importance = ?, folder_name = ?, synced_at = ?
                                WHERE id = ?
                            """, (
                                email_data['subject'], email_data['sender'], 
                                email_data['received_at'], email_data['body'],
                                email_data['conversation_id'], email_data['category'],
                                email_data['ai_category'], email_data['is_read'],
                                email_data['has_attachments'], email_data['importance'],
                                email_data['folder_name'], email_data['synced_at'],
                                email_id
                            ))
                            updated += 1
                        else:
                            # Insert new email
                            conn.execute("""
                                INSERT INTO emails (
                                    id, subject, sender, received_at, body,
                                    conversation_id, category, ai_category,
                                    is_read, has_attachments, importance,
                                    folder_name, synced_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                email_data['id'], email_data['subject'],
                                email_data['sender'], email_data['received_at'],
                                email_data['body'], email_data['conversation_id'],
                                email_data['category'], email_data['ai_category'],
                                email_data['is_read'], email_data['has_attachments'],
                                email_data['importance'], email_data['folder_name'],
                                email_data['synced_at']
                            ))
                            inserted += 1
                    
                    conn.commit()
                    
                    return {
                        'success': True,
                        'inserted': inserted,
                        'updated': updated,
                        'total': len(emails)
                    }
            
            result = await loop.run_in_executor(None, _sync_emails_sync)
            logger.info(f"[EmailSync] Sync complete: {result['inserted']} inserted, "
                       f"{result['updated']} updated")
            return result
            
        except Exception as e:
            logger.error(f"[EmailSync] Failed to sync emails: {e}")
            raise DatabaseError(f"Email sync failed: {str(e)}")
    
    def _ensure_email_schema(self, conn) -> None:
        """Ensure emails table exists with proper schema.
        
        Args:
            conn: Database connection
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                subject TEXT,
                sender TEXT,
                received_at TEXT,
                body TEXT,
                conversation_id TEXT,
                category TEXT,
                ai_category TEXT,
                is_read INTEGER,
                has_attachments INTEGER,
                importance TEXT,
                folder_name TEXT,
                synced_at TEXT
            )
        """)
        conn.commit()
    
    async def calculate_conversation_counts(
        self, 
        conversation_ids: List[str]
    ) -> Dict[str, int]:
        """Calculate email counts per conversation.
        
        Args:
            conversation_ids: List of conversation IDs to count
            
        Returns:
            Dictionary mapping conversation IDs to email counts
            
        Raises:
            DatabaseError: If database query fails
        """
        if not conversation_ids:
            return {}
        
        try:
            loop = asyncio.get_event_loop()
            
            def _calculate_counts_sync():
                with db_manager.get_connection() as conn:
                    placeholders = ','.join('?' * len(conversation_ids))
                    query = f"""
                        SELECT conversation_id, COUNT(*) as count
                        FROM emails
                        WHERE conversation_id IN ({placeholders})
                        GROUP BY conversation_id
                    """
                    cursor = conn.execute(query, conversation_ids)
                    return {row[0]: row[1] for row in cursor.fetchall()}
            
            return await loop.run_in_executor(None, _calculate_counts_sync)
            
        except Exception as e:
            logger.error(f"[EmailSync] Failed to calculate conversation counts: {e}")
            raise DatabaseError(f"Conversation count calculation failed: {str(e)}")
