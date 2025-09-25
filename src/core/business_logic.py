"""Consolidated business logic for Email Helper.

This module consolidates various business logic components that were previously
scattered across multiple service files. It provides a cleaner, more maintainable
approach to handling email processing operations.

Key Classes:
- EmailWorkflow: Orchestrates the complete email processing workflow
- UIStateManager: Manages UI state and component coordination
- ProcessingOrchestrator: Handles background processing with progress tracking

This consolidation eliminates duplicate code and provides a more cohesive
architecture for the email helper system.
"""

import threading
import logging
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
import json
import os
from concurrent.futures import ThreadPoolExecutor, Future

from core.base_processor import BaseProcessor
from core.interfaces import EmailProvider, AIProvider, StorageProvider
from utils import *


class EmailWorkflow(BaseProcessor):
    """Orchestrates the complete email processing workflow."""
    
    def __init__(self, email_provider: EmailProvider, ai_provider: AIProvider, 
                 storage_provider: StorageProvider):
        super().__init__("EmailWorkflow")
        self.email_provider = email_provider
        self.ai_provider = ai_provider
        self.storage_provider = storage_provider
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    def process_batch(self, folder_name: str = "Inbox", count: int = 50) -> Future:
        """Process a batch of emails asynchronously."""
        def _process():
            try:
                self.logger.info(f"Starting batch processing: {count} emails from {folder_name}")
                self.reset_cancellation()
                
                # Step 1: Retrieve emails
                self.update_progress(10)
                emails = self.email_provider.get_emails(folder_name, count)
                
                if self.is_cancelled():
                    return self.create_result(False, message="Processing cancelled")
                
                # Step 2: Process each email
                processed_emails = []
                total_emails = len(emails)
                
                for i, email in enumerate(emails):
                    if self.is_cancelled():
                        break
                        
                    progress = 10 + (70 * (i + 1) / total_emails)
                    self.update_progress(int(progress))
                    
                    processed_email = self._process_single_email(email)
                    processed_emails.append(processed_email)
                
                if self.is_cancelled():
                    return self.create_result(False, message="Processing cancelled")
                
                # Step 3: Analyze relationships and priorities
                self.update_progress(85)
                batch_analysis = self.ai_provider.analyze_batch(processed_emails)
                
                # Step 4: Save results
                self.update_progress(95)
                tasks = self._extract_tasks(processed_emails, batch_analysis)
                self.storage_provider.save_tasks(tasks)
                
                self.update_progress(100)
                
                result_data = {
                    'emails': processed_emails,
                    'batch_analysis': batch_analysis,
                    'tasks': tasks,
                    'processed_at': datetime.now().isoformat(),
                    'total_count': len(processed_emails)
                }
                
                self.logger.info(f"Batch processing completed: {len(processed_emails)} emails processed")
                return self.create_result(True, result_data, "Processing completed successfully")
                
            except Exception as e:
                self.logger.error(f"Error in batch processing: {e}")
                return self.create_result(False, message=f"Processing failed: {e}")
        
        return self.executor.submit(_process)
    
    def _process_single_email(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single email with AI analysis."""
        processed = email.copy()
        processed['processed_at'] = datetime.now().isoformat()
        
        try:
            # Get email body if not present
            if 'body' not in processed or not processed['body']:
                body = self.email_provider.get_email_body(email.get('entry_id', ''))
                processed['body'] = body
            
            # AI classification
            ai_result = self.ai_provider.classify_email(processed['body'])
            processed['classification'] = ai_result
            
        except Exception as e:
            self.logger.warning(f"Error processing email {email.get('subject', 'Unknown')}: {e}")
            processed['processing_error'] = str(e)
            
        return processed
    
    def _extract_tasks(self, emails: List[Dict[str, Any]], batch_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract actionable tasks from processed emails."""
        tasks = []
        
        for email in emails:
            classification = email.get('classification', {})
            if classification.get('action_type') in ['required_personal_action', 'team_action']:
                task = {
                    'email_id': email.get('entry_id'),
                    'subject': email.get('subject'),
                    'sender': email.get('sender'),
                    'due_date': classification.get('due_date'),
                    'priority': classification.get('priority', 'medium'),
                    'action_required': classification.get('action_required'),
                    'category': classification.get('action_type'),
                    'created_at': datetime.now().isoformat(),
                    'status': 'outstanding'
                }
                tasks.append(task)
        
        return tasks


class UIStateManager:
    """Manages UI state and component coordination."""
    
    def __init__(self):
        self.state = {}
        self.callbacks = {}
        self.lock = threading.RLock()
        
    def set(self, key: str, value: Any) -> None:
        """Set a state value and notify callbacks."""
        with self.lock:
            old_value = self.state.get(key)
            self.state[key] = value
            
            # Notify specific callbacks
            if key in self.callbacks:
                for callback in self.callbacks[key]:
                    try:
                        callback(key, value, old_value)
                    except Exception as e:
                        logging.error(f"Error in state callback for {key}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        with self.lock:
            return self.state.get(key, default)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple state values at once."""
        for key, value in updates.items():
            self.set(key, value)
    
    def subscribe(self, key: str, callback: Callable[[str, Any, Any], None]) -> None:
        """Subscribe to state changes for a specific key."""
        with self.lock:
            if key not in self.callbacks:
                self.callbacks[key] = []
            self.callbacks[key].append(callback)
    
    def unsubscribe(self, key: str, callback: Callable) -> None:
        """Unsubscribe from state changes."""
        with self.lock:
            if key in self.callbacks and callback in self.callbacks[key]:
                self.callbacks[key].remove(callback)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all state values."""
        with self.lock:
            return self.state.copy()
    
    def clear(self) -> None:
        """Clear all state."""
        with self.lock:
            self.state.clear()


class ProcessingOrchestrator:
    """Handles background processing with progress tracking and coordination."""
    
    def __init__(self, state_manager: UIStateManager):
        self.state_manager = state_manager
        self.active_operations = {}
        self.logger = logging.getLogger(__name__)
        
    def start_operation(self, operation_id: str, operation: Callable, 
                       progress_callback: Optional[Callable] = None) -> Future:
        """Start a background operation with progress tracking."""
        if operation_id in self.active_operations:
            raise ValueError(f"Operation {operation_id} is already running")
        
        def wrapped_operation():
            try:
                self.state_manager.set(f"operation.{operation_id}.status", "running")
                self.state_manager.set(f"operation.{operation_id}.progress", 0)
                
                # Set up progress callback
                if hasattr(operation, 'set_progress_callback') and progress_callback:
                    operation.set_progress_callback(progress_callback)
                
                result = operation()
                
                self.state_manager.set(f"operation.{operation_id}.status", "completed")
                self.state_manager.set(f"operation.{operation_id}.progress", 100)
                self.state_manager.set(f"operation.{operation_id}.result", result)
                
                return result
                
            except Exception as e:
                self.logger.error(f"Error in operation {operation_id}: {e}")
                self.state_manager.set(f"operation.{operation_id}.status", "error")
                self.state_manager.set(f"operation.{operation_id}.error", str(e))
                raise
            finally:
                if operation_id in self.active_operations:
                    del self.active_operations[operation_id]
        
        future = ThreadPoolExecutor(max_workers=1).submit(wrapped_operation)
        self.active_operations[operation_id] = {
            'future': future,
            'operation': operation,
            'started_at': datetime.now()
        }
        
        return future
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel a running operation."""
        if operation_id not in self.active_operations:
            return False
        
        operation_info = self.active_operations[operation_id]
        operation = operation_info['operation']
        
        # Try to cancel the operation gracefully
        if hasattr(operation, 'cancel_operation'):
            operation.cancel_operation()
        
        # Cancel the future
        operation_info['future'].cancel()
        
        self.state_manager.set(f"operation.{operation_id}.status", "cancelled")
        del self.active_operations[operation_id]
        
        return True
    
    def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Get the status of an operation."""
        return {
            'status': self.state_manager.get(f"operation.{operation_id}.status", "unknown"),
            'progress': self.state_manager.get(f"operation.{operation_id}.progress", 0),
            'error': self.state_manager.get(f"operation.{operation_id}.error"),
            'result': self.state_manager.get(f"operation.{operation_id}.result"),
            'is_active': operation_id in self.active_operations
        }
    
    def get_active_operations(self) -> List[str]:
        """Get list of active operation IDs."""
        return list(self.active_operations.keys())
    
    def wait_for_operation(self, operation_id: str, timeout: Optional[float] = None) -> Any:
        """Wait for an operation to complete and return its result."""
        if operation_id not in self.active_operations:
            # Check if we have a cached result
            result = self.state_manager.get(f"operation.{operation_id}.result")
            if result is not None:
                return result
            raise ValueError(f"Operation {operation_id} not found")
        
        future = self.active_operations[operation_id]['future']
        return future.result(timeout=timeout)