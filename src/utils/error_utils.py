"""
Error handling utilities for standardized error management
"""

import logging
import traceback
from typing import Optional, Dict, Any, Callable
from datetime import datetime

# Configure module logger
logger = logging.getLogger(__name__)


def standardized_error_handler(operation_name: str, error: Exception, 
                             context: Optional[Dict[str, Any]] = None,
                             user_message: Optional[str] = None) -> Dict[str, Any]:
    """Standardized error handling pattern for the application.
    
    Args:
        operation_name: Name of the operation that failed
        error: The exception that occurred
        context: Additional context for debugging
        user_message: Custom user-friendly message
        
    Returns:
        Dict with error information for consistent handling
    """
    if context is None:
        context = {}
    
    error_info = {
        'operation': operation_name,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
        'timestamp': datetime.now().isoformat()
    }
    
    # Log the full error with context
    logger.error(f"Error in {operation_name}: {error}", exc_info=True, extra={'context': context})
    
    # Determine user-friendly message
    if user_message:
        friendly_message = user_message
    elif isinstance(error, ConnectionError):
        friendly_message = "Service temporarily unavailable"
    elif isinstance(error, FileNotFoundError):
        friendly_message = "Required file not found"
    elif isinstance(error, ValueError):
        friendly_message = "Invalid data provided"
    else:
        friendly_message = f"Failed to {operation_name.lower()}"
    
    # Return structured error info
    return {
        'success': False,
        'error': friendly_message,
        'details': str(error),
        'error_info': error_info
    }


def safe_execute(operation_name: str, func: Callable, 
                fallback_value: Any = None, **kwargs) -> Any:
    """Safely execute a function with standardized error handling.
    
    Args:
        operation_name: Name of the operation for logging
        func: Function to execute
        fallback_value: Value to return on error
        **kwargs: Arguments to pass to the function
        
    Returns:
        Function result or fallback_value on error
    """
    try:
        return func(**kwargs)
    except Exception as e:
        error_result = standardized_error_handler(operation_name, e, context=kwargs)
        logger.warning(f"Using fallback value for {operation_name}: {fallback_value}")
        return fallback_value


def log_operation_start(operation_name: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log the start of an operation with context."""
    logger.info(f"Starting {operation_name}", extra={'context': context or {}})


def log_operation_success(operation_name: str, result_summary: str = "") -> None:
    """Log successful completion of an operation."""
    logger.info(f"Completed {operation_name}: {result_summary}")


def create_error_report(errors: list, operation_context: str) -> Dict[str, Any]:
    """Create a comprehensive error report for debugging.
    
    Args:
        errors: List of error dictionaries from standardized_error_handler
        operation_context: Context description for the overall operation
        
    Returns:
        Dict containing error report data
    """
    return {
        'report_timestamp': datetime.now().isoformat(),
        'operation_context': operation_context,
        'total_errors': len(errors),
        'error_types': list(set(e.get('error_info', {}).get('error_type', 'Unknown') for e in errors)),
        'errors': errors,
        'summary': f"{len(errors)} errors occurred during {operation_context}"
    }