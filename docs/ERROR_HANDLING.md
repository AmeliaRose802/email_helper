# Error Handling Guide

This document describes the error handling architecture and patterns used in the Email Helper application.

## Overview

The Email Helper application implements a comprehensive error handling strategy that includes:

- **Custom exception hierarchy** for precise error identification
- **Standardized error handlers** for consistent logging and reporting
- **Error recovery strategies** with automatic retries
- **User-friendly error messages** for better UX
- **Error boundaries** to contain failures
- **Graceful degradation** when services are unavailable

## Exception Hierarchy

All custom exceptions inherit from `EmailHelperError`, the base exception class defined in `src/core/exceptions.py`.

### Base Exception

```python
from core.exceptions import EmailHelperError

class EmailHelperError(Exception):
    """Base exception for all Email Helper errors."""
    
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
```

### Exception Categories

#### AI Processing Errors

- `AIError` - Base class for AI-related errors
- `AIServiceUnavailableError` - AI service is unavailable (recoverable)
- `AIQuotaExceededError` - AI service quota exceeded
- `AIResponseError` - Invalid AI response format (recoverable)
- `AITimeoutError` - AI request timeout (recoverable)

#### Email Service Errors

- `EmailError` - Base class for email-related errors
- `EmailServiceUnavailableError` - Email service unavailable (recoverable)
- `EmailNotFoundError` - Email not found
- `EmailAccessDeniedError` - Access denied to email
- `EmailFolderError` - Email folder operation failed
- `EmailAuthenticationError` - Email authentication failed

#### Database Errors

- `DatabaseError` - Base class for database errors
- `DatabaseConnectionError` - Database connection failed (recoverable)
- `DatabaseIntegrityError` - Database integrity constraint violated
- `DatabaseQueryError` - Database query failed (recoverable)

#### Task Management Errors

- `TaskError` - Base class for task errors
- `TaskNotFoundError` - Task not found
- `TaskValidationError` - Task data validation failed
- `TaskPersistenceError` - Task persistence failed (recoverable)

#### Validation Errors

- `ValidationError` - Input validation failed
- `DataParsingError` - Data parsing failed

## Error Handling Utilities

### Standardized Error Handler

The `standardized_error_handler` function provides consistent error logging and reporting:

```python
from utils.error_utils import standardized_error_handler

try:
    result = process_email(email)
except Exception as e:
    error_info = standardized_error_handler(
        operation_name="Process Email",
        error=e,
        context={'email_id': email.id},
        user_message="Failed to process email"
    )
    return error_info
```

### Decorator Pattern

Use the `@with_error_handling` decorator for automatic error handling:

```python
from utils.error_utils import with_error_handling

@with_error_handling(
    operation_name="Classify Email",
    fallback_value={'category': 'unknown'},
    raise_on_error=False
)
def classify_email(email_content: str) -> dict:
    return ai_service.classify(email_content)
```

### Error Boundary Context Manager

Use error boundaries to contain failures in specific code blocks:

```python
from utils.error_utils import error_boundary

with error_boundary("Database Transaction", raise_on_error=True):
    db.begin_transaction()
    db.insert_email(email)
    db.commit()
```

### Retry Pattern

Automatically retry operations that may fail temporarily:

```python
from utils.error_utils import retry_on_error

@retry_on_error(
    max_retries=3,
    delay_seconds=2.0,
    exponential_backoff=True,
    retry_on=(ConnectionError, AIServiceUnavailableError)
)
def fetch_ai_classification(email: str) -> dict:
    return ai_service.classify(email)
```

### Graceful Degradation

Implement fallback strategies when primary services fail:

```python
from utils.error_utils import graceful_degradation

def get_email_classification(email):
    """Get email classification with fallback to rule-based classifier."""
    classify_func = graceful_degradation(
        primary_func=lambda: ai_service.classify(email),
        fallback_func=lambda: rule_based_classifier(email),
        fallback_value={'category': 'unknown'},
        operation_name='Email Classification'
    )
    return classify_func()
```

### Error Aggregation

Collect multiple errors during batch operations:

```python
from utils.error_utils import ErrorAggregator

aggregator = ErrorAggregator("Batch Email Processing")

for email in emails:
    try:
        process_email(email)
    except Exception as e:
        aggregator.add_error(e, context={'email_id': email.id})

if aggregator.has_errors():
    report = aggregator.get_report()
    logger.error(f"Batch processing completed with {aggregator.error_count()} errors")
```

## FastAPI Error Handling

### Exception Handlers

The backend uses centralized error handlers defined in `backend/core/error_handlers.py`:

- `email_helper_error_handler` - Handles custom `EmailHelperError` exceptions
- `http_exception_handler` - Handles HTTP exceptions
- `validation_error_handler` - Handles request validation errors
- `general_exception_handler` - Catches all unhandled exceptions

