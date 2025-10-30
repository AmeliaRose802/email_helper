"""
Custom exception hierarchy for Email Helper application.

This module defines a comprehensive exception hierarchy that enables:
- Precise error identification and handling
- Consistent error messages across layers
- Error recovery strategies based on exception type
- User-friendly error reporting
"""

from typing import Optional, Dict, Any


# Base exceptions
class EmailHelperError(Exception):
    """Base exception for all Email Helper errors.
    
    All custom exceptions in the application inherit from this base class,
    allowing for consistent error handling and logging patterns.
    
    Attributes:
        message: Human-readable error message
        details: Additional error context for debugging
        user_message: User-friendly message for UI display
        recoverable: Whether the operation can be retried
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recoverable: bool = False
    ):
        self.message = message
        self.details = details or {}
        self.user_message = user_message or self._default_user_message()
        self.recoverable = recoverable
        super().__init__(self.message)
    
    def _default_user_message(self) -> str:
        """Generate default user-friendly message."""
        return "An error occurred. Please try again."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details,
            "recoverable": self.recoverable
        }


# Configuration and initialization errors
class ConfigurationError(EmailHelperError):
    """Raised when configuration is invalid or missing."""
    
    def _default_user_message(self) -> str:
        return "Application configuration error. Please check your settings."


class InitializationError(EmailHelperError):
    """Raised when a component fails to initialize properly."""
    
    def _default_user_message(self) -> str:
        return "Failed to start component. Please restart the application."


# AI and processing errors
class AIError(EmailHelperError):
    """Base class for AI-related errors."""
    pass


class AIServiceUnavailableError(AIError):
    """Raised when AI service is unavailable or not responding."""
    
    def __init__(self, message: str = "AI service unavailable", **kwargs):
        super().__init__(message, recoverable=True, **kwargs)
    
    def _default_user_message(self) -> str:
        return "AI service is temporarily unavailable. Please try again later."


class AIQuotaExceededError(AIError):
    """Raised when AI service quota is exceeded."""
    
    def _default_user_message(self) -> str:
        return "AI service usage limit reached. Please try again later."


class AIResponseError(AIError):
    """Raised when AI response is malformed or invalid."""
    
    def __init__(self, message: str = "Invalid AI response", **kwargs):
        super().__init__(message, recoverable=True, **kwargs)
    
    def _default_user_message(self) -> str:
        return "AI processing error. Please try again."


class AITimeoutError(AIError):
    """Raised when AI service request times out."""
    
    def __init__(self, message: str = "AI request timeout", **kwargs):
        super().__init__(message, recoverable=True, **kwargs)
    
    def _default_user_message(self) -> str:
        return "AI request timed out. Please try again."


# Email service errors
class EmailError(EmailHelperError):
    """Base class for email-related errors."""
    pass


class EmailServiceUnavailableError(EmailError):
    """Raised when email service (Outlook) is unavailable."""
    
    def __init__(self, message: str = "Email service unavailable", **kwargs):
        super().__init__(message, recoverable=True, **kwargs)
    
    def _default_user_message(self) -> str:
        return "Cannot connect to email service. Please check your connection."


class EmailNotFoundError(EmailError):
    """Raised when requested email is not found."""
    
    def _default_user_message(self) -> str:
        return "Email not found."


class EmailAccessDeniedError(EmailError):
    """Raised when access to email is denied."""
    
    def _default_user_message(self) -> str:
        return "Access denied. Please check your permissions."


class EmailFolderError(EmailError):
    """Raised when email folder operations fail."""
    
    def _default_user_message(self) -> str:
        return "Email folder operation failed."


class EmailAuthenticationError(EmailError):
    """Raised when email authentication fails."""
    
    def _default_user_message(self) -> str:
        return "Email authentication failed. Please sign in again."


# Database errors
class DatabaseError(EmailHelperError):
    """Base class for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    
    def __init__(self, message: str = "Database connection failed", **kwargs):
        super().__init__(message, recoverable=True, **kwargs)
    
    def _default_user_message(self) -> str:
        return "Database connection error. Please try again."


class DatabaseIntegrityError(DatabaseError):
    """Raised when database integrity constraint is violated."""
    
    def _default_user_message(self) -> str:
        return "Data integrity error. Please check your input."


