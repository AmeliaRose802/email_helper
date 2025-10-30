"""Processing Pipeline API Endpoints.

This module provides API endpoints for managing email processing pipelines,
job queuing, WebSocket connections, and real-time status updates.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from pydantic import BaseModel, Field

from backend.services.job_queue import job_queue, ProcessingPipeline, ProcessingJob
from backend.services.websocket_manager import websocket_manager
from backend.workers.email_processor import email_processor_worker

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class StartProcessingRequest(BaseModel):
    """Request model for starting email processing."""
    email_ids: List[str] = Field(..., description="List of email IDs to process")
    priority: str = Field("medium", description="Processing priority (low, medium, high, urgent)")


class ProcessingStatusResponse(BaseModel):
    """Response model for processing status."""
    pipeline_id: str
    status: str
    overall_progress: int
    email_count: int
    jobs_completed: int
    jobs_failed: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    type: str
    email_id: str
    status: str
    progress_percentage: int
    progress_message: str
    error: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]


@router.post("/processing/start", response_model=Dict[str, Any])
async def start_processing(
    request: StartProcessingRequest
):
    """Start email processing pipeline for multiple emails."""
    try:
        # Use default user since auth is disabled
        user_id = "default_user"
        
        if not request.email_ids:
            raise HTTPException(status_code=400, detail="No email IDs provided")
        
        # Validate email IDs (basic validation)
        if len(request.email_ids) > 100:
            raise HTTPException(status_code=400, detail="Too many emails (max 100)")
        
        # Create processing pipeline
        pipeline_id = await job_queue.create_pipeline(request.email_ids, user_id)
        
        # Start worker if not running
        await email_processor_worker.start()
        
        logger.info(f"Started processing pipeline {pipeline_id} for user {user_id} with {len(request.email_ids)} emails")
        
        return {
            "pipeline_id": pipeline_id,
            "status": "started",
            "email_count": len(request.email_ids),
            "message": f"Processing started for {len(request.email_ids)} emails"
        }
        
    except Exception as e:
        logger.error(f"Failed to start processing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@router.get("/processing/{pipeline_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(
    pipeline_id: str
):
    """Get processing pipeline status."""
    try:
        pipeline = await job_queue.get_pipeline(pipeline_id)
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        # Count job statuses
        jobs_completed = sum(1 for job in pipeline.jobs if job.status.value == "completed")
        jobs_failed = sum(1 for job in pipeline.jobs if job.status.value == "failed")
        
        return ProcessingStatusResponse(
            pipeline_id=pipeline.id,
            status=pipeline.status,
            overall_progress=pipeline.overall_progress,
            email_count=len(pipeline.email_ids),
            jobs_completed=jobs_completed,
            jobs_failed=jobs_failed,
            created_at=pipeline.created_at,
            started_at=pipeline.started_at,
            completed_at=pipeline.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing status: {str(e)}")


@router.get("/processing/{pipeline_id}/jobs", response_model=List[JobStatusResponse])
async def get_pipeline_jobs(
    pipeline_id: str
):
    """Get all jobs in a processing pipeline."""
    try:
        pipeline = await job_queue.get_pipeline(pipeline_id)
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        # Check user access
        user_id = str(getattr(current_user, 'id', 'anonymous'))
        if pipeline.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        jobs = []
        for job in pipeline.jobs:
            jobs.append(JobStatusResponse(
                job_id=job.id,
                type=job.type.value,
                email_id=job.email_id,
                status=job.status.value,
                progress_percentage=job.progress.percentage,
                progress_message=job.progress.message,
                error=job.error,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at
            ))
        
        return jobs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pipeline jobs: {str(e)}")


@router.post("/processing/{pipeline_id}/cancel")
async def cancel_processing(
    pipeline_id: str
):
    """Cancel processing pipeline."""
    try:
        pipeline = await job_queue.get_pipeline(pipeline_id)
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        success = await job_queue.cancel_pipeline(pipeline_id)
        
        if success:
            # Broadcast cancellation to WebSocket clients
            await websocket_manager.broadcast_pipeline_status(pipeline_id, {
                "status": "cancelled",
                "message": "Pipeline cancelled by user"
            })
            
            return {"message": "Pipeline cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel pipeline")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel processing: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel processing: {str(e)}")


@router.get("/processing/stats")
async def get_processing_stats():
    """Get processing system statistics."""
    try:
        # Get WebSocket stats
        websocket_stats = await websocket_manager.get_stats()
        
        # Get basic queue stats (would be more detailed with Redis/Celery)
        user_pipelines = job_queue._pipelines.values()
        
        total_pipelines = len(user_pipelines)
        active_pipelines = len([p for p in user_pipelines if p.status == "running"])
        completed_pipelines = len([p for p in user_pipelines if p.status == "completed"])
        
        return {
            "processing_stats": {
                "total_pipelines": total_pipelines,
                "active_pipelines": active_pipelines,
                "completed_pipelines": completed_pipelines,
                "worker_status": "running" if email_processor_worker.is_running else "stopped"
            },
            "websocket_stats": websocket_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get processing stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing stats: {str(e)}")


@router.websocket("/processing/ws/{pipeline_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    pipeline_id: str,
    user_id: str = Query(..., description="User ID for authentication")
):
    """WebSocket endpoint for real-time processing updates."""
    try:
        # Basic authentication check (in production, use proper JWT validation)
        if not user_id:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        # Verify pipeline access
        pipeline = await job_queue.get_pipeline(pipeline_id)
        if not pipeline:
            await websocket.close(code=4004, reason="Pipeline not found")
            return
        
        if pipeline.user_id != user_id:
            await websocket.close(code=4003, reason="Access denied")
            return
        
        # Handle WebSocket connection
        await websocket_manager.handle_connection(websocket, user_id, pipeline_id)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for pipeline {pipeline_id}")
    except Exception as e:
        logger.error(f"WebSocket error for pipeline {pipeline_id}: {e}")
        try:
            await websocket.close(code=4000, reason="Internal error")
        except:
            pass


@router.websocket("/processing/ws")
async def general_websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., description="User ID for authentication")
):
    """General WebSocket endpoint for processing updates."""
    try:
        # Basic authentication check
        if not user_id:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        # Handle WebSocket connection without specific pipeline
        await websocket_manager.handle_connection(websocket, user_id)
        
    except WebSocketDisconnect:
        logger.info(f"General WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"General WebSocket error for user {user_id}: {e}")
        try:
            await websocket.close(code=4000, reason="Internal error")
        except:
            pass