### HTTP Status Code Mapping

Exception types are automatically mapped to appropriate HTTP status codes:

- `AuthenticationError` → 401 Unauthorized
- `AuthorizationError` → 403 Forbidden
- `ValidationError` → 422 Unprocessable Entity
- `NotFoundError` → 404 Not Found
- `RateLimitError` → 429 Too Many Requests
- `ServiceUnavailableError` → 503 Service Unavailable
- Other errors → 500 Internal Server Error

### API Error Response Format

All API errors follow a consistent response format:

```json
{
  "success": false,
  "error": "User-friendly error message",
  "error_type": "EmailNotFoundError",
  "recoverable": true,
  "details": {
    "error_type": "EmailNotFoundError",
    "message": "Email with ID abc123 not found",
    "details": {
      "email_id": "abc123"
    }
  }
}
```

## Best Practices

### 1. Use Specific Exceptions

Always use the most specific exception type:

```python
# Good
raise EmailNotFoundError(
    message=f"Email {email_id} not found",
    details={'email_id': email_id}
)

# Bad
raise Exception("Email not found")
```

### 2. Provide Context

Include relevant context in error details:

```python
raise AIResponseError(
    message="Failed to parse AI response",
    details={
        'response_length': len(response),
        'expected_format': 'JSON',
        'actual_format': 'text'
    }
)
```

### 3. Set Recoverable Flag

Indicate whether the operation can be retried:

```python
# Recoverable error
raise AIServiceUnavailableError(
    message="AI service timeout",
    recoverable=True  # User can retry
)

# Non-recoverable error
raise ValidationError(
    message="Invalid email format",
    recoverable=False  # User must fix input
)
```

### 4. Provide User-Friendly Messages

Always set clear, actionable user messages:

```python
raise EmailServiceUnavailableError(
    message="Failed to connect to Outlook",
    user_message="Cannot connect to your email. Please check your internet connection and try again."
)
```

### 5. Log with Context

Use structured logging with context:

```python
from utils.error_utils import log_error_with_context

try:
    result = process_email(email)
except Exception as e:
    log_error_with_context(
        logger,
        error=e,
        operation="Process Email",
        context={'email_id': email.id, 'folder': email.folder}
    )
    raise
```

### 6. Handle Errors at Appropriate Layers

- **Service Layer**: Catch and convert external service errors to custom exceptions
- **API Layer**: Handle exceptions and return formatted responses
- **Business Logic**: Let exceptions bubble up with added context

### 7. Test Error Paths

Always test error handling:

```python
def test_email_not_found_error():
    """Test email not found error handling."""
    with pytest.raises(EmailNotFoundError) as exc_info:
        email_service.get_email("nonexistent_id")
    
    assert exc_info.value.user_message == "Email not found."
    assert not exc_info.value.recoverable
```

## Error Recovery Strategies

### Retry with Exponential Backoff

For transient errors (network issues, service unavailability):

```python
@retry_on_error(max_retries=3, exponential_backoff=True)
def fetch_data_from_service():
    return external_service.get_data()
```

### Circuit Breaker Pattern

Prevent cascading failures by stopping requests to failing services:

```python
# TODO: Implement circuit breaker pattern for external services
```

### Fallback Values

Provide sensible defaults when operations fail:

```python
def get_user_preferences():
    """Get user preferences with fallback to defaults."""
    try:
        return db.get_preferences(user_id)
    except DatabaseError:
        logger.warning("Failed to load preferences, using defaults")
        return DEFAULT_PREFERENCES
```

### Graceful Service Degradation

Continue operating with reduced functionality:

```python
if not ai_service.is_available():
    logger.warning("AI service unavailable, using rule-based classification")
    return rule_based_classifier.classify(email)
```

## Monitoring and Debugging

### Error Logging

All errors are logged with:
- Timestamp
- Operation name
- Error type and message
- Full context
- Stack trace (for unexpected errors)

### Error Reports

Use `ErrorAggregator` to generate comprehensive error reports for batch operations.

### Debug Mode

In debug mode, API responses include full error details and stack traces.

## Migration Guide

### Converting Existing Code

Replace generic error handling:

```python
# Before
try:
    result = process_email(email)
except Exception as e:
    logging.error(f"Error: {e}")
    return None
```

With structured error handling:

```python
# After
from core.exceptions import EmailError
from utils.error_utils import with_error_handling

@with_error_handling(operation_name="Process Email", fallback_value=None)
def process_email(email):
    # ... processing logic ...
    return result
```

## See Also

- [Testing Guide](testing/TESTING_GUIDE.md) - Testing error scenarios
- [Architecture Documentation](ARCHITECTURE.md) - System architecture
- [API Documentation](API.md) - API error responses
