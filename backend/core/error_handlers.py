"""FastAPI error handlers with consistent responses."""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.core.infrastructure.exceptions import (
    EmailHelperError, ValidationError, AuthenticationError, AuthorizationError,
    RateLimitError, AIServiceUnavailableError, EmailServiceUnavailableError,
    DatabaseConnectionError, DatabaseError, EmailNotFoundError, TaskNotFoundError,
    ResourceNotAvailableError
)
from backend.core.infrastructure.error_utils import standardized_error_handler

logger = logging.getLogger(__name__)

# Status code mapping for exceptions
STATUS_MAP = {
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    (EmailNotFoundError, TaskNotFoundError): status.HTTP_404_NOT_FOUND,
    RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
    (AIServiceUnavailableError, EmailServiceUnavailableError, 
     DatabaseConnectionError, ResourceNotAvailableError): status.HTTP_503_SERVICE_UNAVAILABLE,
    DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
}

def _get_status_code(exc: EmailHelperError) -> int:
    """Map exception to HTTP status code."""
    for exc_types, code in STATUS_MAP.items():
        if isinstance(exc, exc_types if isinstance(exc_types, tuple) else (exc_types,)):
            return code
    return status.HTTP_500_INTERNAL_SERVER_ERROR

def _get_request_context(request: Request) -> dict:
    """Extract request context for logging."""
    return {
        'url': str(request.url),
        'method': request.method,
        'client': request.client.host if request.client else None
    }

async def email_helper_error_handler(request: Request, exc: EmailHelperError) -> JSONResponse:
    """Handle EmailHelper exceptions."""
    standardized_error_handler(
        operation_name=f"{request.method} {request.url.path}",
        error=exc,
        context=_get_request_context(request)
    )
    
    response_data = {
        'success': False,
        'error': exc.user_message,
        'error_type': exc.__class__.__name__,
        'recoverable': exc.recoverable
    }
    
    if hasattr(request.app.state, 'debug') and request.app.state.debug:
        response_data['details'] = exc.to_dict()
    
    return JSONResponse(status_code=_get_status_code(exc), content=response_data)

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={'success': False, 'error': exc.detail, 'status_code': exc.status_code}
    )

async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors."""
    errors = [{
        'field': '.'.join(str(loc) for loc in error['loc']),
        'message': error['msg'],
        'type': error['type']
    } for error in exc.errors()]
    
    logger.warning(f"Validation error on {request.method} {request.url.path}: {len(errors)} errors")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={'success': False, 'error': 'Invalid request data', 'validation_errors': errors}
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    standardized_error_handler(
        operation_name=f"{request.method} {request.url.path}",
        error=exc,
        context=_get_request_context(request),
        include_traceback=True
    )
    
    logger.error(f"Unhandled exception on {request.method} {request.url.path}", exc_info=True)
    
    response_data = {'success': False, 'error': 'An unexpected error occurred. Please try again.', 'recoverable': True}
    
    if hasattr(request.app.state, 'debug') and request.app.state.debug:
        response_data['details'] = {'error_type': type(exc).__name__, 'message': str(exc)}
    
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response_data)


def register_error_handlers(app) -> None:
    """Register error handlers with FastAPI app."""
    app.add_exception_handler(EmailHelperError, email_helper_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    logger.info("Error handlers registered")

class ErrorHandlingMiddleware:
    """Middleware for error tracking and logging."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            logger.error(
                f"Middleware error on {scope.get('method', '')} {scope.get('path', '')}",
                exc_info=True
            )
            raise
