"""
FastAPI error handlers and middleware for consistent error responses.

This module provides centralized error handling for the FastAPI backend,
ensuring consistent error responses and proper logging.
"""

import sys
import logging
from typing import Union, Dict, Any
from pathlib import Path

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.exceptions import (
    EmailHelperError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    AIServiceUnavailableError,
    EmailServiceUnavailableError,
    DatabaseConnectionError,
    DatabaseError,
    EmailNotFoundError,
    TaskNotFoundError,
    ResourceNotAvailableError
)
from utils.error_utils import standardized_error_handler, format_error_for_api

logger = logging.getLogger(__name__)


async def email_helper_error_handler(
    request: Request,
    exc: EmailHelperError
) -> JSONResponse:
    """Handle custom EmailHelper exceptions.
    
    Args:
        request: The FastAPI request
        exc: The EmailHelperError exception
        
    Returns:
        JSONResponse with error details
    """
    # Log the error
    standardized_error_handler(
        operation_name=f"{request.method} {request.url.path}",
        error=exc,
        context={
            'url': str(request.url),
            'method': request.method,
            'client': request.client.host if request.client else None
        }
    )
    
    # Determine HTTP status code based on exception type
    status_code = _get_status_code_for_exception(exc)
    
    # Build response
    response_data = {
        'success': False,
        'error': exc.user_message,
        'error_type': exc.__class__.__name__,
        'recoverable': exc.recoverable
    }
    
    # Include details in debug mode
    if hasattr(request.app.state, 'debug') and request.app.state.debug:
        response_data['details'] = exc.to_dict()
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions with consistent format.
    
    Args:
        request: The FastAPI request
        exc: The HTTP exception
        
    Returns:
        JSONResponse with error details
    """
    logger.warning(
        f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'success': False,
            'error': exc.detail,
            'status_code': exc.status_code
        }
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors.
    
    Args:
        request: The FastAPI request
        exc: The validation error
        
    Returns:
        JSONResponse with validation error details
    """
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field = '.'.join(str(loc) for loc in error['loc'])
        errors.append({
            'field': field,
            'message': error['msg'],
            'type': error['type']
        })
    
    logger.warning(
        f"Validation error on {request.method} {request.url.path}: {len(errors)} errors"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            'success': False,
            'error': 'Invalid request data',
            'validation_errors': errors
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions.
    
    Args:
        request: The FastAPI request
        exc: The exception
        
    Returns:
        JSONResponse with error details
    """
    # Log the full exception
    error_info = standardized_error_handler(
        operation_name=f"{request.method} {request.url.path}",
        error=exc,
        context={
            'url': str(request.url),
            'method': request.method,
            'client': request.client.host if request.client else None
        },
        include_traceback=True
    )
    
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}",
        exc_info=True
    )
    
    # Don't expose internal error details to clients
    response_data = {
        'success': False,
        'error': 'An unexpected error occurred. Please try again.',
        'recoverable': True
    }
    
    # Include details only in debug mode
    if hasattr(request.app.state, 'debug') and request.app.state.debug:
        response_data['details'] = {
            'error_type': type(exc).__name__,
            'message': str(exc)
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


def _get_status_code_for_exception(exc: EmailHelperError) -> int:
    """Map exception types to HTTP status codes.
    
    Args:
        exc: The exception
        
    Returns:
        Appropriate HTTP status code
    """
    # Authentication and authorization
    if isinstance(exc, AuthenticationError):
        return status.HTTP_401_UNAUTHORIZED
    if isinstance(exc, AuthorizationError):
        return status.HTTP_403_FORBIDDEN
    
    # Validation errors
    if isinstance(exc, ValidationError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Not found errors
    if isinstance(exc, (EmailNotFoundError, TaskNotFoundError)):
        return status.HTTP_404_NOT_FOUND
    
    # Rate limiting
    if isinstance(exc, RateLimitError):
        return status.HTTP_429_TOO_MANY_REQUESTS
    
    # Service unavailable
    if isinstance(exc, (
        AIServiceUnavailableError,
        EmailServiceUnavailableError,
        DatabaseConnectionError,
        ResourceNotAvailableError
    )):
        return status.HTTP_503_SERVICE_UNAVAILABLE
    
    # Database errors
    if isinstance(exc, DatabaseError):
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # Default to 500 for other errors
    return status.HTTP_500_INTERNAL_SERVER_ERROR


def register_error_handlers(app) -> None:
    """Register all error handlers with FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Custom exception handlers
    app.add_exception_handler(EmailHelperError, email_helper_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Error handlers registered successfully")


class ErrorHandlingMiddleware:
    """Middleware for additional error handling logic.
    
    This middleware can be used for:
    - Error tracking/monitoring
    - Error metrics collection
    - Custom error logging
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Process request with error tracking."""
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        
        # Track request
        request_path = scope.get('path', '')
        request_method = scope.get('method', '')
        
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            # Log error
            logger.error(
                f"Middleware caught error on {request_method} {request_path}",
                exc_info=True
            )
            # Re-raise to be handled by exception handlers
            raise
