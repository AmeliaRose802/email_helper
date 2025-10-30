"""Automatic Email Processing Service.

This service runs in the background and automatically processes unclassified emails
with AI, even when the UI is minimized or not in focus. It polls for new emails
at regular intervals and queues them for classification.
"""

import asyncio
import logging
from typing import Optional, Set
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to Python path for existing service imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from backend.services.job_queue import job_queue
from backend.workers.email_processor import email_processor_worker

logger = logging.getLogger(__name__)


class AutoEmailProcessor:
    """Automatic background email processor that runs continuously."""
    
    def __init__(self, poll_interval: int = 60, max_batch_size: int = 10):
        """Initialize the auto processor.
        
        Args:
            poll_interval: Seconds between polling for new emails (default: 60)
            max_batch_size: Maximum emails to process in one batch (default: 10)
        """
        self.poll_interval = poll_interval
        self.max_batch_size = max_batch_size
        self.is_running = False
        self._stop_event = asyncio.Event()
        self._processed_emails: Set[str] = set()  # Track already processed emails
        self.logger = logging.getLogger(__name__)
        
        # Import services
        self.email_service = None
        self._init_services()
        
        self.logger.info(
            f"AutoEmailProcessor initialized: "
            f"poll_interval={poll_interval}s, max_batch_size={max_batch_size}"
        )
    
    def _init_services(self):
        """Initialize required services."""
        try:
            from backend.services.email_provider import get_email_provider
            self.email_service = get_email_provider()
            self.logger.info("Email service initialized for auto processing")
        except ImportError as e:
            self.logger.error(f"Failed to initialize email service: {e}")
            self.email_service = None
    
    async def start(self):
        """Start the automatic processor."""
        if self.is_running:
            self.logger.warning("Auto processor already running")
            return
        
        if not self.email_service:
            self.logger.error("Cannot start auto processor: email service not available")
            return
        
        self.is_running = True
        self._stop_event.clear()
        
        self.logger.info("[AUTO] Starting AutoEmailProcessor - emails will be classified automatically")
        
        # Ensure worker is started
        await email_processor_worker.start()
        
        # Start polling loop
        asyncio.create_task(self._polling_loop())
    
    async def stop(self):
        """Stop the automatic processor."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping AutoEmailProcessor")
        self.is_running = False
        self._stop_event.set()
    
    async def _polling_loop(self):
        """Main polling loop that checks for unclassified emails."""
        self.logger.info(f"Polling loop started (interval: {self.poll_interval}s)")
        
        while self.is_running:
            try:
                await self._check_and_process_emails()
                
                # Wait for next poll interval
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.poll_interval
                    )
                    # If we get here, stop was called
                    break
                except asyncio.TimeoutError:
                    # Timeout is normal - time for next poll
                    pass
                    
            except Exception as e:
                self.logger.error(f"Error in polling loop: {e}", exc_info=True)
                await asyncio.sleep(10)  # Wait before retrying on error
        
        self.logger.info("Polling loop stopped")
    
    async def _check_and_process_emails(self):
        """Check for unclassified emails and queue them for processing."""
        try:
            # Get recent emails (last 7 days) that need classification
            unclassified_emails = await self._get_unclassified_emails()
            
            if not unclassified_emails:
                return
            
            # Filter out already processed emails
            new_emails = [
                email for email in unclassified_emails
                if email['id'] not in self._processed_emails
            ]
            
            if not new_emails:
                return
            
            # Limit batch size
            batch = new_emails[:self.max_batch_size]
            email_ids = [email['id'] for email in batch]
            
            self.logger.info(
                f"[EMAIL] Found {len(new_emails)} new unclassified emails, "
                f"queuing {len(batch)} for AI processing"
            )
            
            # Create processing pipeline
            pipeline_id = await job_queue.create_pipeline(
                email_ids,
                user_id="system_auto_processor"
            )
            
            # Mark as processed
            self._processed_emails.update(email_ids)
            
            self.logger.info(
                f"[OK] Created processing pipeline {pipeline_id} for {len(batch)} emails"
            )
            
            # Clean up old processed email IDs (keep only last 1000)
            if len(self._processed_emails) > 1000:
                # Keep only the most recent 800
                self._processed_emails = set(list(self._processed_emails)[-800:])
            
        except Exception as e:
            self.logger.error(f"Error checking/processing emails: {e}", exc_info=True)
    
    async def _get_unclassified_emails(self):
        """Get emails that need AI classification.
        
        Returns:
            List of email dicts with id, subject, sender, etc.
        """
        try:
            # Try to get emails from the email service
            # This assumes the email service has a method to get unclassified emails
            if hasattr(self.email_service, 'get_unclassified_emails'):
                return await self.email_service.get_unclassified_emails(
                    max_count=self.max_batch_size * 2  # Get extra to filter
                )
            
            # Fallback: get recent emails and check for ai_category
            if hasattr(self.email_service, 'get_inbox_conversations'):
                conversations = await self.email_service.get_inbox_conversations(
                    skip=0,
                    limit=50  # Check recent 50 emails
                )
                
                unclassified = []
                for conv in conversations:
                    rep_email = conv.get('representativeEmail', {})
                    if not rep_email.get('ai_category'):
                        unclassified.append({
                            'id': rep_email.get('id'),
                            'subject': rep_email.get('subject'),
                            'sender': rep_email.get('sender'),
                            'received_date': rep_email.get('received_date')
                        })
                
                return unclassified
            
            # Email service doesn't support this - return empty list silently
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting unclassified emails: {e}", exc_info=True)
            return []
    
    def get_stats(self) -> dict:
        """Get statistics about the auto processor.
        
        Returns:
            Dict with stats like is_running, processed_count, etc.
        """
        return {
            'is_running': self.is_running,
            'poll_interval': self.poll_interval,
            'max_batch_size': self.max_batch_size,
            'processed_emails_count': len(self._processed_emails),
            'worker_running': email_processor_worker.is_running
        }


# Global auto processor instance with default settings
# Poll every 60 seconds, process up to 10 emails per batch
auto_email_processor = AutoEmailProcessor(poll_interval=60, max_batch_size=10)
