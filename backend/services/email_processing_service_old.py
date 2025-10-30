"""Email processing service for business logic operations.

This service coordinates between specialized email processing services,
providing a unified interface for the API layer. It delegates to:
- EmailSyncService: Database synchronization
- EmailClassificationService: AI classification and bulk operations
- EmailTaskExtractionService: Task creation from emails
- EmailAccuracyService: Accuracy tracking

This follows the Single Responsibility Principle by delegating to
focused services rather than handling everything in one large class.
"""

import logging
from typing import Dict, Any, List, Optional

from backend.services.ai_service import AIService
from backend.services.email_provider import EmailProvider
from backend.services.task_service import TaskService
from backend.services.email_sync_service import EmailSyncService
from backend.services.email_classification_service import EmailClassificationService
from backend.services.email_task_extraction_service import EmailTaskExtractionService
from backend.services.email_accuracy_service import EmailAccuracyService


# Configure module logger
logger = logging.getLogger(__name__)


# Re-export exceptions for backward compatibility
class EmailProcessingError(Exception):
    """Base exception for email processing errors."""
    pass


class EmailNotFoundError(EmailProcessingError):
    """Raised when an email is not found."""
    pass


class DatabaseError(EmailProcessingError):
    """Raised when database operations fail."""
    pass


class AIProcessingError(EmailProcessingError):
    """Raised when AI processing fails."""
    pass


class RateLimitError(EmailProcessingError):
    """Raised when rate limits are exceeded."""
    pass


class ContentFilterError(EmailProcessingError):
    """Raised when content is blocked by filters."""
    pass


