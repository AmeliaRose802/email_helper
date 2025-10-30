"""Test suite for Processing Pipeline API endpoints."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from backend.api.processing import router
from backend.services.job_queue import job_queue, JobStatus, JobType, JobPriority
from backend.services.websocket_manager import websocket_manager
from backend.workers.email_processor import email_processor_worker


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock user data."""
    return {"user_id": "test_user_123", "email": "test@example.com"}



class TestProcessingAPI:
    """Test suite for Processing API endpoints."""
    
    def test_start_processing_success(self, client):
        """Test successful processing start."""
        email_ids = ["email_1", "email_2", "email_3"]
        
        response = client.post(
            "/api/processing/start",
            json={"email_ids": email_ids, "priority": "medium"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "pipeline_id" in data
        assert data["status"] == "started"
        assert data["email_count"] == 3
        assert "message" in data
    
    def test_start_processing_empty_emails(self, client):
        """Test processing start with empty email list."""
        response = client.post(
            "/api/processing/start",
            json={"email_ids": []}
        )
        
        assert response.status_code == 400
        assert "No email IDs provided" in response.json()["detail"]
    
    def test_start_processing_too_many_emails(self, client):
        """Test processing start with too many emails."""
        email_ids = [f"email_{i}" for i in range(101)]  # 101 emails
        
        response = client.post(
            "/api/processing/start",
            json={"email_ids": email_ids}
        )
        
        assert response.status_code == 400
        assert "Too many emails" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_processing_status_success(self, client):
        """Test getting processing status."""
        # Create a test pipeline
        email_ids = ["email_1", "email_2"]
        pipeline_id = await job_queue.create_pipeline(email_ids, "test_user_123")
        
        response = client.get(f"/api/processing/{pipeline_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["pipeline_id"] == pipeline_id
        assert data["email_count"] == 2
        assert "overall_progress" in data
        assert "jobs_completed" in data
        assert "jobs_failed" in data
    
    def test_get_processing_status_not_found(self, client):
        """Test getting status for non-existent pipeline."""
        response = client.get("/api/processing/nonexistent_pipeline/status")
        
        assert response.status_code == 404
        assert "Pipeline not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_pipeline_jobs_success(self, client):
        """Test getting pipeline jobs."""
        # Create a test pipeline
        email_ids = ["email_1", "email_2"]
        pipeline_id = await job_queue.create_pipeline(email_ids, "test_user_123")
        
        response = client.get(f"/api/processing/{pipeline_id}/jobs")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 6  # 3 jobs per email (analysis, extraction, categorization)
        
        # Check job structure
        job = data[0]
        assert "job_id" in job
        assert "type" in job
        assert "email_id" in job
        assert "status" in job
        assert "progress_percentage" in job
    
    @pytest.mark.asyncio
    async def test_cancel_processing_success(self, client):
        """Test successful processing cancellation."""
        # Create a test pipeline
        email_ids = ["email_1", "email_2"]
        pipeline_id = await job_queue.create_pipeline(email_ids, "test_user_123")
        
        response = client.post(f"/api/processing/{pipeline_id}/cancel")
        
        assert response.status_code == 200
        assert "cancelled successfully" in response.json()["message"]
        
        # Verify pipeline is cancelled
        pipeline = await job_queue.get_pipeline(pipeline_id)
        assert pipeline.status == "cancelled"
    
    def test_cancel_processing_not_found(self, client):
        """Test cancelling non-existent pipeline."""
        response = client.post("/api/processing/nonexistent_pipeline/cancel")
        
        assert response.status_code == 404
        assert "Pipeline not found" in response.json()["detail"]
    
    def test_get_processing_stats(self, client):
        """Test getting processing statistics."""
        response = client.get("/api/processing/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "processing_stats" in data
        assert "websocket_stats" in data
        
        processing_stats = data["processing_stats"]
        assert "total_pipelines" in processing_stats
        assert "active_pipelines" in processing_stats
        assert "worker_status" in processing_stats


class TestJobQueue:
    """Test suite for Job Queue functionality."""
    
    @pytest.mark.asyncio
    async def test_create_pipeline(self):
        """Test pipeline creation."""
        email_ids = ["email_1", "email_2"]
        user_id = "test_user"
        
        pipeline_id = await job_queue.create_pipeline(email_ids, user_id)
        
        assert pipeline_id is not None
        assert pipeline_id.startswith("pipeline_")
        
        # Verify pipeline exists
        pipeline = await job_queue.get_pipeline(pipeline_id)
        assert pipeline is not None
        assert pipeline.user_id == user_id
        assert pipeline.email_ids == email_ids
        assert len(pipeline.jobs) == 6  # 3 jobs per email
    
    @pytest.mark.asyncio
    async def test_job_progress_update(self):
        """Test job progress updates."""
        # Create pipeline
        pipeline_id = await job_queue.create_pipeline(["email_1"], "test_user")
        pipeline = await job_queue.get_pipeline(pipeline_id)
        job = pipeline.jobs[0]
        
        # Update progress
        from backend.services.job_queue import JobProgress
        progress = JobProgress(
            step="Test Step",
            percentage=50,
            message="Test progress update"
        )
        
        success = await job_queue.update_job_progress(job.id, progress)
        assert success is True
        
        # Verify update
        updated_job = await job_queue.get_job(job.id)
        assert updated_job.progress.percentage == 50
        assert updated_job.progress.message == "Test progress update"
    
    @pytest.mark.asyncio
    async def test_complete_job(self):
        """Test job completion."""
        # Create pipeline
        pipeline_id = await job_queue.create_pipeline(["email_1"], "test_user")
        pipeline = await job_queue.get_pipeline(pipeline_id)
        job = pipeline.jobs[0]
        
        # Complete job
        result = {"test": "result"}
        success = await job_queue.complete_job(job.id, result)
        assert success is True
        
        # Verify completion
        completed_job = await job_queue.get_job(job.id)
        assert completed_job.status == JobStatus.COMPLETED
        assert completed_job.result == result
        assert completed_job.progress.percentage == 100
    
    @pytest.mark.asyncio
    async def test_fail_job_with_retry(self):
        """Test job failure with retry mechanism."""
        # Create pipeline
        pipeline_id = await job_queue.create_pipeline(["email_1"], "test_user")
        pipeline = await job_queue.get_pipeline(pipeline_id)
        job = pipeline.jobs[0]
        
        # Fail job (should retry)
        error_message = "Test error"
        success = await job_queue.fail_job(job.id, error_message)
        assert success is True
        
        # Verify retry attempt
        failed_job = await job_queue.get_job(job.id)
        assert failed_job.retry_count == 1
        assert error_message in failed_job.error
    
    @pytest.mark.asyncio
    async def test_cancel_pipeline(self):
        """Test pipeline cancellation."""
        # Create pipeline
        pipeline_id = await job_queue.create_pipeline(["email_1", "email_2"], "test_user")
        
        # Cancel pipeline
        success = await job_queue.cancel_pipeline(pipeline_id)
        assert success is True
        
        # Verify cancellation
        pipeline = await job_queue.get_pipeline(pipeline_id)
        assert pipeline.status == "cancelled"
        
        # Verify all jobs are cancelled
        for job in pipeline.jobs:
            assert job.status == JobStatus.CANCELLED


class TestWebSocketManager:
    """Test suite for WebSocket Manager."""
    
    @pytest.mark.asyncio
    async def test_websocket_stats(self):
        """Test WebSocket statistics."""
        stats = await websocket_manager.get_stats()
        
        assert "websocket_manager" in stats
        assert "connections" in stats
        assert "features" in stats
        
        features = stats["features"]
        assert features["real_time_updates"] is True
        assert features["pipeline_subscriptions"] is True


class TestEmailProcessorWorker:
    """Test suite for Email Processor Worker."""
    
    def test_worker_initialization(self):
        """Test worker initialization."""
        assert email_processor_worker is not None
        assert hasattr(email_processor_worker, 'start')
        assert hasattr(email_processor_worker, 'stop')
    
    @pytest.mark.asyncio
    async def test_worker_start_stop(self):
        """Test worker start and stop."""
        # Start worker
        await email_processor_worker.start()
        assert email_processor_worker.is_running is True
        
        # Stop worker
        await email_processor_worker.stop()
        assert email_processor_worker.is_running is False


class TestIntegration:
    """Integration tests for the complete processing pipeline."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_processing(self):
        """Test complete processing pipeline."""
        # Create pipeline
        email_ids = ["test_email_1"]
        user_id = "test_user"
        pipeline_id = await job_queue.create_pipeline(email_ids, user_id)
        
        # Get pipeline
        pipeline = await job_queue.get_pipeline(pipeline_id)
        assert pipeline is not None
        assert len(pipeline.jobs) == 3  # 3 jobs for 1 email
        
        # Simulate job processing
        for job in pipeline.jobs:
            # Start job
            job.status = JobStatus.PROCESSING
            
            # Update progress
            from backend.services.job_queue import JobProgress
            progress = JobProgress(
                step=f"Processing {job.type.value}",
                percentage=50,
                message=f"Processing {job.type.value}..."
            )
            await job_queue.update_job_progress(job.id, progress)
            
            # Complete job
            result = {"processed": True, "job_type": job.type.value}
            await job_queue.complete_job(job.id, result)
        
        # Verify pipeline completion
        final_pipeline = await job_queue.get_pipeline(pipeline_id)
        assert final_pipeline.status == "completed"
        assert final_pipeline.overall_progress == 100
        
        # Verify all jobs completed
        for job in final_pipeline.jobs:
            assert job.status == JobStatus.COMPLETED
            assert job.result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])