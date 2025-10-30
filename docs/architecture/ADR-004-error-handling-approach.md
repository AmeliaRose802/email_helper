# ADR-004: Error Handling Approach

## Status
**Accepted** (October 2025)

## Context

Email Helper integrates with multiple external services and handles various error scenarios:

**External Dependencies:**
- Microsoft Outlook (COM interface)
- Azure OpenAI (AI processing)
- SQLite Database (data persistence)
- Microsoft Graph API (cloud email access)
- File System (configuration, logs)

**Error Scenarios:**
- Outlook not running or accessible
- Azure OpenAI rate limits or API failures
- Database connection failures
- Network connectivity issues
- Invalid user input
- Resource exhaustion (memory, disk)
- Configuration errors

**User Experience Goals:**
- **Resilient**: Application continues working when possible
- **Informative**: Clear error messages for users
- **Recoverable**: Automatic retry and fallback mechanisms
- **Debuggable**: Detailed logging for troubleshooting
- **Consistent**: Uniform error handling across codebase

**Technical Goals:**
- **Type-Safe**: Typed error responses
- **Testable**: Easy to test error scenarios
- **Maintainable**: Centralized error handling logic
- **Performant**: Minimal overhead in happy path

## Decision

We implement a **layered error handling strategy** with graceful degradation:

### Error Hierarchy

```python
# Custom exception hierarchy
class EmailHelperError(Exception):
    """Base exception for all Email Helper errors."""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class ServiceError(EmailHelperError):
    """Error from external service."""
    pass

class OutlookError(ServiceError):
    """Outlook-specific error."""
    pass

class AIServiceError(ServiceError):
    """AI service error."""
    pass

class DatabaseError(ServiceError):
    """Database operation error."""
    pass

class ValidationError(EmailHelperError):
    """Input validation error."""
    pass

class ConfigurationError(EmailHelperError):
    """Configuration error."""
    pass
```

### Graceful Degradation Strategy

**Priority 1: Keep Application Running**
```python
def get_email_provider() -> EmailProvider:
    """Get email provider with fallback chain."""
    # Try COM provider
    if settings.use_com_backend:
        try:
            return COMEmailProvider()
        except OutlookError as e:
            logger.warning(f"COM provider failed, trying fallback: {e}")
    
    # Try Graph API provider
    if settings.graph_configured:
        try:
            return GraphAPIProvider()
        except ServiceError as e:
            logger.warning(f"Graph API failed, using mock: {e}")
    
    # Fall back to mock provider
    logger.info("Using mock provider for development")
    return MockEmailProvider()
```

**Priority 2: Retry with Exponential Backoff**
```python
def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0
) -> Any:
    """Retry function with exponential backoff.
    
    Args:
        func: Function to retry
        max_attempts: Maximum retry attempts
        base_delay: Base delay in seconds
    
    Returns:
        Result from successful function call
    
    Raises:
        Last exception if all attempts fail
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return func()
        except (ConnectionError, TimeoutError) as e:
            last_exception = e
            if attempt < max_attempts - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
    
    raise last_exception

# Usage
result = retry_with_backoff(
    lambda: ai_client.classify(email),
    max_attempts=3,
    base_delay=1.0
)
```

### API Error Responses

**Consistent Error Format:**
```python
# Pydantic model for error responses
class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    request_id: Optional[str] = None

# FastAPI exception handler
@app.exception_handler(EmailHelperError)
async def email_helper_error_handler(
    request: Request,
    exc: EmailHelperError
) -> JSONResponse:
    """Handle Email Helper exceptions."""
    error_response = ErrorResponse(
        error=exc.message,
        error_code=exc.__class__.__name__,
        details=exc.details,
        timestamp=datetime.utcnow(),
        request_id=request.state.request_id
    )
    
    # Log error with context
    logger.error(
        f"Error handling request {request.url}: {exc}",
        extra={
            "request_id": request.state.request_id,
            "error_type": type(exc).__name__,
            "details": exc.details
        }
    )
    
    # Map to appropriate HTTP status
    status_code = {
        ValidationError: 400,
        ServiceError: 503,
        OutlookError: 503,
        AIServiceError: 503,
        DatabaseError: 500,
        ConfigurationError: 500,
    }.get(type(exc), 500)
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump()
    )
```

### Logging Strategy