class DatabaseQueryError(DatabaseError):
    """Raised when database query fails."""
    
    def __init__(self, message: str = "Database query failed", **kwargs):
        super().__init__(message, recoverable=True, **kwargs)
    
    def _default_user_message(self) -> str:
        return "Database operation failed. Please try again."


# Task management errors
class TaskError(EmailHelperError):
    """Base class for task-related errors."""
    pass


class TaskNotFoundError(TaskError):
    """Raised when requested task is not found."""
    
    def _default_user_message(self) -> str:
        return "Task not found."


class TaskValidationError(TaskError):
    """Raised when task data validation fails."""
    
    def _default_user_message(self) -> str:
        return "Invalid task data. Please check your input."


class TaskPersistenceError(TaskError):
    """Raised when task persistence operations fail."""
    
    def __init__(self, message: str = "Task persistence failed", **kwargs):
        super().__init__(message, recoverable=True, **kwargs)
    
    def _default_user_message(self) -> str:
        return "Failed to save task. Please try again."


# Data validation errors
class ValidationError(EmailHelperError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        kwargs['details'] = details
        super().__init__(message, **kwargs)
    
    def _default_user_message(self) -> str:
        field = self.details.get('field')
        if field:
            return f"Invalid value for {field}."
        return "Invalid input. Please check your data."


class DataParsingError(EmailHelperError):
    """Raised when data parsing fails."""
    
    def _default_user_message(self) -> str:
        return "Failed to parse data. Please check the format."


# Network and external service errors
class NetworkError(EmailHelperError):
    """Raised for network-related errors."""
    
    def __init__(self, message: str = "Network error", **kwargs):
        super().__init__(message, recoverable=True, **kwargs)
    
    def _default_user_message(self) -> str:
        return "Network connection error. Please check your connection."


class ExternalServiceError(EmailHelperError):
    """Raised when external service call fails."""
    
    def __init__(self, service_name: str, message: str, **kwargs):
        details = kwargs.get('details', {})
        details['service'] = service_name
        kwargs['details'] = details
        super().__init__(message, recoverable=True, **kwargs)
    
    def _default_user_message(self) -> str:
        service = self.details.get('service', 'External service')
        return f"{service} is unavailable. Please try again later."


# Rate limiting errors
class RateLimitError(EmailHelperError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None, **kwargs):
        details = kwargs.get('details', {})
        if retry_after:
            details['retry_after'] = retry_after
        kwargs['details'] = details
        super().__init__(message, recoverable=True, **kwargs)
    
    def _default_user_message(self) -> str:
        retry_after = self.details.get('retry_after')
        if retry_after:
            return f"Too many requests. Please wait {retry_after} seconds."
        return "Too many requests. Please try again later."


# File and resource errors
class ResourceError(EmailHelperError):
    """Base class for resource-related errors."""
    pass


class FileNotFoundError(ResourceError):
    """Raised when required file is not found."""
    
    def _default_user_message(self) -> str:
        return "Required file not found."


class FileAccessError(ResourceError):
    """Raised when file access is denied."""
    
    def _default_user_message(self) -> str:
        return "Cannot access file. Please check permissions."


class ResourceNotAvailableError(ResourceError):
    """Raised when required resource is not available."""
    
    def __init__(self, resource_name: str, message: Optional[str] = None, **kwargs):
        msg = message or f"Resource not available: {resource_name}"
        details = kwargs.get('details', {})
        details['resource'] = resource_name
        kwargs['details'] = details
        super().__init__(msg, **kwargs)
    
    def _default_user_message(self) -> str:
        return "Required resource is not available."


# Authentication and authorization errors
class AuthenticationError(EmailHelperError):
    """Raised when authentication fails."""
    
    def _default_user_message(self) -> str:
        return "Authentication failed. Please sign in again."


class AuthorizationError(EmailHelperError):
    """Raised when authorization fails."""
    
    def _default_user_message(self) -> str:
        return "Access denied. You don't have permission for this action."


# Timeout errors
class TimeoutError(EmailHelperError):
    """Raised when operation times out."""
    
    def __init__(self, operation: str, timeout_seconds: Optional[int] = None, **kwargs):
        message = f"Operation timed out: {operation}"
        details = kwargs.get('details', {})
        details['operation'] = operation
        if timeout_seconds:
            details['timeout_seconds'] = timeout_seconds
        kwargs['details'] = details
        super().__init__(message, recoverable=True, **kwargs)
    
    def _default_user_message(self) -> str:
        return "Operation timed out. Please try again."
