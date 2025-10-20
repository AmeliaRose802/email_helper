"""Background Email Processing Worker.

This module provides background email processing capabilities including
AI analysis, task extraction, and categorization with progress tracking
and comprehensive error handling.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add src to Python path for existing service imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from backend.services.job_queue import job_queue, JobStatus, JobType, JobProgress
from backend.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class EmailProcessorWorker:
    """Background worker for processing emails asynchronously."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self._stop_event = asyncio.Event()
        
        # Import services (with fallbacks for development)
        self.ai_service = self._get_ai_service()
        self.email_service = self._get_email_service()
        self.task_service = self._get_task_service()
        
        self.logger.info("EmailProcessorWorker initialized")
    
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
            # Update job status
            await job_queue.update_job_progress(job.id, JobProgress(
                step=job.progress.step,
                percentage=5,
                message=f"Starting {job.type.value}...",
                started_at=datetime.utcnow().isoformat()
            ))
            
            # Broadcast job start
            await websocket_manager.broadcast_job_status(job.id, {
                "status": "processing",
                "progress": 5,
                "message": f"Starting {job.type.value}..."
            })
            
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
        await job_queue.update_job_progress(job.id, JobProgress(
            step="AI Analysis",
            percentage=20,
            message="Retrieving email data..."
        ))
        
        email_data = await self.email_service.get_email_content(email_id)
        if not email_data:
            raise ValueError(f"Email {email_id} not found")
        
        # Step 2: Perform AI analysis
        await job_queue.update_job_progress(job.id, JobProgress(
            step="AI Analysis",
            percentage=50,
            message="Analyzing email content with AI..."
        ))
        
        analysis_result = await self.ai_service.generate_summary(email_data)
        
        # Step 3: Store results
        await job_queue.update_job_progress(job.id, JobProgress(
            step="AI Analysis",
            percentage=90,
            message="Storing analysis results..."
        ))
        
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
        await job_queue.update_job_progress(job.id, JobProgress(
            step="Task Extraction",
            percentage=20,
            message="Retrieving email data..."
        ))
        
        email_data = await self.email_service.get_email_content(email_id)
        if not email_data:
            raise ValueError(f"Email {email_id} not found")
        
        # Step 2: Extract tasks
        await job_queue.update_job_progress(job.id, JobProgress(
            step="Task Extraction",
            percentage=60,
            message="Extracting actionable tasks..."
        ))
        
        tasks = await self.ai_service.extract_action_items(email_data)
        
        # Step 3: Create tasks in system
        await job_queue.update_job_progress(job.id, JobProgress(
            step="Task Extraction",
            percentage=85,
            message="Creating tasks in system..."
        ))
        
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
        await job_queue.update_job_progress(job.id, JobProgress(
            step="Categorization",
            percentage=30,
            message="Retrieving email data..."
        ))
        
        email_data = await self.email_service.get_email_content(email_id)
        if not email_data:
            raise ValueError(f"Email {email_id} not found")
        
        # Step 2: Determine category
        await job_queue.update_job_progress(job.id, JobProgress(
            step="Categorization",
            percentage=70,
            message="Determining email category..."
        ))
        
        category_result = await self.ai_service.classify_email(email_data)
        
        # Step 3: Update email category
        await job_queue.update_job_progress(job.id, JobProgress(
            step="Categorization",
            percentage=90,
            message="Updating email category..."
        ))
        
        await self.email_service.update_email_category(email_id, category_result)
        
        return {
            "email_id": email_id,
            "category": category_result,
            "processed_at": datetime.utcnow().isoformat()
        }


# Global worker instance
email_processor_worker = EmailProcessorWorker()