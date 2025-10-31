"""Background Email Processing Worker.

This module provides background email processing capabilities including
AI analysis, task extraction, and categorization with progress tracking
and comprehensive error handling.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from backend.services.job_queue import job_queue, JobType, JobProgress
from backend.services.websocket_manager import websocket_manager


class EmailProcessorWorker:
    """Background worker for processing emails asynchronously."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self._stop_event = asyncio.Event()
        
        # Services are lazily initialized when first accessed
        self._ai_service = None
        self._email_service = None
        self._task_service = None
        
        self.logger.info("EmailProcessorWorker initialized")
    
    async def _update_progress(self, job_id: str, step: str, percentage: int, message: str):
        """Update job progress and broadcast to websocket clients.
        
        Args:
            job_id: Job identifier
            step: Current processing step name
            percentage: Progress percentage (0-100)
            message: Human-readable progress message
        """
        await job_queue.update_job_progress(job_id, JobProgress(
            step=step,
            percentage=percentage,
            message=message,
            started_at=datetime.utcnow().isoformat() if percentage == 5 else None
        ))
        
        await websocket_manager.broadcast_job_status(job_id, {
            "status": "processing",
            "progress": percentage,
            "message": message
        })
    
    @property
    def ai_service(self):
        """Lazy-load AI service."""
        if self._ai_service is None:
            self._ai_service = self._get_ai_service()
        return self._ai_service
    
    @property
    def email_service(self):
        """Lazy-load email service."""
        if self._email_service is None:
            self._email_service = self._get_email_service()
        return self._email_service
    
    @property
    def task_service(self):
        """Lazy-load task service."""
        if self._task_service is None:
            self._task_service = self._get_task_service()
        return self._task_service
    
    def _get_ai_service(self):
        """Get AI service - no fallback to mock."""
        try:
            from backend.services.ai_service import get_ai_service
            return get_ai_service()
        except ImportError as e:
            self.logger.error(f"AI service import failed: {e}")
            raise ImportError(f"AI service required but not available: {e}")
    
    def _get_email_service(self):
        """Get email service - no fallback to mock."""
        try:
            from backend.services.email_provider import get_email_provider
            return get_email_provider()
        except ImportError as e:
            self.logger.error(f"Email service import failed: {e}")
            raise ImportError(f"Email service required but not available: {e}")
    
    def _get_task_service(self):
        """Get task service - no fallback to mock."""
        try:
            from backend.services.task_service import get_task_service
            return get_task_service()
        except ImportError as e:
            self.logger.error(f"Task service import failed: {e}")
            raise ImportError(f"Task service required but not available: {e}")
    
    async def start(self):
        """Start the background worker."""
        if self.is_running:
            self.logger.warning("Worker already running")
            return
        
        self.is_running = True
        self._stop_event.clear()
        
        self.logger.info("Starting EmailProcessorWorker")
        
        # Start processing loop
        asyncio.create_task(self._processing_loop())
    
    async def stop(self):
        """Stop the background worker."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping EmailProcessorWorker")
        self.is_running = False
        self._stop_event.set()
    
    async def _processing_loop(self):
        """Main processing loop."""
        while self.is_running:
            try:
                # Get next job from queue
                job = await job_queue.get_next_job()
                
                if job:
                    self.logger.info(f"Processing job {job.id} of type {job.type.value}")
                    await self._process_job(job)
                else:
                    # No jobs available, wait a bit
                    await asyncio.sleep(1)
                
                # Check for stop event
                if self._stop_event.is_set():
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
        
        self.logger.info("EmailProcessorWorker stopped")
    
    async def _process_job(self, job):
        """Process a single job."""
        try:
            # Update job status to processing
            await self._update_progress(job.id, job.progress.step, 5, f"Starting {job.type.value}...")
            
            # Process based on job type
            if job.type == JobType.EMAIL_ANALYSIS:
                result = await self._process_email_analysis(job)
            elif job.type == JobType.TASK_EXTRACTION:
                result = await self._process_task_extraction(job)
            elif job.type == JobType.CATEGORIZATION:
                result = await self._process_categorization(job)
            else:
                raise ValueError(f"Unknown job type: {job.type}")
            
            # Mark job as completed
            await job_queue.complete_job(job.id, result)
            
            # Broadcast completion
            await websocket_manager.broadcast_job_status(job.id, {
                "status": "completed",
                "progress": 100,
                "message": f"{job.type.value} completed successfully",
                "result": result
            })
            
        except Exception as e:
            self.logger.error(f"Job {job.id} failed: {e}")
            await job_queue.fail_job(job.id, str(e))
            
            # Broadcast failure
            await websocket_manager.broadcast_job_status(job.id, {
                "status": "failed",
                "progress": job.progress.percentage,
                "message": f"{job.type.value} failed: {str(e)}",
                "error": str(e)
            })
    
    async def _process_email_analysis(self, job) -> Dict[str, Any]:
        """Process email AI analysis."""
        email_id = job.email_id
        
        # Step 1: Get email data
        await self._update_progress(job.id, "AI Analysis", 20, "Retrieving email data...")
        
        email_data = await self.email_service.get_email_content(email_id)
        if not email_data:
            raise ValueError(f"Email {email_id} not found")
        
        # Step 2: Perform AI analysis
        await self._update_progress(job.id, "AI Analysis", 50, "Analyzing email content with AI...")
        
        analysis_result = await self.ai_service.generate_summary(email_data)
        
        # Step 3: Store results
        await self._update_progress(job.id, "AI Analysis", 90, "Storing analysis results...")
        
        # Store analysis (mock implementation)
        stored_result = {
            "email_id": email_id,
            "analysis": analysis_result,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        return stored_result
    
    async def _process_task_extraction(self, job) -> Dict[str, Any]:
        """Process task extraction from email."""
        email_id = job.email_id
        
        # Step 1: Get email and analysis data
        await self._update_progress(job.id, "Task Extraction", 20, "Retrieving email data...")
        
        email_data = await self.email_service.get_email_content(email_id)
        if not email_data:
            raise ValueError(f"Email {email_id} not found")
        
        # Step 2: Extract tasks
        await self._update_progress(job.id, "Task Extraction", 60, "Extracting actionable tasks...")
        
        tasks = await self.ai_service.extract_action_items(email_data)
        
        # Step 3: Create tasks in system
        await self._update_progress(job.id, "Task Extraction", 85, "Creating tasks in system...")
        
        created_tasks = []
        for task_data in tasks:
            task = await self.task_service.create_task({
                **task_data,
                "email_id": email_id,
                "source": "email_processing"
            })
            created_tasks.append(task)
        
        return {
            "email_id": email_id,
            "tasks_created": len(created_tasks),
            "tasks": created_tasks,
            "processed_at": datetime.utcnow().isoformat()
        }
    
    async def _process_categorization(self, job) -> Dict[str, Any]:
        """Process email categorization."""
        email_id = job.email_id
        
        # Step 1: Get email data
        await self._update_progress(job.id, "Categorization", 30, "Retrieving email data...")
        
        email_data = await self.email_service.get_email_content(email_id)
        if not email_data:
            raise ValueError(f"Email {email_id} not found")
        
        # Step 2: Determine category
        await self._update_progress(job.id, "Categorization", 70, "Determining email category...")
        
        category_result = await self.ai_service.classify_email(email_data)
        
        # Step 3: Update email category
        await self._update_progress(job.id, "Categorization", 90, "Updating email category...")
        
        await self.email_service.update_email_category(email_id, category_result)
        
        return {
            "email_id": email_id,
            "category": category_result,
            "processed_at": datetime.utcnow().isoformat()
        }


# Lazy-initialized global worker instance
_email_processor_worker: Optional[EmailProcessorWorker] = None


def get_email_processor_worker() -> EmailProcessorWorker:
    """Get or create the global email processor worker instance.
    
    This lazy initialization pattern ensures the worker is only created when
    actually needed, not at module import time. This prevents test collection
    failures when COM/email services aren't configured.
    """
    global _email_processor_worker
    if _email_processor_worker is None:
        _email_processor_worker = EmailProcessorWorker()
    return _email_processor_worker


