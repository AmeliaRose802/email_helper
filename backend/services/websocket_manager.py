"""WebSocket Manager for Real-time Processing Updates.

This module provides WebSocket connection management and real-time broadcasting
of processing status updates, job progress, and pipeline events.
"""

import json
import logging
import asyncio
from typing import Dict, Set, Any, Optional, List
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import asdict

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Pipeline subscriptions: pipeline_id -> set of user_ids
        self.pipeline_subscriptions: Dict[str, Set[str]] = {}
        # User to pipeline mapping for cleanup
        self.user_pipelines: Dict[str, Set[str]] = {}
        
        self.logger.info("WebSocket ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket, user_id: str, pipeline_id: Optional[str] = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        # Add to active connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Subscribe to pipeline if specified
        if pipeline_id:
            await self.subscribe_to_pipeline(user_id, pipeline_id)
        
        self.logger.info(f"WebSocket connected for user {user_id}, pipeline: {pipeline_id}")
        
        # Send connection confirmation
        await self.send_to_user(user_id, {
            "type": "connection_established",
            "user_id": user_id,
            "pipeline_id": pipeline_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Clean up empty connection sets
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # Clean up pipeline subscriptions for this user
                user_pipelines = self.user_pipelines.get(user_id, set()).copy()
                for pipeline_id in user_pipelines:
                    await self.unsubscribe_from_pipeline(user_id, pipeline_id)
        
        self.logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def subscribe_to_pipeline(self, user_id: str, pipeline_id: str):
        """Subscribe user to pipeline updates."""
        if pipeline_id not in self.pipeline_subscriptions:
            self.pipeline_subscriptions[pipeline_id] = set()
        
        self.pipeline_subscriptions[pipeline_id].add(user_id)
        
        if user_id not in self.user_pipelines:
            self.user_pipelines[user_id] = set()
        self.user_pipelines[user_id].add(pipeline_id)
        
        self.logger.debug(f"User {user_id} subscribed to pipeline {pipeline_id}")
    
    async def unsubscribe_from_pipeline(self, user_id: str, pipeline_id: str):
        """Unsubscribe user from pipeline updates."""
        if pipeline_id in self.pipeline_subscriptions:
            self.pipeline_subscriptions[pipeline_id].discard(user_id)
            
            # Clean up empty pipeline subscriptions
            if not self.pipeline_subscriptions[pipeline_id]:
                del self.pipeline_subscriptions[pipeline_id]
        
        if user_id in self.user_pipelines:
            self.user_pipelines[user_id].discard(pipeline_id)
            
            if not self.user_pipelines[user_id]:
                del self.user_pipelines[user_id]
        
        self.logger.debug(f"User {user_id} unsubscribed from pipeline {pipeline_id}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all connections for a specific user."""
        if user_id not in self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected_sockets = []
        
        for websocket in self.active_connections[user_id].copy():
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                self.logger.warning(f"Failed to send message to user {user_id}: {e}")
                disconnected_sockets.append(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected_sockets:
            await self.disconnect(websocket, user_id)
    
    async def broadcast_to_pipeline(self, pipeline_id: str, message: Dict[str, Any]):
        """Broadcast message to all users subscribed to a pipeline."""
        if pipeline_id not in self.pipeline_subscriptions:
            return
        
        message["pipeline_id"] = pipeline_id
        
        for user_id in self.pipeline_subscriptions[pipeline_id].copy():
            await self.send_to_user(user_id, message)
        
        self.logger.debug(f"Broadcast message to pipeline {pipeline_id} subscribers")
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        
        return {
            "total_connections": total_connections,
            "connected_users": len(self.active_connections),
            "active_pipeline_subscriptions": len(self.pipeline_subscriptions),
            "users_with_pipeline_subscriptions": len(self.user_pipelines)
        }


class WebSocketManager:
    """Main WebSocket manager for processing updates."""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.logger = logging.getLogger(__name__)
    
    async def handle_connection(self, websocket: WebSocket, user_id: str, pipeline_id: Optional[str] = None):
        """Handle WebSocket connection lifecycle."""
        await self.connection_manager.connect(websocket, user_id, pipeline_id)
        
        try:
            while True:
                # Listen for client messages
                data = await websocket.receive_text()
                await self.handle_client_message(websocket, user_id, data)
                
        except WebSocketDisconnect:
            self.logger.info(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            self.logger.error(f"WebSocket error for user {user_id}: {e}")
        finally:
            await self.connection_manager.disconnect(websocket, user_id)
    
    async def handle_client_message(self, websocket: WebSocket, user_id: str, message: str):
        """Handle messages from client."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe_pipeline":
                pipeline_id = data.get("pipeline_id")
                if pipeline_id:
                    await self.connection_manager.subscribe_to_pipeline(user_id, pipeline_id)
                    await websocket.send_text(json.dumps({
                        "type": "subscription_confirmed",
                        "pipeline_id": pipeline_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            
            elif message_type == "unsubscribe_pipeline":
                pipeline_id = data.get("pipeline_id")
                if pipeline_id:
                    await self.connection_manager.unsubscribe_from_pipeline(user_id, pipeline_id)
                    await websocket.send_text(json.dumps({
                        "type": "unsubscription_confirmed",
                        "pipeline_id": pipeline_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            
            elif message_type == "cancel_pipeline":
                pipeline_id = data.get("pipeline_id")
                if pipeline_id:
                    # Import here to avoid circular imports
                    from backend.services.job_queue import job_queue
                    await job_queue.cancel_pipeline(pipeline_id)
                    
                    await self.connection_manager.broadcast_to_pipeline(pipeline_id, {
                        "type": "pipeline_cancelled",
                        "pipeline_id": pipeline_id,
                        "user_id": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            elif message_type == "retry_failed_jobs":
                # Handle retry logic
                await websocket.send_text(json.dumps({
                    "type": "retry_initiated",
                    "message": "Retry functionality not yet implemented",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
            elif message_type == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON message from user {user_id}: {message}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.utcnow().isoformat()
            }))
        except Exception as e:
            self.logger.error(f"Error handling client message: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Internal server error",
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def broadcast_job_status(self, job_id: str, status_update: Dict[str, Any]):
        """Broadcast job status update to relevant subscribers."""
        # Add timestamp
        status_update["timestamp"] = datetime.utcnow().isoformat()
        status_update["type"] = "job_status"
        status_update["job_id"] = job_id
        
        # Import here to avoid circular imports
        from backend.services.job_queue import job_queue
        
        job = await job_queue.get_job(job_id)
        if not job:
            return
        
        # Find pipeline containing this job
        for pipeline_id, pipeline in job_queue._pipelines.items():
            if any(j.id == job_id for j in pipeline.jobs):
                await self.connection_manager.broadcast_to_pipeline(pipeline_id, status_update)
                break
    
    async def broadcast_pipeline_status(self, pipeline_id: str, status_update: Dict[str, Any]):
        """Broadcast pipeline status update to subscribers."""
        status_update["timestamp"] = datetime.utcnow().isoformat()
        status_update["type"] = "pipeline_status"
        status_update["pipeline_id"] = pipeline_id
        
        await self.connection_manager.broadcast_to_pipeline(pipeline_id, status_update)
    
    async def send_processing_complete(self, pipeline_id: str, results: Dict[str, Any]):
        """Send processing completion notification."""
        message = {
            "type": "pipeline_complete",
            "pipeline_id": pipeline_id,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.broadcast_to_pipeline(pipeline_id, message)
    
    async def send_processing_error(self, pipeline_id: str, error: str):
        """Send processing error notification."""
        message = {
            "type": "pipeline_error",
            "pipeline_id": pipeline_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.broadcast_to_pipeline(pipeline_id, message)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics."""
        connection_stats = await self.connection_manager.get_connection_stats()
        
        return {
            "websocket_manager": "active",
            "connections": connection_stats,
            "features": {
                "real_time_updates": True,
                "pipeline_subscriptions": True,
                "job_progress_tracking": True,
                "error_notifications": True
            }
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()