**Structured Logging with Context:**
```python
import logging
import json
from datetime import datetime

class ContextLogger:
    """Logger with contextual information."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def error(self, message: str, exc: Exception = None, **context):
        """Log error with context."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "message": message,
            "exception": str(exc) if exc else None,
            "exception_type": type(exc).__name__ if exc else None,
            **context
        }
        
        self.logger.error(json.dumps(log_data))
        
        # Log stack trace separately for readability
        if exc:
            self.logger.exception(exc)

# Usage
logger = ContextLogger(__name__)

try:
    result = process_email(email)
except OutlookError as e:
    logger.error(
        "Failed to process email",
        exc=e,
        email_id=email.id,
        folder=email.folder,
        attempt_count=attempts
    )
```

### User-Facing Error Messages

**Clear, Actionable Messages:**
```python
# Error message mapping
ERROR_MESSAGES = {
    "outlook_not_running": {
        "user_message": "Outlook is not running. Please open Outlook and try again.",
        "actions": [
            "Open Microsoft Outlook",
            "Ensure you're logged in to your email account",
            "Try again"
        ]
    },
    "ai_service_unavailable": {
        "user_message": "AI service is temporarily unavailable. Emails will be classified when service returns.",
        "actions": [
            "Your emails are still being fetched",
            "Classification will happen automatically when service is available",
            "You can manually classify emails if needed"
        ]
    },
    "database_error": {
        "user_message": "Error saving data. Your work may not be saved.",
        "actions": [
            "Check disk space",
            "Restart the application",
            "Contact support if problem persists"
        ]
    }
}

def get_user_error_message(error_code: str) -> Dict[str, Any]:
    """Get user-friendly error message."""
    return ERROR_MESSAGES.get(
        error_code,
        {
            "user_message": "An unexpected error occurred.",
            "actions": [
                "Try again",
                "Check logs for details",
                "Contact support if problem persists"
            ]
        }
    )
```

## Consequences

### Positive

✅ **Resilient**: Application continues working with degraded functionality
✅ **User-Friendly**: Clear error messages guide users to solutions
✅ **Debuggable**: Comprehensive logging aids troubleshooting
✅ **Testable**: Easy to test error scenarios with custom exceptions
✅ **Consistent**: Uniform error handling across all layers
✅ **Type-Safe**: Typed exceptions and error responses
✅ **Recoverable**: Automatic retry and fallback mechanisms
✅ **Maintainable**: Centralized error handling logic

### Negative

❌ **Complexity**: Multiple error handling layers add complexity
❌ **Fallback Limitations**: Mock providers may not fully replace real services
❌ **Silent Failures**: Graceful degradation might hide issues
❌ **Performance**: Retry logic adds latency on failures
❌ **Logging Volume**: Verbose logging can be overwhelming

### Neutral

⚠️ **Error Message Maintenance**: Need to keep error messages updated
⚠️ **Monitoring Requirements**: Need monitoring to detect degraded service
⚠️ **Testing Burden**: Must test all error paths thoroughly

## Alternatives Considered

### Alternative 1: Let It Crash (Erlang Style)
```python
# No error handling, let exceptions propagate
def process_email(email):
    ai_result = ai_client.classify(email)  # Might fail
    db.save(ai_result)  # Might fail
    return ai_result
```

**Rejected because:**
- Poor user experience (app crashes)
- No graceful degradation
- Lost work on failures
- Not suitable for desktop/web app

### Alternative 2: Return Error Codes
```python
def process_email(email) -> Tuple[Optional[Result], int]:
    """Return (result, error_code)."""
    try:
        result = ai_client.classify(email)
        return result, 0
    except Exception:
        return None, ERROR_AI_FAILED
```

**Rejected because:**
- Not Pythonic (exceptions are the Python way)
- Easy to ignore error codes
- Type safety issues
- Verbose call sites

### Alternative 3: Result Type (Rust Style)
```python
from typing import Union

Result = Union[Ok[T], Err[E]]

def process_email(email) -> Result[Classification, Error]:
    try:
        result = ai_client.classify(email)
        return Ok(result)
    except Exception as e:
        return Err(e)
```

**Rejected because:**
- Not idiomatic Python
- Requires library or custom implementation
- More complex than exceptions
- Python exceptions work well

### Alternative 4: No Retries, Immediate Failure
```python
# Fail immediately on first error
def process_email(email):
    result = ai_client.classify(email)  # Fails on transient error
    return result
```

**Rejected because:**
- Poor resilience
- Doesn't handle transient failures
- Bad user experience
- External services have transient issues

## Implementation Details

### Error Recovery Strategies

**1. Circuit Breaker Pattern (Future Enhancement)**
```python
class CircuitBreaker:
    """Prevent repeated calls to failing service."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func: Callable) -> Any:
        """Call function through circuit breaker."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise ServiceUnavailableError("Circuit breaker open")
        
        try:
            result = func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
```

