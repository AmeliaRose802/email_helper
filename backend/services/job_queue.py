"""Job Queue Management Service for Email Processing Pipeline.

This module provides background job queue management using Celery and Redis
for processing emails asynchronously with retry mechanisms, priority handling,
and comprehensive error management.
"""

import uuid
import logging
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
import asyncio

# For now, using a simple in-memory implementation
# In production, would use: from celery import Celery
# from redis import Redis

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job execution status."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobType(Enum):
    """Types of processing jobs."""
    EMAIL_ANALYSIS = "email_analysis"
    TASK_EXTRACTION = "task_extraction"
    CATEGORIZATION = "categorization"
    BATCH_PROCESSING = "batch_processing"


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class JobProgress:
    """Job progress information."""
    step: str
    percentage: int
    message: str
    started_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ProcessingJob:
    """Processing job definition."""
    id: str
    type: JobType
    email_id: str
    user_id: str
    status: JobStatus
    priority: JobPriority
    progress: JobProgress
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(UTC).isoformat()


@dataclass
class ProcessingPipeline:
    """Processing pipeline definition."""
    id: str
    email_ids: List[str]
    user_id: str
    jobs: List[ProcessingJob]
    overall_progress: int
    status: str  # 'running', 'completed', 'failed', 'paused'
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(UTC).isoformat()


