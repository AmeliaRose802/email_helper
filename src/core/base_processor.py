"""Base processor class with common functionality.

This module provides a base class that encapsulates common processing
patterns used across the email helper system. It reduces code duplication
and provides consistent error handling, logging, and operation patterns.

The BaseProcessor provides:
- Standardized error handling with logging
- Common configuration access patterns
- Progress tracking for long operations
- Cancellation support for background tasks
- Consistent operation result formatting

All main processing classes should inherit from BaseProcessor to
ensure consistent behavior and reduce code duplication.
"""

import logging
from typing import Any, Dict, Optional, Callable
from abc import ABC
from utils.error_utils import standardized_error_handler, safe_execute


class BaseProcessor(ABC):
    """Base class for all processor components.
    
    Provides common functionality for error handling, logging,
    configuration access, and operation management.
    """
    
    def __init__(self, logger_name: str = None):
        self.logger = logging.getLogger(logger_name or self.__class__.__name__)
        self._is_cancelled = False
        self._progress_callback: Optional[Callable[[int], None]] = None
        
    def set_progress_callback(self, callback: Callable[[int], None]):
        """Set a callback function for progress updates."""
        self._progress_callback = callback
        
    def update_progress(self, progress: int):
        """Update progress if callback is set."""
        if self._progress_callback:
            self._progress_callback(progress)
            
    def cancel_operation(self):
        """Cancel the current operation."""
        self._is_cancelled = True
        self.logger.info("Operation cancelled by user")
        
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self._is_cancelled
        
    def reset_cancellation(self):
        """Reset cancellation state for new operations."""
        self._is_cancelled = False
        
    def safe_process(self, operation: Callable[[], Any], operation_name: str = "operation") -> Optional[Any]:
        """Execute an operation with standardized error handling."""
        try:
            self.logger.debug(f"Starting {operation_name}")
            result = operation()
            self.logger.debug(f"Completed {operation_name}")
            return result
        except Exception as e:
            from ..utils.error_utils import standardized_error_handler
            error_result = standardized_error_handler(operation_name, e)
            self.logger.error(f"Error in {operation_name}: {e}")
            return error_result
            
    def create_result(self, success: bool, data: Any = None, message: str = "", errors: list = None) -> Dict[str, Any]:
        """Create a standardized result dictionary."""
        return {
            'success': success,
            'data': data,
            'message': message,
            'errors': errors or [],
            'timestamp': logging.Formatter().formatTime(logging.LogRecord(
                name='', level=0, pathname='', lineno=0, msg='', args=(), exc_info=None
            ))
        }