class EmailProcessingService:
    """Coordinating service for email processing operations.
    
    This service delegates to specialized services for different concerns:
    - sync_service: Database operations
    - classification_service: AI classification
    - task_service: Task extraction
    - accuracy_service: Accuracy tracking
    """
    
    def __init__(
        self, 
        ai_service: AIService, 
        email_provider: EmailProvider, 
        task_service: TaskService
    ):
        """Initialize the email processing coordinator.
        
        Args:
            ai_service: AI service for classification and analysis
            email_provider: Email provider for Outlook operations
            task_service: Task service for task management
        """
        # Initialize specialized services
        self.sync_service = EmailSyncService()
        self.classification_service = EmailClassificationService(ai_service, email_provider)
        self.task_extraction_service = EmailTaskExtractionService(
            ai_service, email_provider, task_service
        )
        self.accuracy_service = EmailAccuracyService()
        
        # Keep references for backward compatibility
        self.ai_service = ai_service
        self.email_provider = email_provider
        self.task_service = task_service
        
        logger.info("[EmailProcessing] Initialized with specialized services")
    
    async def get_emails_from_database(
        self,
        limit: int = 50000,
        offset: int = 0,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get emails from database with AI classifications.
        
        Args:
            limit: Maximum number of emails to return
            offset: Number of emails to skip for pagination
            category: Filter by AI category
            search: Search query for subject/sender/body
            
        Returns:
            Dictionary with emails list, total count, and pagination info
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            loop = asyncio.get_event_loop()
            
            def _get_emails_sync():
                with db_manager.get_connection() as conn:
                    where_conditions = ["1=1"]
                    params = []
                    
                    if category:
                        where_conditions.append("ai_category = ?")
                        params.append(category)
                    
                    if search:
                        where_conditions.append(
                            "(subject LIKE ? OR sender LIKE ? OR body LIKE ?)"
                        )
                        search_term = f"%{search}%"
                        params.extend([search_term, search_term, search_term])
                    
                    where_clause = " AND ".join(where_conditions)
                    
                    count_query = f"SELECT COUNT(*) FROM emails WHERE {where_clause}"
                    cursor = conn.execute(count_query, params)
                    total = cursor.fetchone()[0]
                    
                    query = f"""
                        SELECT id, subject, sender, recipient, body, date,
                               ai_category, ai_confidence, ai_reasoning, one_line_summary,
                               conversation_id, category
                        FROM emails
                        WHERE {where_clause}
                        ORDER BY date DESC
                        LIMIT ? OFFSET ?
                    """
                    params.extend([limit, offset])
                    cursor = conn.execute(query, params)
                    
                    rows = cursor.fetchall()
                    emails = []
                    
                    for row in rows:
                        row_dict = dict(row)
                        email = {
                            'id': row_dict.get('id'),
                            'subject': row_dict.get('subject', ''),
                            'sender': row_dict.get('sender', ''),
                            'recipient': row_dict.get('recipient', ''),
                            'body': row_dict.get('body', ''),
                            'received_time': row_dict.get('date'),
                            'date': row_dict.get('date'),
                            'ai_category': row_dict.get('ai_category'),
                            'ai_confidence': row_dict.get('ai_confidence', 0.0),
                            'ai_reasoning': row_dict.get('ai_reasoning', ''),
                            'one_line_summary': row_dict.get('one_line_summary', ''),
                            'conversation_id': row_dict.get('conversation_id'),
                            'category': row_dict.get('category'),
                            'is_read': True,
                            'has_attachments': False,
                            'importance': 'Normal',
                            'categories': []
                        }
                        emails.append(email)
                    
                    return {
                        'emails': emails,
                        'total': total,
                        'offset': offset,
                        'limit': limit,
                        'has_more': (offset + len(emails)) < total
                    }
            
            result = await loop.run_in_executor(None, _get_emails_sync)
            logger.info(f"[DB] Retrieved {len(result['emails'])} emails from database (total: {result['total']})")
            return result
            
        except Exception as e:
            logger.error(f"[DB] Failed to get emails from database: {e}")
            raise DatabaseError(f"Database query failed: {str(e)}")
    
    async def sync_emails_to_database(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync classified emails to database.
        
        Args:
            emails: List of email dictionaries with AI classifications
            
        Returns:
            Dictionary with sync results and statistics
            
        Raises:
            DatabaseError: If database operations fail
        """
        if not emails:
            return {
                'success': True,
                'message': 'No emails to sync',
                'synced_count': 0,
                'failed_count': 0,
                'errors': []
            }
        
        try:
            loop = asyncio.get_event_loop()
            
            def _sync_emails_sync():
                synced_count = 0
                errors = []
                
                with db_manager.get_connection() as conn:
                    self._ensure_email_schema(conn)
                    
                    # PERFORMANCE: Batch check existing emails in ONE query instead of N queries
                    email_ids = [e.get('id') for e in emails if e.get('id')]
                    if not email_ids:
                        return {
                            'success': True,
                            'message': 'No valid email IDs to sync',
                            'synced_count': 0,
                            'failed_count': 0,
                            'errors': []
                        }
                    
                    placeholders = ','.join('?' * len(email_ids))
                    cursor = conn.execute(
                        f"SELECT id FROM emails WHERE id IN ({placeholders})",
                        email_ids
                    )
                    existing_ids = {row[0] for row in cursor.fetchall()}
                    
                    # PERFORMANCE: Batch INSERT and UPDATE operations
                    for email_data in emails:
                        try:
                            email_id = email_data.get('id')
                            if not email_id:
                                errors.append("Email missing ID field")
                                continue
                            
                            if email_id in existing_ids:
                                # UPDATE existing email
                                conn.execute(
                                    """
                                    UPDATE emails 
                                    SET ai_category = ?, 
                                        ai_confidence = ?, 
                                        ai_reasoning = ?,
                                        one_line_summary = ?,
                                        processed_at = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                    """,
                                    (
                                        email_data.get('ai_category'),
                                        email_data.get('ai_confidence', 0.0),
                                        email_data.get('ai_reasoning', ''),
                                        email_data.get('one_line_summary', ''),
                                        email_id
                                    )
                                )
                            else:
                                # INSERT new email
                                conn.execute(
                                    """
                                    INSERT INTO emails (
                                        id, subject, sender, recipient, content, body, 
                                        received_date, date, category, ai_category, 
                                        confidence, ai_confidence, ai_reasoning, 
                                        one_line_summary, conversation_id, user_id, processed_at
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                                    """,
                                    (
                                        email_id,
                                        email_data.get('subject', ''),
                                        email_data.get('sender', ''),
                                        email_data.get('recipient', ''),
                                        email_data.get('body', ''),
                                        email_data.get('body', ''),
                                        email_data.get('date'),
                                        email_data.get('date'),
                                        email_data.get('ai_category'),  # Legacy category field
                                        email_data.get('ai_category'),
                                        email_data.get('ai_confidence', 0.0),
                                        email_data.get('ai_confidence', 0.0),
                                        email_data.get('ai_reasoning', ''),
                                        email_data.get('one_line_summary', ''),
                                        email_data.get('conversation_id'),
                                        1  # Default user_id
                                    )
                                )
                            
                            synced_count += 1
                            
                        except Exception as e:
                            error_msg = f"Failed to sync email {email_data.get('id', 'unknown')}: {str(e)}"
                            logger.error(f"[Sync] {error_msg}")
                            errors.append(error_msg)
                    
                    conn.commit()
                    
                return {
                    'success': len(errors) == 0,
                    'message': f"Synced {synced_count} emails to database",
                    'synced_count': synced_count,
                    'failed_count': len(errors),
                    'errors': errors if errors else None
                }
            
            result = await loop.run_in_executor(None, _sync_emails_sync)
            logger.info(f"[Sync] Completed: {result['synced_count']} synced, {result['failed_count']} failed")
            return result
            
        except Exception as e:
            logger.error(f"[Sync] Failed to sync emails: {e}")
            raise DatabaseError(f"Email sync failed: {str(e)}")
    
    def _ensure_email_schema(self, conn) -> None:
        """Ensure emails table has all necessary columns."""
        try:
            columns_to_add = [
                ("ai_category", "TEXT"),
                ("ai_confidence", "REAL"),
                ("ai_reasoning", "TEXT"),
                ("one_line_summary", "TEXT"),
                ("body", "TEXT"),
                ("date", "TIMESTAMP"),
                ("conversation_id", "TEXT"),
                ("category", "TEXT")  # User-corrected category for accuracy tracking
            ]
            
            for column_name, column_type in columns_to_add:
                try:
                    conn.execute(f"ALTER TABLE emails ADD COLUMN {column_name} {column_type}")
                except Exception:
                    pass
            
            conn.commit()
        except Exception as e:
            logger.warning(f"[Schema] Could not ensure email schema: {e}")
    
    async def calculate_conversation_counts(
        self, 
        emails: List[Dict[str, Any]], 
        sample_size: int = 1000
    ) -> Dict[str, int]:
        """Calculate conversation counts for email threading.
        
        Args:
            emails: List of emails to analyze
            sample_size: Maximum number of emails to sample for accurate counts
            
        Returns:
            Dictionary mapping conversation_id to email count
        """
        try:
            loop = asyncio.get_event_loop()
            
            def _calculate_counts_sync():
                logger.info(f"[ConvCount] Calculating conversation counts for {len(emails)} emails")
                conversation_counts = {}
                
                # Use provided emails or fetch a sample if needed
                emails_to_analyze = emails[:sample_size] if len(emails) > sample_size else emails
                
                for email in emails_to_analyze:
                    conv_id = email.get('conversation_id')
                    if conv_id:
                        conversation_counts[conv_id] = conversation_counts.get(conv_id, 0) + 1
                
                multi_email_conversations = sum(1 for c in conversation_counts.values() if c > 1)
                logger.info(f"[ConvCount] Found {len(conversation_counts)} unique conversations, "
                          f"{multi_email_conversations} multi-email threads")
                
                return conversation_counts
            
            return await loop.run_in_executor(None, _calculate_counts_sync)
            
        except Exception as e:
            logger.error(f"[ConvCount] Failed to calculate conversation counts: {e}")
            return {}
    
    async def analyze_holistically(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform holistic analysis across multiple emails.
        
        This identifies expired items, superseded actions, and duplicates
        by analyzing emails together rather than individually.
        
        Args:
            emails: List of emails to analyze holistically
            
        Returns:
            Dictionary with analysis results including expired_items,
            superseded_actions, and duplicate_groups
            
        Raises:
            AIProcessingError: If AI analysis fails
        """
        if not emails:
            return {
                'expired_items': [],
                'superseded_actions': [],
                'duplicate_groups': [],
                'truly_relevant_actions': []
            }
        
        try:
            logger.info(f"[Holistic] Starting holistic analysis for {len(emails)} emails")
            
            # Rate limiting before AI call
            await self.rate_limiter.holistic_analysis_delay()
            
            result = await self.ai_service.analyze_holistically(emails)
            
            # Log analysis results
            expired_count = len(result.get('expired_items', []))
            superseded_count = len(result.get('superseded_actions', []))
            duplicate_groups = len(result.get('duplicate_groups', []))
            
            logger.info(f"[Holistic] Analysis complete: {expired_count} expired, "
                       f"{superseded_count} superseded, {duplicate_groups} duplicate groups")
            
            return result
            
        except Exception as e:
            error_msg = str(e).lower()
            if 'content_filter' in error_msg or 'responsibleaipolicyviolation' in error_msg:
                logger.warning(f"[Holistic] [FILTER] Content filter blocked holistic analysis: {e}")
                raise ContentFilterError("Content blocked by AI content policy")
            elif 'rate' in error_msg or 'quota' in error_msg or '429' in error_msg:
                logger.warning(f"[Holistic] [RATE] Rate limit hit during holistic analysis: {e}")
                raise RateLimitError("AI service rate limit exceeded")
            else:
                logger.error(f"[Holistic] AI processing failed: {e}")
                raise AIProcessingError(f"Holistic analysis failed: {str(e)}")
    
    async def extract_tasks_from_emails(
        self, 
        email_ids: List[str], 
        user_id: int = 1
    ) -> Dict[str, Any]:
        """Extract tasks and summaries from emails with rate limiting.
        
        This processes emails based on their AI category and creates appropriate
        tasks, summaries, or assessments with proper error handling and rate limiting.
        
        Args:
            email_ids: List of email IDs to process
            user_id: User ID for task ownership
            
        Returns:
            Dictionary with processing results and statistics
            
        Raises:
            EmailProcessingError: If processing fails
        """
        if not email_ids:
            return {
                'status': 'completed',
                'tasks_created': 0,
                'summaries_created': 0,
                'errors': [],
                'processed_count': 0
            }
        
        try:
            logger.info(f"[TaskExtract] Starting task extraction for {len(email_ids)} emails")
            
            tasks_created = 0
            summaries_created = 0
            errors = []
            processed_count = 0
            
            # First, perform holistic analysis to detect reclassifications
            # This also fetches and CACHES email bodies in memory for reuse
            holistic_reclassifications, email_body_cache = await self._perform_holistic_reclassification(email_ids)
            
            # Process each email individually
            for email_id in email_ids:
                try:
                    # Get email from database
                    email = await self._get_email_from_database(email_id)
                    if not email:
                        logger.warning(f"[TaskExtract] Email {email_id[:30]}... not found in database")
                        continue
                    
                    # Apply holistic reclassification if available
                    ai_category = holistic_reclassifications.get(email_id, email.get('ai_category', ''))
                    if ai_category != email.get('ai_category'):
                        logger.info(f"[TaskExtract] [Holistic] Reclassified {email_id[:30]}... to: {ai_category}")
                        await self._update_email_category(email_id, ai_category)
                        email['ai_category'] = ai_category
                    
                    ai_category = ai_category.lower() if ai_category else ''
                    
                    # Classify if needed (pass cache to avoid redundant Outlook fetches)
                    if not ai_category:
                        ai_category = await self._classify_email_if_needed(email, email_body_cache)
                    
                    # Process based on category (pass cache to reuse bodies)
                    result = await self._process_email_by_category(email, ai_category, user_id, email_body_cache)
                    
                    if result.get('task_created'):
                        tasks_created += 1
                    if result.get('summary_created'):
                        summaries_created += 1
                    if result.get('error'):
                        errors.append(result['error'])
                    
                    processed_count += 1
                    
                except Exception as e:
                    error_msg = self._diagnose_processing_error(e, email_id)
                    errors.append(error_msg)
                    logger.error(f"[TaskExtract] {error_msg}")
                    continue
            
            result = {
                'status': 'completed',
                'tasks_created': tasks_created,
                'summaries_created': summaries_created,
                'errors': errors,
                'processed_count': processed_count,
                'total_requested': len(email_ids)
            }
            
            logger.info(f"[TaskExtract] Completed: {tasks_created} tasks, "
                       f"{summaries_created} summaries, {len(errors)} errors")
            
            return result
            
        except Exception as e:
            logger.error(f"[TaskExtract] Critical failure: {e}", exc_info=True)
            raise EmailProcessingError(f"Task extraction failed: {str(e)}")
    
    async def _perform_holistic_reclassification(self, email_ids: List[str]) -> tuple[Dict[str, str], Dict[str, str]]:
        """Perform holistic analysis and return reclassifications + cached email bodies.
        
        Returns:
            Tuple of (reclassifications_dict, email_body_cache_dict)
        """
        try:
            # Get emails for holistic analysis
            emails_for_analysis = []
            email_body_cache = {}  # Cache bodies in memory for reuse during task extraction
            
            loop = asyncio.get_event_loop()
            
            def _get_emails_sync():
                with db_manager.get_connection() as conn:
                    placeholders = ','.join('?' * len(email_ids))
                    cursor = conn.execute(
                        f"SELECT id, subject, sender, ai_category, conversation_id FROM emails WHERE id IN ({placeholders})",
                        email_ids
                    )
                    return [dict(row) for row in cursor.fetchall()]
            
            emails_for_analysis = await loop.run_in_executor(None, _get_emails_sync)
            
            # Fetch email bodies from Outlook on-demand for analysis AND cache them
            if emails_for_analysis:
                logger.info(f"[Holistic] Fetching {len(emails_for_analysis)} email bodies from Outlook (caching for reuse)...")
                
                # CRITICAL: Batch fetch all bodies in a single executor call to ensure COM thread safety
                def _fetch_all_bodies():
                    """Fetch all email bodies in one COM thread context."""
                    bodies = {}
                    for email in emails_for_analysis:
                        email_id = email.get('id')
                        if email_id:
                            try:
                                # Use sync method directly to stay on same thread
                                body = self.email_provider.adapter.get_email_body(email_id)
                                bodies[email_id] = body or ''
                            except Exception as e:
                                logger.warning(f"[Holistic] Could not fetch body for {email_id[:30]}...: {e}")
                                bodies[email_id] = ''
                    return bodies
                
                # Fetch all bodies in single executor call (one COM thread context)
                email_body_cache = await loop.run_in_executor(None, _fetch_all_bodies)
                
                # Update email dicts with cached bodies
                for email in emails_for_analysis:
                    email_id = email.get('id')
                    if email_id and email_id in email_body_cache:
                        email['body'] = email_body_cache[email_id]
                
                logger.info(f"[Holistic] Analyzing {len(emails_for_analysis)} emails for reclassification")
                holistic_result = await self.analyze_holistically(emails_for_analysis)
                
                reclassifications = {}
                
                # Process expired items - reclassify to spam_to_delete
                for expired in holistic_result.get('expired_items', []):
                    email_id = expired.get('email_id')
                    reason = expired.get('reason', 'Past deadline or event occurred')
                    if email_id:
                        reclassifications[email_id] = 'spam_to_delete'
                        logger.info(f"[Holistic] [CLEAN] Marking expired: {email_id[:30]}... - {reason}")
                
                # Process superseded actions - reclassify to work_relevant
                for superseded in holistic_result.get('superseded_actions', []):
                    original_id = superseded.get('original_email_id')
                    superseded_by = superseded.get('superseded_by_email_id')
                    reason = superseded.get('reason', 'Superseded by newer email')
                    if original_id:
                        reclassifications[original_id] = 'work_relevant'
                        logger.info(f"[Holistic] [SUPERSEDE] Marking superseded: {original_id[:30]}... "
                                  f"by {superseded_by[:30] if superseded_by else 'newer'}... - {reason}")
                
                # Process duplicates - archive all but canonical
                for dup_group in holistic_result.get('duplicate_groups', []):
                    keep_id = dup_group.get('keep_email_id')
                    archive_ids = dup_group.get('archive_email_ids', [])
                    topic = dup_group.get('topic', 'Duplicate')
                    for archive_id in archive_ids:
                        if archive_id and archive_id != keep_id:
                            reclassifications[archive_id] = 'spam_to_delete'
                            logger.info(f"[Holistic] [DUP] Archiving duplicate: {archive_id[:30]}... "
                                      f"(keeping {keep_id[:30] if keep_id else 'canonical'}...) - {topic}")
                
                logger.info(f"[Holistic] Reclassification complete: {len(reclassifications)} emails, {len(email_body_cache)} bodies cached")
                return reclassifications, email_body_cache
                
        except Exception as e:
            logger.warning(f"[Holistic] Reclassification failed (continuing): {e}")
        
        return {}, {}
    
    async def _get_email_from_database(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get email metadata from database by ID."""
        loop = asyncio.get_event_loop()
        
        def _get_email_sync():
            with db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, subject, sender, ai_category, conversation_id FROM emails WHERE id = ?",
                    (email_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        
        return await loop.run_in_executor(None, _get_email_sync)
    
    async def _update_email_category(self, email_id: str, category: str) -> None:
        """Update email category in database."""
        loop = asyncio.get_event_loop()
        
        def _update_sync():
            with db_manager.get_connection() as conn:
                conn.execute(
                    "UPDATE emails SET ai_category = ? WHERE id = ?",
                    (category, email_id)
                )
                conn.commit()
        
        await loop.run_in_executor(None, _update_sync)
    
    async def _classify_email_if_needed(self, email: Dict[str, Any], body_cache: Dict[str, str] = None) -> str:
        """Classify email if no category exists."""
        try:
            await self.rate_limiter.ai_request_delay()
            
            email_id = email.get('id')
            
            # Check cache first, then fetch from Outlook if needed
            body = email.get('body', '')
            if not body and body_cache:
                body = body_cache.get(email_id, '')
            if not body:
                # Fetch in executor to ensure proper COM threading
                loop = asyncio.get_event_loop()
                try:
                    body = await loop.run_in_executor(
                        None, 
                        self.email_provider.adapter.get_email_body,
                        email_id
                    )
                    body = body or ''
                except Exception as e:
                    logger.warning(f"[Classify] Could not fetch body for {email_id[:30]}...: {e}")
                    body = ''
            
            email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{body}"
            classification_result = await self.ai_service.classify_email(email_content=email_text)
            return classification_result.get('category', 'work_relevant').lower()
            
        except Exception as e:
            logger.error(f"[TaskExtract] Failed to classify email {email.get('id', '')[:30]}...: {e}")
            return 'work_relevant'  # Fallback category
    
    async def _process_email_by_category(
        self, 
        email: Dict[str, Any], 
        ai_category: str, 
        user_id: int,
        body_cache: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Process email based on its AI category."""
        if ai_category in self.actionable_categories:
            return await self._create_action_task(email, ai_category, user_id, body_cache)
        elif ai_category in self.job_categories:
            return await self._create_job_task(email, user_id, body_cache)
        elif ai_category in self.event_categories:
            return await self._create_event_task(email, user_id, body_cache)
        elif ai_category in self.summary_categories:
            return await self._create_summary_task(email, ai_category, user_id, body_cache)
        
        logger.info(f"[TaskExtract] [SKIP] No processing needed for category '{ai_category}': {email.get('id', '')[:30]}...")
        return {'task_created': False, 'summary_created': False}
    
    async def _create_action_task(
        self, 
        email: Dict[str, Any], 
        ai_category: str, 
        user_id: int,
        body_cache: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Create task from actionable email."""
        try:
            email_id = email.get('id')
            
            # Check cache first, then fetch from Outlook if needed
            body = email.get('body', '')
            if not body and body_cache:
                body = body_cache.get(email_id, '')
            if not body:
                # Fetch in executor to ensure proper COM threading
                loop = asyncio.get_event_loop()
                try:
                    body = await loop.run_in_executor(
                        None,
                        self.email_provider.adapter.get_email_body,
                        email_id
                    )
                    body = body or ''
                except Exception as e:
                    logger.warning(f"[ActionTask] Could not fetch body for {email_id[:30]}...: {e}")
                    body = ''
            
            email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{body}"
            action_result = await self.ai_service.extract_action_items(email_text)
            
            # Check for fallback responses
            action_text = action_result.get('action_required', '') if action_result else ''
            if self._is_fallback_response(action_text, action_result):
                logger.info(f"[TaskExtract] [SKIP] Fallback response for {email.get('id', '')[:30]}...")
                return {'task_created': False, 'summary_created': False}
            
            if action_result and action_text:
                # Determine priority
                priority = 'high' if ai_category == 'required_personal_action' else 'medium'
                if 'urgent' in email.get('subject', '').lower():
                    priority = 'high'
                
                # Parse due date
                due_date = self._parse_due_date(action_result.get('due_date'))
                
                description_parts = [f"Action: {action_result.get('action_required', '')}"]
                if action_result.get('explanation'):
                    description_parts.append(f"\nDetails: {action_result['explanation']}")
                if action_result.get('relevance'):
                    description_parts.append(f"\nRelevance: {action_result['relevance']}")
                if action_result.get('links'):
                    description_parts.append(f"\nLinks: {', '.join(action_result['links'])}")
                description_parts.append(f"\nSender: {email.get('sender', '')}")
                
                task_data = TaskCreate(
                    title=email.get('subject', 'Action Required')[:200],
                    description='\n'.join(description_parts),
                    status=TaskStatus.TODO,
                    priority=TaskPriority(priority),
                    category=ai_category,
                    email_id=email.get('id'),
                    due_date=due_date,
                    tags=[ai_category, 'action_item'],
                    metadata={
                        'sender': email.get('sender', ''), 
                        'links': action_result.get('links', [])
                    }
                )
                
                created_task = await self.task_service.create_task(task_data, user_id)
                logger.info(f"[TaskExtract] [OK] Created action task #{created_task.id} for {email.get('id', '')[:20]}...")
                return {'task_created': True, 'summary_created': False}
                
        except Exception as e:
            return {'task_created': False, 'summary_created': False, 'error': str(e)}
        
        return {'task_created': False, 'summary_created': False}
    
    async def _create_job_task(self, email: Dict[str, Any], user_id: int, body_cache: Dict[str, str] = None) -> Dict[str, Any]:
        """Create task from job listing email."""
        try:
            email_id = email.get('id')
            
            # Check cache first, then fetch from Outlook if needed
            body = email.get('body', '')
            if not body and body_cache:
                body = body_cache.get(email_id, '')
            if not body:
                # Fetch in executor to ensure proper COM threading
                loop = asyncio.get_event_loop()
                try:
                    body = await loop.run_in_executor(
                        None,
                        self.email_provider.adapter.get_email_body,
                        email_id
                    )
                    body = body or ''
                except Exception as e:
                    logger.warning(f"[JobTask] Could not fetch body for {email_id[:30]}...: {e}")
                    body = ''
            
            email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{body}"
            action_result = await self.ai_service.extract_action_items(email_text)
            
            action_text = action_result.get('action_required', '') if action_result else ''
            if self._is_fallback_response(action_text, action_result):
                logger.info(f"[TaskExtract] [SKIP] Job listing fallback for {email.get('id', '')[:30]}...")
                return {'task_created': False, 'summary_created': False}
            
            description_parts = [f"Job Listing: {email.get('subject', '')}"]
            if action_result.get('explanation'):
                description_parts.append(f"\nQualification Match: {action_result['explanation']}")
            if action_result.get('relevance'):
                description_parts.append(f"\nRelevance: {action_result['relevance']}")
            if action_result.get('links'):
                description_parts.append(f"\nApply: {', '.join(action_result['links'])}")
            description_parts.append(f"\nFrom: {email.get('sender', '')}")
            
            due_date = self._parse_due_date(action_result.get('due_date'))
            
            task_data = TaskCreate(
                title=f"[JOB] {email.get('subject', 'Job Listing')[:190]}",
                description='\n'.join(description_parts),
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                category='job_listing',
                email_id=email.get('id'),
                due_date=due_date,
                tags=['job_listing', 'opportunity'],
                metadata={
                    'sender': email.get('sender', ''), 
                    'links': action_result.get('links', [])
                }
            )
            
            created_task = await self.task_service.create_task(task_data, user_id)
            logger.info(f"[TaskExtract] [OK] Created job task #{created_task.id} for {email.get('id', '')[:20]}...")
            return {'task_created': True, 'summary_created': False}
            
        except Exception as e:
            return {'task_created': False, 'summary_created': False, 'error': str(e)}
    
    async def _create_event_task(self, email: Dict[str, Any], user_id: int, body_cache: Dict[str, str] = None) -> Dict[str, Any]:
        """Create task from optional event email."""
        try:
            email_id = email.get('id')
            
            # Check cache first, then fetch from Outlook if needed
            body = email.get('body', '')
            if not body and body_cache:
                body = body_cache.get(email_id, '')
            if not body:
                # Fetch in executor to ensure proper COM threading
                loop = asyncio.get_event_loop()
                try:
                    body = await loop.run_in_executor(
                        None,
                        self.email_provider.adapter.get_email_body,
                        email_id
                    )
                    body = body or ''
                except Exception as e:
                    logger.warning(f"[EventTask] Could not fetch body for {email_id[:30]}...: {e}")
                    body = ''
            
            email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{body}"
            action_result = await self.ai_service.extract_action_items(email_text)
            
            action_text = action_result.get('action_required', '') if action_result else ''
            if self._is_fallback_response(action_text, action_result):
                logger.info(f"[TaskExtract] [SKIP] Event fallback for {email.get('id', '')[:30]}...")
                return {'task_created': False, 'summary_created': False}
            
            description_parts = [f"Optional Event: {email.get('subject', '')}"]
            if action_result.get('relevance'):
                description_parts.append(f"\nRelevance: {action_result['relevance']}")
            if action_result.get('explanation'):
                description_parts.append(f"\nDetails: {action_result['explanation']}")
            if action_result.get('links'):
                description_parts.append(f"\nRegister: {', '.join(action_result['links'])}")
            description_parts.append(f"\nFrom: {email.get('sender', '')}")
            
            event_date = self._parse_due_date(action_result.get('due_date'))
            
            task_data = TaskCreate(
                title=f"[EVENT] {email.get('subject', 'Optional Event')[:185]}",
                description='\n'.join(description_parts),
                status=TaskStatus.TODO,
                priority=TaskPriority.LOW,
                category='optional_event',
                email_id=email.get('id'),
                due_date=event_date,
                tags=['optional_event', 'networking'],
                metadata={
                    'sender': email.get('sender', ''), 
                    'links': action_result.get('links', [])
                }
            )
            
            created_task = await self.task_service.create_task(task_data, user_id)
            logger.info(f"[TaskExtract] [OK] Created event task #{created_task.id} for {email.get('id', '')[:20]}...")
            return {'task_created': False, 'summary_created': True}
            
        except Exception as e:
            return {'task_created': False, 'summary_created': False, 'error': str(e)}
    
    async def _create_summary_task(
        self, 
        email: Dict[str, Any], 
        ai_category: str, 
        user_id: int,
        body_cache: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Create summary task from FYI or newsletter email."""
        try:
            email_id = email.get('id')
            
            # Check cache first, then fetch from Outlook if needed
            body = email.get('body', '')
            if not body and body_cache:
                body = body_cache.get(email_id, '')
            if not body:
                # Fetch in executor to ensure proper COM threading
                loop = asyncio.get_event_loop()
                try:
                    body = await loop.run_in_executor(
                        None,
                        self.email_provider.adapter.get_email_body,
                        email_id
                    )
                    body = body or ''
                except Exception as e:
                    logger.warning(f"[SummaryTask] Could not fetch body for {email_id[:30]}...: {e}")
                    body = ''
            
            email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{body}"
            
            summary_type = 'detailed' if ai_category == 'newsletter' else 'fyi'
            summary_result = await self.ai_service.generate_summary(email_text, summary_type=summary_type)
            summary_text = summary_result.get('summary', f'{ai_category.title()} content')
            
            if ai_category == 'newsletter':
                description_parts = [f"[NEWS] Newsletter Summary"]
                description_parts.append(f"\n{summary_text}")
                if summary_result.get('key_points'):
                    description_parts.append(f"\n\nKey Points:")
                    for point in summary_result['key_points']:
                        description_parts.append(f"• {point}")
                description_parts.append(f"\n\nFrom: {email.get('sender', '')}")
                
                task_data = TaskCreate(
                    title=f"[NEWS] {email.get('subject', 'Newsletter')[:190]}",
                    description='\n'.join(description_parts),
                    status=TaskStatus.TODO,
                    priority=TaskPriority.LOW,
                    category='newsletter',
                    email_id=email.get('id'),
                    tags=['newsletter', 'reading'],
                    metadata={
                        'sender': email.get('sender', ''), 
                        'key_points': summary_result.get('key_points', [])
                    }
                )
            else:  # fyi
                description_parts = [f"[FYI] {summary_text}"]
                description_parts.append(f"\nFrom: {email.get('sender', '')}")
                
                task_data = TaskCreate(
                    title=f"[FYI] {email.get('subject', 'FYI')[:195]}",
                    description='\n'.join(description_parts),
                    status=TaskStatus.TODO,
                    priority=TaskPriority.LOW,
                    category='fyi',
                    email_id=email.get('id'),
                    tags=['fyi', 'information'],
                    metadata={'sender': email.get('sender', '')}
                )
            
            created_task = await self.task_service.create_task(task_data, user_id)
            logger.info(f"[TaskExtract] [OK] Created {ai_category} summary #{created_task.id} for {email.get('id', '')[:20]}...")
            return {'task_created': False, 'summary_created': True}
            
        except Exception as e:
            return {'task_created': False, 'summary_created': False, 'error': str(e)}
    
    def _is_fallback_response(self, action_text: str, action_result: Dict[str, Any]) -> bool:
        """Check if response is a fallback/error response."""
        if not action_text:
            return True
        
        fallback_phrases = [
            'unable to extract action items',
            'review email content',
            'unable to parse structured response',
            'ai processing unavailable',
            'content filter blocked'
        ]
        
        return (
            any(phrase in action_text.lower() for phrase in fallback_phrases) or
            'error' in action_result
        )
    
    def _parse_due_date(self, due_date_str: Optional[str]) -> Optional[datetime]:
        """Parse due date string to datetime object."""
        if not due_date_str or due_date_str in ['No specific deadline', '', 'Unknown']:
            return None
        
        try:
            # Try common datetime formats
            import re
            from datetime import datetime
            
            # Remove extra whitespace and common text
            clean_str = due_date_str.strip()
            
            # Common patterns
            patterns = [
                r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
                r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
                r'(\d{1,2}-\d{1,2}-\d{4})',  # MM-DD-YYYY
            ]
            
            for pattern in patterns:
                match = re.search(pattern, clean_str)
                if match:
                    date_str = match.group(1)
                    if '/' in date_str:
                        return datetime.strptime(date_str, '%m/%d/%Y')
                    elif '-' in date_str and len(date_str) == 10:
                        return datetime.strptime(date_str, '%Y-%m-%d')
                    elif '-' in date_str:
                        return datetime.strptime(date_str, '%m-%d-%Y')
            
            return None
        except Exception:
            return None
    
    def _diagnose_processing_error(self, error: Exception, email_id: str) -> str:
        """Diagnose and categorize processing errors."""
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        if 'content_filter' in error_msg or 'responsibleaipolicyviolation' in error_msg:
            return f"[FILTER] Content filter blocked processing for {email_id[:30]}..."
        elif 'rate' in error_msg or 'quota' in error_msg or '429' in error_msg:
            return f"[RATE] Rate limit hit processing {email_id[:30]}..."
        elif 'timeout' in error_msg or 'connection' in error_msg:
            return f"[CONN] Network error processing {email_id[:30]}..."
        elif 'badrequest' in error_msg or 'invalid' in error_msg:
            return f"[BADREQ] Invalid data in {email_id[:30]}..."
        else:
            return f"[ERROR] Unexpected error ({error_type}) processing {email_id[:30]}...: {error}"
    
    async def get_accuracy_statistics(self) -> Dict[str, Any]:
        """Calculate AI classification accuracy statistics.
        
        Compares ai_category (original AI prediction) with category (user-corrected)
        to determine accuracy metrics.
        
        Returns:
            Dictionary with overall and per-category accuracy statistics
            
        Raises:
            DatabaseError: If database query fails
        """
        try:
            loop = asyncio.get_event_loop()
            
            def _calculate_accuracy_sync():
                with db_manager.get_connection() as conn:
                    # Get all emails with both AI and user categories
                    cursor = conn.execute("""
                        SELECT ai_category, category
                        FROM emails
                        WHERE ai_category IS NOT NULL 
                          AND ai_category != ''
                          AND category IS NOT NULL
                          AND category != ''
                    """)
                    
                    rows = cursor.fetchall()
                
                if not rows:
                    return {
                        "overall_accuracy": 0,
                        "total_emails": 0,
                        "total_correct": 0,
                        "categories": []
                    }
                
                # Calculate per-category statistics
                category_stats = defaultdict(lambda: {
                    'total': 0,
                    'correct': 0,
                    'true_positives': 0,
                    'false_positives': 0,
                    'false_negatives': 0
                })
                
                total_emails = len(rows)
                total_correct = 0
                
                # First pass: count totals and correct classifications
                for ai_cat, user_cat in rows:
                    ai_cat = ai_cat.lower()
                    user_cat = user_cat.lower()
                    
                    category_stats[ai_cat]['total'] += 1
                    
                    if ai_cat == user_cat:
                        category_stats[ai_cat]['correct'] += 1
                        category_stats[ai_cat]['true_positives'] += 1
                        total_correct += 1
                
                # Second pass: calculate false positives and false negatives
                for ai_cat, user_cat in rows:
                    ai_cat = ai_cat.lower()
                    user_cat = user_cat.lower()
                    
                    if ai_cat != user_cat:
                        category_stats[ai_cat]['false_positives'] += 1
                        category_stats[user_cat]['false_negatives'] += 1
                
                # Calculate metrics for each category
                categories = []
                for cat, stats in category_stats.items():
                    total = stats['total']
                    correct = stats['correct']
                    tp = stats['true_positives']
                    fp = stats['false_positives']
                    fn = stats['false_negatives']
                    
                    accuracy = (correct / total * 100) if total > 0 else 0
                    precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0
                    recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0
                    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
                    
                    # Format category name nicely
                    cat_display = cat.replace('_', ' ').title()
                    
                    categories.append({
                        'category': cat_display,
                        'total': total,
                        'correct': correct,
                        'accuracy': round(accuracy, 1),
                        'precision': round(precision, 1),
                        'recall': round(recall, 1),
                        'f1': round(f1, 1),
                        'truePositives': tp,
                        'falsePositives': fp,
                        'falseNegatives': fn
                    })
                
                # Sort by total (most common categories first)
                categories.sort(key=lambda x: x['total'], reverse=True)
                
                overall_accuracy = (total_correct / total_emails * 100) if total_emails > 0 else 0
                
                return {
                    "overall_accuracy": round(overall_accuracy, 1),
                    "total_emails": total_emails,
                    "total_correct": total_correct,
                    "categories": categories
                }
            
            result = await loop.run_in_executor(None, _calculate_accuracy_sync)
            logger.info(f"[AccuracyStats] Calculated for {result['total_emails']} emails, "
                       f"overall accuracy: {result['overall_accuracy']}%")
            return result
            
        except Exception as e:
            logger.error(f"[AccuracyStats] Failed to calculate accuracy: {e}")
            raise DatabaseError(f"Accuracy calculation failed: {str(e)}")
    
    def get_category_mappings(self) -> List[Dict[str, Any]]:
        """Get category to folder mappings.
        
        Returns:
            List of category mappings with folder names and inbox status
        """
        mappings = []
        
        for category, folder_name in self.inbox_categories.items():
            mappings.append({
                'category': category,
                'folder_name': folder_name,
                'stays_in_inbox': True
            })
        
        for category, folder_name in self.non_inbox_categories.items():
            mappings.append({
                'category': category,
                'folder_name': folder_name,
                'stays_in_inbox': False
            })
        
        logger.info(f"[CategoryMap] Returned {len(mappings)} category mappings")
        return mappings
    
    async def bulk_apply_classifications(
        self, 
        email_ids: List[str], 
        apply_to_outlook: bool = True
    ) -> Dict[str, Any]:
        """Bulk apply AI classifications to Outlook folders.
        
        Args:
            email_ids: List of email IDs to process
            apply_to_outlook: Whether to move emails to Outlook folders
            
        Returns:
            Dictionary with processing results and statistics
            
        Raises:
            EmailProcessingError: If bulk processing fails
        """
        if not email_ids:
            return {
                'success': True,
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'errors': []
            }
        
        try:
            logger.info(f"[BulkApply] Starting bulk apply for {len(email_ids)} emails")
            
            successful = 0
            failed = 0
            errors = []
            
            # CRITICAL: COM operations must be serialized - no concurrent access
            # Use sync loop to avoid threading issues with COM objects
            loop = asyncio.get_event_loop()
            
            for email_id in email_ids:
                try:
                    # Get email data in executor to ensure proper COM threading
                    def _get_email():
                        return self.email_provider.get_email_by_id(email_id)
                    
                    email = await loop.run_in_executor(None, _get_email)
                    if not email:
                        logger.warning(f"[BulkApply] Email {email_id[:20]}... not found, skipping")
                        continue
                    
                    # Get or determine AI category
                    ai_category = email.get('ai_category')
                    
                    if not ai_category:
                        # Classify the email first
                        email_text = f"Subject: {email.get('subject', '')}\nFrom: {email.get('sender', '')}\n\n{email.get('body', '')}"
                        
                        try:
                            classification_result = await self.ai_service.classify_email(
                                email_content=email_text
                            )
                            ai_category = classification_result.get('category', 'work_relevant')
                        except Exception as classify_error:
                            errors.append(f"Failed to classify email {email_id}: {str(classify_error)}")
                            ai_category = 'work_relevant'  # Fallback category
                    
                    # Apply to Outlook if requested
                    if apply_to_outlook:
                        folder_name = self.all_categories.get(ai_category.lower())
                        
                        logger.info(f"[BulkApply] Email {email_id[:20]}... -> Category: '{ai_category}' -> Folder: '{folder_name}'")
                        
                        if folder_name:
                            # Execute COM move operation in executor for thread safety
                            def _move_email():
                                return self.email_provider.move_email(email_id, folder_name)
                            
                            move_success = await loop.run_in_executor(None, _move_email)
                            
                            if move_success:
                                successful += 1
                                logger.info(f"[BulkApply] [OK] Successfully moved to {folder_name}")
                            else:
                                error_msg = f"Failed to move email {email_id} to {folder_name}"
                                errors.append(error_msg)
                                logger.error(f"[BulkApply] [FAIL] {error_msg}")
                                failed += 1
                        else:
                            # Category doesn't require folder move (stays in inbox)
                            logger.info(f"[BulkApply] Category '{ai_category}' has no folder mapping, skipping move")
                            successful += 1
                    else:
                        # Just classification without moving
                        successful += 1
                        
                except Exception as e:
                    errors.append(f"Error processing email {email_id}: {str(e)}")
                    failed += 1
            
            result = {
                'success': failed == 0,
                'processed': len(email_ids),
                'successful': successful,
                'failed': failed,
                'errors': errors
            }
            
            logger.info(f"[BulkApply] Completed: {successful} successful, {failed} failed")
            return result
            
        except Exception as e:
            logger.error(f"[BulkApply] Critical failure: {e}")
            raise EmailProcessingError(f"Bulk apply failed: {str(e)}")
    
    async def update_email_classification(
        self, 
        email_id: str, 
        category: str, 
        apply_to_outlook: bool = True
    ) -> Dict[str, Any]:
        """Update email classification and optionally apply to Outlook.
        
        Args:
            email_id: Email ID to update
            category: New category to assign
            apply_to_outlook: Whether to move email to appropriate folder
            
        Returns:
            Dictionary with operation results
            
        Raises:
            EmailProcessingError: If update fails
        """
        try:
            category_lower = category.lower()
            folder_name = self.all_categories.get(category_lower, 'Work Relevant')
            
            # Store user correction in database for accuracy tracking
            loop = asyncio.get_event_loop()
            
            def _update_category_sync():
                with db_manager.get_connection() as conn:
                    conn.execute("""
                        UPDATE emails 
                        SET category = ? 
                        WHERE id = ?
                    """, (category_lower, email_id))
                    conn.commit()
            
            await loop.run_in_executor(None, _update_category_sync)
            
            if apply_to_outlook and folder_name:
                # Move email to the category folder
                success = self.email_provider.move_email(email_id, folder_name)
                
                if success:
                    message = f"Email classified as '{category}' and moved to '{folder_name}'"
                    logger.info(f"[Classification] [OK] {message} for {email_id[:20]}...")
                else:
                    message = f"Failed to move email to '{folder_name}'"
                    logger.error(f"[Classification] [FAIL] {message} for {email_id[:20]}...")
                    
                return {
                    'success': success,
                    'message': message,
                    'email_id': email_id
                }
            else:
                # Just update classification without moving
                message = f"Email classified as '{category}' (stored in database)"
                logger.info(f"[Classification] [OK] {message} for {email_id[:20]}...")
                
                return {
                    'success': True,
                    'message': message,
                    'email_id': email_id
                }
        
        except Exception as e:
            logger.error(f"[Classification] Failed to update classification for {email_id[:20]}...: {e}")
            raise EmailProcessingError(f"Classification update failed: {str(e)}")


# Global service instance for FastAPI dependency injection
_email_processing_service: Optional[EmailProcessingService] = None


def get_email_processing_service() -> EmailProcessingService:
    """Factory function for EmailProcessingService dependency injection."""
    global _email_processing_service
    
    if _email_processing_service is None:
        from backend.core.dependencies import get_ai_service, get_email_provider
        from backend.services.task_service import get_task_service
        
        # Initialize dependencies
        ai_service = get_ai_service()
        email_provider = get_email_provider()
        task_service = get_task_service()
        
        _email_processing_service = EmailProcessingService(ai_service, email_provider, task_service)
    
    return _email_processing_service