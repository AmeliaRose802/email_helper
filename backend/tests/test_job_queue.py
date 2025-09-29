"""Test suite for Job Queue functionality."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from backend.services.job_queue import (
    JobQueue, 
    ProcessingJob, 
    ProcessingPipeline, 
    JobStatus, 
    JobType, 
    JobPriority, 
    JobProgress
)


class TestJobStatus:
    """Test JobStatus enum."""
    
    def test_job_status_values(self):
        """Test job status enum values."""
        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"
        assert JobStatus.RETRYING.value == "retrying"


class TestJobType:
    """Test JobType enum."""
    
    def test_job_type_values(self):
        """Test job type enum values."""
        assert JobType.EMAIL_ANALYSIS.value == "email_analysis"
        assert JobType.TASK_EXTRACTION.value == "task_extraction"
        assert JobType.CATEGORIZATION.value == "categorization"
        assert JobType.BATCH_PROCESSING.value == "batch_processing"


class TestJobPriority:
    """Test JobPriority enum."""
    
    def test_job_priority_values(self):
        """Test job priority enum values."""
        assert JobPriority.LOW.value == 1
        assert JobPriority.MEDIUM.value == 2
        assert JobPriority.HIGH.value == 3
        assert JobPriority.URGENT.value == 4


class TestJobProgress:
    """Test JobProgress data class."""
    
    def test_job_progress_creation(self):
        """Test JobProgress creation."""
        progress = JobProgress(
            step="Test Step",
            percentage=50,
            message="Test message"
        )
        
        assert progress.step == "Test Step"
        assert progress.percentage == 50
        assert progress.message == "Test message"
        assert progress.started_at is None
        assert progress.updated_at is None


class TestProcessingJob:
    """Test ProcessingJob data class."""
    
    def test_processing_job_creation(self):
        """Test ProcessingJob creation."""
        progress = JobProgress(
            step="Analysis",
            percentage=0,
            message="Starting analysis"
        )
        
        job = ProcessingJob(
            id="test_job_1",
            type=JobType.EMAIL_ANALYSIS,
            email_id="email_123",
            user_id="user_456",
            status=JobStatus.QUEUED,
            priority=JobPriority.MEDIUM,
            progress=progress
        )
        
        assert job.id == "test_job_1"
        assert job.type == JobType.EMAIL_ANALYSIS
        assert job.email_id == "email_123"
        assert job.user_id == "user_456"
        assert job.status == JobStatus.QUEUED
        assert job.priority == JobPriority.MEDIUM
        assert job.progress == progress
        assert job.result is None
        assert job.error is None
        assert job.created_at is not None
        assert job.retry_count == 0
        assert job.max_retries == 3
    
    def test_processing_job_post_init(self):
        """Test ProcessingJob post init sets created_at."""
        progress = JobProgress("Test", 0, "Test")
        job = ProcessingJob(
            id="test",
            type=JobType.EMAIL_ANALYSIS,
            email_id="email",
            user_id="user",
            status=JobStatus.QUEUED,
            priority=JobPriority.MEDIUM,
            progress=progress
        )
        
        assert job.created_at is not None
        # Should be in ISO format
        datetime.fromisoformat(job.created_at)


class TestProcessingPipeline:
    """Test ProcessingPipeline data class."""
    
    def test_processing_pipeline_creation(self):
        """Test ProcessingPipeline creation."""
        jobs = []
        pipeline = ProcessingPipeline(
            id="pipeline_123",
            email_ids=["email_1", "email_2"],
            user_id="user_456",
            jobs=jobs,
            overall_progress=0,
            status="running"
        )
        
        assert pipeline.id == "pipeline_123"
        assert pipeline.email_ids == ["email_1", "email_2"]
        assert pipeline.user_id == "user_456"
        assert pipeline.jobs == jobs
        assert pipeline.overall_progress == 0
        assert pipeline.status == "running"
        assert pipeline.created_at is not None


class TestJobQueue:
    """Test JobQueue class."""
    
    @pytest.fixture
    def job_queue(self):
        """Create a fresh JobQueue instance for each test."""
        return JobQueue()
    
    def test_job_queue_initialization(self, job_queue):
        """Test JobQueue initialization."""
        assert job_queue._jobs == {}
        assert job_queue._pipelines == {}
        assert job_queue._job_callbacks == {}
        assert len(job_queue._queues) == 4  # One for each priority
    
    @pytest.mark.asyncio
    async def test_create_pipeline(self, job_queue):
        """Test pipeline creation."""
        email_ids = ["email_1", "email_2"]
        user_id = "test_user"
        
        pipeline_id = await job_queue.create_pipeline(email_ids, user_id)
        
        assert pipeline_id is not None
        assert pipeline_id.startswith("pipeline_")
        
        # Verify pipeline was created
        pipeline = await job_queue.get_pipeline(pipeline_id)
        assert pipeline is not None
        assert pipeline.user_id == user_id
        assert pipeline.email_ids == email_ids
        assert len(pipeline.jobs) == 6  # 3 jobs per email
        assert pipeline.status == "running"
        
        # Verify jobs were created and queued
        for job in pipeline.jobs:
            assert job.user_id == user_id
            assert job.email_id in email_ids
            assert job.status == JobStatus.QUEUED
            assert job.priority == JobPriority.MEDIUM
            assert job.id in job_queue._jobs
    
    @pytest.mark.asyncio
    async def test_get_pipeline_nonexistent(self, job_queue):
        """Test getting non-existent pipeline."""
        result = await job_queue.get_pipeline("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_job_nonexistent(self, job_queue):
        """Test getting non-existent job."""
        result = await job_queue.get_job("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_job_progress(self, job_queue):
        """Test updating job progress."""
        # Create a pipeline with jobs
        pipeline_id = await job_queue.create_pipeline(["email_1"], "user_1")
        pipeline = await job_queue.get_pipeline(pipeline_id)
        job = pipeline.jobs[0]
        
        # Update progress
        new_progress = JobProgress(
            step="Updated Step",
            percentage=75,
            message="Updated message"
        )
        
        success = await job_queue.update_job_progress(job.id, new_progress)
        assert success is True
        
        # Verify update
        updated_job = await job_queue.get_job(job.id)
        assert updated_job.progress.step == "Updated Step"
        assert updated_job.progress.percentage == 75
        assert updated_job.progress.message == "Updated message"
        assert updated_job.progress.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_update_job_progress_nonexistent(self, job_queue):
        """Test updating progress for non-existent job."""
        progress = JobProgress("Test", 50, "Test")
        success = await job_queue.update_job_progress("nonexistent", progress)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_complete_job(self, job_queue):
        """Test completing a job."""
        # Create a pipeline with jobs
        pipeline_id = await job_queue.create_pipeline(["email_1"], "user_1")
        pipeline = await job_queue.get_pipeline(pipeline_id)
        job = pipeline.jobs[0]
        
        # Complete job
        result = {"test": "result", "processed": True}
        success = await job_queue.complete_job(job.id, result)
        assert success is True
        
        # Verify completion
        completed_job = await job_queue.get_job(job.id)
        assert completed_job.status == JobStatus.COMPLETED
        assert completed_job.result == result
        assert completed_job.completed_at is not None
        assert completed_job.progress.percentage == 100
        assert completed_job.progress.message == "Completed successfully"
    
    @pytest.mark.asyncio
    async def test_complete_job_nonexistent(self, job_queue):
        """Test completing non-existent job."""
        success = await job_queue.complete_job("nonexistent", {"test": "result"})
        assert success is False
    
    @pytest.mark.asyncio
    async def test_fail_job_with_retries(self, job_queue):
        """Test failing a job with retry logic."""
        # Create a pipeline with jobs
        pipeline_id = await job_queue.create_pipeline(["email_1"], "user_1")
        pipeline = await job_queue.get_pipeline(pipeline_id)
        job = pipeline.jobs[0]
        
        # Fail job (should trigger retry)
        error_message = "Test error occurred"
        success = await job_queue.fail_job(job.id, error_message)
        assert success is True
        
        # Verify retry was attempted
        failed_job = await job_queue.get_job(job.id)
        assert failed_job.retry_count == 1
        assert error_message in failed_job.error
        # Job should be queued again for retry
        assert failed_job.status == JobStatus.QUEUED
    
    @pytest.mark.asyncio
    async def test_fail_job_max_retries(self, job_queue):
        """Test failing a job after max retries."""
        # Create a pipeline with jobs
        pipeline_id = await job_queue.create_pipeline(["email_1"], "user_1")
        pipeline = await job_queue.get_pipeline(pipeline_id)
        job = pipeline.jobs[0]
        
        # Set job to max retries
        job.retry_count = job.max_retries
        
        # Fail job (should not retry)
        error_message = "Final error"
        success = await job_queue.fail_job(job.id, error_message)
        assert success is True
        
        # Verify job is marked as failed
        failed_job = await job_queue.get_job(job.id)
        assert failed_job.status == JobStatus.FAILED
        assert failed_job.error == error_message
        assert failed_job.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_get_next_job_priority_order(self, job_queue):
        """Test getting next job respects priority order."""
        # Create jobs with different priorities
        await job_queue.create_pipeline(["email_1"], "user_1")
        
        # Manually add jobs with different priorities
        urgent_job = ProcessingJob(
            id="urgent_job",
            type=JobType.EMAIL_ANALYSIS,
            email_id="email_urgent",
            user_id="user_1",
            status=JobStatus.QUEUED,
            priority=JobPriority.URGENT,
            progress=JobProgress("Urgent", 0, "Urgent job")
        )
        
        low_job = ProcessingJob(
            id="low_job",
            type=JobType.EMAIL_ANALYSIS,
            email_id="email_low",
            user_id="user_1",
            status=JobStatus.QUEUED,
            priority=JobPriority.LOW,
            progress=JobProgress("Low", 0, "Low priority job")
        )
        
        job_queue._jobs[urgent_job.id] = urgent_job
        job_queue._jobs[low_job.id] = low_job
        job_queue._queues[JobPriority.URGENT].append(urgent_job.id)
        job_queue._queues[JobPriority.LOW].append(low_job.id)
        
        # Get next job should return urgent job first
        next_job = await job_queue.get_next_job()
        assert next_job is not None
        assert next_job.id == "urgent_job"
        assert next_job.status == JobStatus.PROCESSING
    
    @pytest.mark.asyncio
    async def test_get_next_job_empty_queue(self, job_queue):
        """Test getting next job from empty queue."""
        next_job = await job_queue.get_next_job()
        assert next_job is None
    
    @pytest.mark.asyncio
    async def test_cancel_pipeline(self, job_queue):
        """Test cancelling a pipeline."""
        # Create a pipeline
        pipeline_id = await job_queue.create_pipeline(["email_1", "email_2"], "user_1")
        
        # Cancel pipeline
        success = await job_queue.cancel_pipeline(pipeline_id)
        assert success is True
        
        # Verify pipeline is cancelled
        pipeline = await job_queue.get_pipeline(pipeline_id)
        assert pipeline.status == "cancelled"
        assert pipeline.completed_at is not None
        
        # Verify all jobs are cancelled
        for job in pipeline.jobs:
            assert job.status == JobStatus.CANCELLED
            assert job.completed_at is not None
            assert "Cancelled by user" in job.progress.message
    
    @pytest.mark.asyncio
    async def test_cancel_pipeline_nonexistent(self, job_queue):
        """Test cancelling non-existent pipeline."""
        success = await job_queue.cancel_pipeline("nonexistent")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_register_callback(self, job_queue):
        """Test registering callbacks."""
        callback_called = False
        callback_args = None
        
        async def test_callback(identifier, event_type):
            nonlocal callback_called, callback_args
            callback_called = True
            callback_args = (identifier, event_type)
        
        # Register callback
        await job_queue.register_callback("test_id", test_callback)
        
        # Verify callback was registered
        assert "test_id" in job_queue._job_callbacks
        assert test_callback in job_queue._job_callbacks["test_id"]
    
    @pytest.mark.asyncio
    async def test_pipeline_progress_calculation(self, job_queue):
        """Test pipeline progress calculation."""
        # Create a pipeline
        pipeline_id = await job_queue.create_pipeline(["email_1"], "user_1")
        pipeline = await job_queue.get_pipeline(pipeline_id)
        
        # Complete some jobs
        job1 = pipeline.jobs[0]
        job2 = pipeline.jobs[1]
        
        # Complete first job
        await job_queue.complete_job(job1.id, {"result": "completed"})
        
        # Update second job progress to 50%
        progress = JobProgress("Step 2", 50, "Half done")
        await job_queue.update_job_progress(job2.id, progress)
        
        # Check pipeline progress
        updated_pipeline = await job_queue.get_pipeline(pipeline_id)
        # Progress should be calculated based on all jobs
        expected_progress = (100 + 50 + 0) // 3  # 3 jobs total
        assert updated_pipeline.overall_progress == expected_progress
    
    @pytest.mark.asyncio
    async def test_pipeline_completion_detection(self, job_queue):
        """Test pipeline completion detection."""
        # Create a pipeline
        pipeline_id = await job_queue.create_pipeline(["email_1"], "user_1")
        pipeline = await job_queue.get_pipeline(pipeline_id)
        
        # Complete all jobs
        for job in pipeline.jobs:
            await job_queue.complete_job(job.id, {"result": "completed"})
        
        # Check pipeline status
        final_pipeline = await job_queue.get_pipeline(pipeline_id)
        assert final_pipeline.status == "completed"
        assert final_pipeline.overall_progress == 100
        assert final_pipeline.completed_at is not None


class TestJobQueueEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def job_queue(self):
        """Create a fresh JobQueue instance for each test."""
        return JobQueue()
    
    @pytest.mark.asyncio
    async def test_concurrent_job_updates(self, job_queue):
        """Test concurrent job updates."""
        # Create a pipeline
        pipeline_id = await job_queue.create_pipeline(["email_1"], "user_1")
        pipeline = await job_queue.get_pipeline(pipeline_id)
        job = pipeline.jobs[0]
        
        # Simulate concurrent updates
        async def update_progress(percentage, message):
            progress = JobProgress("Concurrent", percentage, message)
            return await job_queue.update_job_progress(job.id, progress)
        
        # Run concurrent updates
        results = await asyncio.gather(
            update_progress(25, "Update 1"),
            update_progress(50, "Update 2"),
            update_progress(75, "Update 3"),
            return_exceptions=True
        )
        
        # All updates should succeed
        assert all(result is True for result in results)
        
        # Final job should have one of the updates
        final_job = await job_queue.get_job(job.id)
        assert final_job.progress.percentage in [25, 50, 75]
    
    @pytest.mark.asyncio
    async def test_empty_email_list_pipeline(self, job_queue):
        """Test creating pipeline with empty email list."""
        pipeline_id = await job_queue.create_pipeline([], "user_1")
        pipeline = await job_queue.get_pipeline(pipeline_id)
        
        assert pipeline is not None
        assert len(pipeline.jobs) == 0
        assert pipeline.overall_progress == 0
    
    @pytest.mark.asyncio
    async def test_large_pipeline(self, job_queue):
        """Test creating large pipeline."""
        # Create pipeline with many emails
        email_ids = [f"email_{i}" for i in range(20)]
        pipeline_id = await job_queue.create_pipeline(email_ids, "user_1")
        pipeline = await job_queue.get_pipeline(pipeline_id)
        
        assert len(pipeline.jobs) == 60  # 3 jobs per email * 20 emails
        assert len(pipeline.email_ids) == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])