**2. Bulkhead Pattern**
```python
# Isolate resources to prevent cascade failures
class ResourcePool:
    """Limited resource pool for external services."""
    
    def __init__(self, max_connections: int = 10):
        self.semaphore = asyncio.Semaphore(max_connections)
    
    async def execute(self, func: Callable):
        """Execute with resource limiting."""
        async with self.semaphore:
            return await func()
```

### Error Context Propagation

```python
import contextvars

# Context variable for request tracking
request_context = contextvars.ContextVar('request_context', default={})

@app.middleware("http")
async def add_request_context(request: Request, call_next):
    """Add context to all log messages in request."""
    context = {
        "request_id": str(uuid.uuid4()),
        "path": request.url.path,
        "method": request.method,
        "client_ip": request.client.host
    }
    
    token = request_context.set(context)
    try:
        response = await call_next(request)
        return response
    finally:
        request_context.reset(token)

# Logging includes context automatically
def log_error(message: str):
    context = request_context.get()
    logger.error(f"{message} - Context: {context}")
```

### Testing Error Scenarios

```python
@pytest.mark.unit
def test_outlook_connection_failure():
    """Test handling of Outlook connection failure."""
    with patch('src.outlook_manager.win32com') as mock_com:
        mock_com.Dispatch.side_effect = Exception("Outlook not running")
        
        # Should fall back to Graph API
        provider = get_email_provider()
        assert isinstance(provider, GraphAPIProvider)

@pytest.mark.integration
def test_retry_on_transient_failure():
    """Test retry logic on transient failures."""
    mock_func = Mock(side_effect=[
        ConnectionError("Timeout"),
        ConnectionError("Timeout"),
        {"success": True}  # Third attempt succeeds
    ])
    
    result = retry_with_backoff(mock_func, max_attempts=3)
    
    assert result == {"success": True}
    assert mock_func.call_count == 3
```

## Best Practices

### Error Handling Guidelines

```python
# ✅ GOOD: Specific exception handling
try:
    email = outlook.get_email(id)
except OutlookError as e:
    logger.error(f"Outlook error: {e}")
    return fallback_email_source()
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    return cached_email()

# ❌ BAD: Bare except
try:
    email = outlook.get_email(id)
except:  # Catches everything, including KeyboardInterrupt!
    pass

# ✅ GOOD: Error context
try:
    result = process_batch(emails)
except ProcessingError as e:
    logger.error(
        f"Failed to process batch",
        exc=e,
        batch_size=len(emails),
        batch_id=batch_id
    )
    raise

# ❌ BAD: Silent failure
try:
    result = process_batch(emails)
except:
    pass  # Error is hidden!
```

### Logging Guidelines

```python
# ✅ GOOD: Structured logging with context
logger.error(
    "Email classification failed",
    extra={
        "email_id": email.id,
        "subject": email.subject[:50],
        "error_type": type(e).__name__,
        "retry_count": retries
    }
)

# ❌ BAD: String concatenation
logger.error("Email " + str(email.id) + " failed: " + str(e))

# ✅ GOOD: Appropriate log levels
logger.debug("Starting email processing")  # Verbose
logger.info("Processed 50 emails")  # Normal operations
logger.warning("AI service slow, took 10s")  # Potential issue
logger.error("Failed to save to database")  # Error needs attention
logger.critical("Database connection lost")  # System-level failure

# ❌ BAD: Everything is an error
logger.error("Starting email processing")  # Should be debug/info
```

## Related Decisions

- [ADR-002: Dependency Injection Pattern](ADR-002-dependency-injection-pattern.md) - DI enables fallback providers
- [ADR-003: Testing Strategy](ADR-003-testing-strategy.md) - Testing error scenarios

## Future Enhancements

1. **Circuit Breaker**: Implement circuit breaker for external services
2. **Health Checks**: Regular health checks for all services
3. **Metrics**: Track error rates and types
4. **Alerting**: Alert on high error rates
5. **Dead Letter Queue**: Store failed operations for retry
6. **Error Budgets**: SLO-based error budgets

## References

- Implementation: `src/core/errors.py`, `backend/api/error_handlers.py`
- Logging: `src/core/logging.py`
- Tests: `test/unit/test_error_handling.py`
- Python Exceptions: https://docs.python.org/3/tutorial/errors.html

## Authors

- Architecture: Development Team
- Documentation: GitHub Copilot
- Review: Project Maintainers