class JobQueue:
    """Job queue management with in-memory storage.

    This implementation provides basic job queue functionality for development.
    In production, this would be backed by Redis and Celery.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._jobs: Dict[str, ProcessingJob] = {}
        self._pipelines: Dict[str, ProcessingPipeline] = {}
        self._job_callbacks: Dict[str, List[callable]] = {}

        # Simulate Redis/Celery with in-memory structures
        self._queues = {
            JobPriority.URGENT: [],
            JobPriority.HIGH: [],
            JobPriority.MEDIUM: [],
            JobPriority.LOW: []
        }

        self.logger.info("JobQueue initialized with in-memory storage")

    async def create_pipeline(self, email_ids: List[str], user_id: str) -> str:
        """Create a new processing pipeline for multiple emails."""
        pipeline_id = f"pipeline_{uuid.uuid4().hex[:8]}"

        jobs = []
        for email_id in email_ids:
            # Create processing jobs for each email
            analysis_job = ProcessingJob(
                id=f"job_{uuid.uuid4().hex[:8]}",
                type=JobType.EMAIL_ANALYSIS,
                email_id=email_id,
                user_id=user_id,
                status=JobStatus.QUEUED,
                priority=JobPriority.MEDIUM,
                progress=JobProgress(
                    step="Email Analysis",
                    percentage=0,
                    message=f"Queued for analysis: {email_id}"
                )
            )

            task_job = ProcessingJob(
                id=f"job_{uuid.uuid4().hex[:8]}",
                type=JobType.TASK_EXTRACTION,
                email_id=email_id,
                user_id=user_id,
                status=JobStatus.QUEUED,
                priority=JobPriority.MEDIUM,
                progress=JobProgress(
                    step="Task Extraction",
                    percentage=0,
                    message=f"Queued for task extraction: {email_id}"
                )
            )

            category_job = ProcessingJob(
                id=f"job_{uuid.uuid4().hex[:8]}",
                type=JobType.CATEGORIZATION,
                email_id=email_id,
                user_id=user_id,
                status=JobStatus.QUEUED,
                priority=JobPriority.MEDIUM,
                progress=JobProgress(
                    step="Categorization",
                    percentage=0,
                    message=f"Queued for categorization: {email_id}"
                )
            )

            jobs.extend([analysis_job, task_job, category_job])

        pipeline = ProcessingPipeline(
            id=pipeline_id,
            email_ids=email_ids,
            user_id=user_id,
            jobs=jobs,
            overall_progress=0,
            status="running"
        )

        # Store pipeline and jobs
        self._pipelines[pipeline_id] = pipeline
        for job in jobs:
            self._jobs[job.id] = job
            # Add to appropriate priority queue
            self._queues[job.priority].append(job.id)

        self.logger.info(f"Created pipeline {pipeline_id} with {len(jobs)} jobs for {len(email_ids)} emails")
        return pipeline_id

    async def get_pipeline(self, pipeline_id: str) -> Optional[ProcessingPipeline]:
        """Get pipeline by ID."""
        return self._pipelines.get(pipeline_id)

    async def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Get job by ID."""
        return self._jobs.get(job_id)

    async def update_job_progress(self, job_id: str, progress: JobProgress) -> bool:
        """Update job progress."""
        if job_id not in self._jobs:
            return False

        job = self._jobs[job_id]
        job.progress = progress
        job.progress.updated_at = datetime.now(UTC).isoformat()

        # Update pipeline overall progress
        pipeline = next((p for p in self._pipelines.values()
                        if any(j.id == job_id for j in p.jobs)), None)
        if pipeline:
            await self._update_pipeline_progress(pipeline.id)

        # Trigger callbacks
        await self._trigger_callbacks(job_id, "progress_update")

        self.logger.debug(f"Updated progress for job {job_id}: {progress.percentage}%")
        return True

    async def complete_job(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Mark job as completed with result."""
        if job_id not in self._jobs:
            return False

        job = self._jobs[job_id]
        job.status = JobStatus.COMPLETED
        job.result = result
        job.completed_at = datetime.now(UTC).isoformat()
        job.progress.percentage = 100
        job.progress.message = "Completed successfully"
        job.progress.updated_at = datetime.now(UTC).isoformat()

        # Update pipeline progress
        pipeline = next((p for p in self._pipelines.values()
                        if any(j.id == job_id for j in p.jobs)), None)
        if pipeline:
            await self._update_pipeline_progress(pipeline.id)

        # Trigger callbacks
        await self._trigger_callbacks(job_id, "completed")

        self.logger.info(f"Completed job {job_id}")
        return True

    async def fail_job(self, job_id: str, error: str) -> bool:
        """Mark job as failed with error."""
        if job_id not in self._jobs:
            return False

        job = self._jobs[job_id]

        # Check if we should retry
        if job.retry_count < job.max_retries:
            job.retry_count += 1
            job.status = JobStatus.RETRYING
            job.error = f"Attempt {job.retry_count}: {error}"

            # Re-queue for retry with exponential backoff
            await asyncio.sleep(2 ** job.retry_count)  # 2, 4, 8 seconds
            job.status = JobStatus.QUEUED
            self._queues[job.priority].append(job.id)

            self.logger.warning(f"Retrying job {job_id} (attempt {job.retry_count}): {error}")
            await self._trigger_callbacks(job_id, "retry")
        else:
            # Max retries reached, mark as failed
            job.status = JobStatus.FAILED
            job.error = error
            job.completed_at = datetime.now(UTC).isoformat()
            job.progress.message = f"Failed: {error}"
            job.progress.updated_at = datetime.now(UTC).isoformat()

            self.logger.error(f"Job {job_id} failed after {job.max_retries} retries: {error}")
            await self._trigger_callbacks(job_id, "failed")

        # Update pipeline progress
        pipeline = next((p for p in self._pipelines.values()
                        if any(j.id == job_id for j in p.jobs)), None)
        if pipeline:
            await self._update_pipeline_progress(pipeline.id)

        return True

    async def get_next_job(self) -> Optional[ProcessingJob]:
        """Get next job from queue based on priority."""
        for priority in [JobPriority.URGENT, JobPriority.HIGH, JobPriority.MEDIUM, JobPriority.LOW]:
            queue = self._queues[priority]
            while queue:
                job_id = queue.pop(0)
                if job_id in self._jobs:
                    job = self._jobs[job_id]
                    if job.status == JobStatus.QUEUED:
                        job.status = JobStatus.PROCESSING
                        job.started_at = datetime.now(UTC).isoformat()
                        return job

        return None

    async def cancel_pipeline(self, pipeline_id: str) -> bool:
        """Cancel all jobs in a pipeline."""
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            return False

        cancelled_count = 0
        for job in pipeline.jobs:
            if job.status in [JobStatus.QUEUED, JobStatus.PROCESSING]:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now(UTC).isoformat()
                job.progress.message = "Cancelled by user"
                job.progress.updated_at = datetime.now(UTC).isoformat()
                cancelled_count += 1

        pipeline.status = "cancelled"
        pipeline.completed_at = datetime.now(UTC).isoformat()

        self.logger.info(f"Cancelled pipeline {pipeline_id} with {cancelled_count} jobs")
        await self._trigger_callbacks(pipeline_id, "pipeline_cancelled")
        return True

    async def register_callback(self, identifier: str, callback: callable):
        """Register callback for job or pipeline events."""
        if identifier not in self._job_callbacks:
            self._job_callbacks[identifier] = []
        self._job_callbacks[identifier].append(callback)

    async def _update_pipeline_progress(self, pipeline_id: str):
        """Update pipeline overall progress."""
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            return

        total_jobs = len(pipeline.jobs)
        if total_jobs == 0:
            return

        completed_jobs = sum(1 for job in pipeline.jobs if job.status == JobStatus.COMPLETED)
        failed_jobs = sum(1 for job in pipeline.jobs if job.status == JobStatus.FAILED)

        # Calculate overall progress
        total_progress = sum(job.progress.percentage for job in pipeline.jobs)
        pipeline.overall_progress = total_progress // total_jobs

        # Update pipeline status
        if completed_jobs == total_jobs:
            pipeline.status = "completed"
            pipeline.completed_at = datetime.now(UTC).isoformat()
        elif failed_jobs > 0 and (completed_jobs + failed_jobs) == total_jobs:
            pipeline.status = "failed"
            pipeline.completed_at = datetime.now(UTC).isoformat()

        await self._trigger_callbacks(pipeline_id, "pipeline_progress")

    async def _trigger_callbacks(self, identifier: str, event_type: str):
        """Trigger registered callbacks."""
        callbacks = self._job_callbacks.get(identifier, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(identifier, event_type)
                else:
                    callback(identifier, event_type)
            except Exception as e:
                self.logger.error(f"Callback error for {identifier}: {e}")


# Global job queue instance
job_queue = JobQueue()
