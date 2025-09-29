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
        """Get AI service with fallback."""
        try:
            from backend.services.ai_service import ai_service
            return ai_service
        except ImportError:
            self.logger.warning("AI service not available, using mock")
            return MockAIService()
    
    def _get_email_service(self):
        """Get email service with fallback."""
        try:
            from backend.services.email_provider import email_service
            return email_service
        except ImportError:
            self.logger.warning("Email service not available, using mock")
            return MockEmailService()
    
    def _get_task_service(self):
        """Get task service with fallback."""
        try:
            from backend.services.task_service import task_service
            return task_service
        except ImportError:
            self.logger.warning("Task service not available, using mock")
            return MockTaskService()
    
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
        
        email_data = await self.email_service.get_email(email_id)
        if not email_data:
            raise ValueError(f"Email {email_id} not found")
        
        # Step 2: Perform AI analysis
        await job_queue.update_job_progress(job.id, JobProgress(
            step="AI Analysis",
            percentage=50,
            message="Analyzing email content with AI..."
        ))
        
        analysis_result = await self.ai_service.analyze_email(email_data)
        
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
            message="Retrieving email analysis..."
        ))
        
        email_data = await self.email_service.get_email(email_id)
        if not email_data:
            raise ValueError(f"Email {email_id} not found")
        
        # Step 2: Extract tasks
        await job_queue.update_job_progress(job.id, JobProgress(
            step="Task Extraction",
            percentage=60,
            message="Extracting actionable tasks..."
        ))
        
        tasks = await self.ai_service.extract_tasks(email_data)
        
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
        
        email_data = await self.email_service.get_email(email_id)
        if not email_data:
            raise ValueError(f"Email {email_id} not found")
        
        # Step 2: Determine category
        await job_queue.update_job_progress(job.id, JobProgress(
            step="Categorization",
            percentage=70,
            message="Determining email category..."
        ))
        
        category_result = await self.ai_service.categorize_email(email_data)
        
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


# Mock services for development
class MockAIService:
    """Mock AI service for development."""
    
    async def analyze_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock email analysis."""
        await asyncio.sleep(2)  # Simulate processing time
        return {
            "sentiment": "neutral",
            "priority": "medium",
            "action_required": True,
            "confidence": 0.85
        }
    
    async def extract_tasks(self, email_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock task extraction."""
        await asyncio.sleep(1.5)  # Simulate processing time
        
        if "meeting" in email_data.get("content", "").lower():
            return [{
                "title": "Attend meeting",
                "description": "Meeting scheduled in email",
                "priority": "medium",
                "due_date": None
            }]
        
        return []
    
    async def categorize_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock email categorization."""
        await asyncio.sleep(1)  # Simulate processing time
        
        content = email_data.get("content", "").lower()
        if "urgent" in content:
            category = "urgent"
        elif "meeting" in content:
            category = "meetings"
        elif "project" in content:
            category = "projects"
        else:
            category = "general"
        
        return {
            "category": category,
            "confidence": 0.75,
            "tags": [category]
        }


class MockEmailService:
    """Mock email service for development."""
    
    async def get_email(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Mock get email."""
        await asyncio.sleep(0.1)  # Simulate database lookup
        return {
            "id": email_id,
            "subject": f"Sample Email {email_id}",
            "content": "This is a sample email content for processing.",
            "sender": "sender@example.com",
            "received_at": datetime.utcnow().isoformat()
        }
    
    async def update_email_category(self, email_id: str, category: Dict[str, Any]):
        """Mock update email category."""
        await asyncio.sleep(0.1)  # Simulate database update
        return True


class MockTaskService:
    """Mock task service for development."""
    
    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock create task."""
        await asyncio.sleep(0.1)  # Simulate database insert
        
        return {
            "id": f"task_{hash(str(task_data))}"[:16],
            "created_at": datetime.utcnow().isoformat(),
            **task_data
        }


# Global worker instance
email_processor_worker = EmailProcessorWorker()