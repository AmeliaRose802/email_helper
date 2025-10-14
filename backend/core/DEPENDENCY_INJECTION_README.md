# Dependency Injection System for COM Adapters

## Overview

This document describes the dependency injection (DI) system implemented for Task T1.3, which wires COM email provider and AI service adapters into the FastAPI dependency injection pattern.

## Architecture

### Components

```
backend/core/dependencies.py
├── get_com_email_provider()     # Direct COM email provider DI
├── get_com_ai_service()         # Direct COM AI service DI
├── get_email_provider()         # Smart provider selection
├── get_ai_service()             # Smart service selection
└── reset_dependencies()         # Test utility
```

### Configuration

```
backend/core/config.py
└── Settings
    ├── use_com_backend: bool           # Enable COM adapters
    ├── com_connection_timeout: int     # Connection timeout (30s)
    └── com_retry_attempts: int         # Retry attempts (3)
```

### API Integration

```
backend/api/emails.py    # Uses get_email_provider()
backend/api/ai.py        # Uses get_ai_service()
```

## Features

### 1. Configuration-Based Provider Selection

The system automatically selects the appropriate provider based on configuration:

**Priority Order (Email Provider):**
1. COM provider (if `use_com_backend=True` and Windows + Outlook available)
2. Graph API provider (if Microsoft Graph credentials configured)
3. Mock provider (for development/testing)

**Priority Order (AI Service):**
1. COM AI service (if `use_com_backend=True` and AI dependencies available)
2. Standard AI service (fallback)

### 2. Singleton Pattern

Each dependency maintains a single instance throughout the application lifecycle:
- Reduces resource usage
- Maintains connection state
- Improves performance

### 3. Error Handling

Comprehensive error handling with appropriate HTTP status codes:
- `503 Service Unavailable` - Provider/service initialization fails
- `401 Unauthorized` - Authentication/connection fails
- Automatic fallback to alternative providers when available

### 4. Backward Compatibility

All existing endpoints continue to work without modification:
- No breaking changes to existing API contracts
- Existing tests pass without changes
- Gradual migration path supported

## Usage

### Configuration

#### Environment Variables (.env)

```bash
# Enable COM backend
USE_COM_BACKEND=true

# COM adapter settings
COM_CONNECTION_TIMEOUT=30
COM_RETRY_ATTEMPTS=3
```

#### Python Settings

```python
from backend.core.config import Settings

class Settings(BaseSettings):
    use_com_backend: bool = True
    com_connection_timeout: int = 30
    com_retry_attempts: int = 3
```

### API Endpoints

#### Email Endpoints

```python
from fastapi import APIRouter, Depends
from backend.core.dependencies import get_email_provider

router = APIRouter()

@router.get("/emails")
async def get_emails(
    folder: str = "Inbox",
    provider = Depends(get_email_provider)
):
    """Get emails using configured provider (COM or standard)."""
    return provider.get_emails(folder_name=folder, count=50)

@router.get("/folders")
async def get_folders(provider = Depends(get_email_provider)):
    """Get folders using configured provider."""
    return provider.get_folders()
```

#### AI Endpoints

```python
from fastapi import APIRouter, Depends
from backend.core.dependencies import get_ai_service

router = APIRouter()

@router.post("/classify")
async def classify_email(
    email_content: str,
    service = Depends(get_ai_service)
):
    """Classify email using configured service (COM or standard)."""
    result = await service.classify_email(email_content)
    return result

@router.post("/action-items")
async def extract_action_items(
    email_content: str,
    service = Depends(get_ai_service)
):
    """Extract action items using configured service."""
    result = await service.extract_action_items(email_content)
    return result
```

### Direct COM Access

For scenarios requiring explicit COM provider usage:

```python
from backend.core.dependencies import get_com_email_provider, get_com_ai_service

@router.post("/com-only/classify")
async def classify_with_com(
    email_content: str,
    service = Depends(get_com_ai_service)
):
    """Force COM AI service usage."""
    return await service.classify_email(email_content)
```

## Testing

### Unit Tests

```bash
# Run all dependency injection tests
pytest backend/tests/test_dependencies.py -v

# Results: 18/18 tests passing
# - COM email provider tests: 5/5 ✅
# - COM AI service tests: 4/4 ✅
# - Provider selection tests: 4/4 ✅
# - Service selection tests: 4/4 ✅
# - Reset functionality: 1/1 ✅
```

### Integration Tests

```bash
# Run API integration tests
pytest backend/tests/test_di_integration.py -v

# Tests cover:
# - Email endpoints with DI
# - AI endpoints with DI
# - Error handling
# - Backward compatibility
```

### Test Utilities

For testing with dependency injection:

```python
from backend.core.dependencies import reset_dependencies

def test_something():
    """Test that uses dependencies."""
    # Reset to clean state
    reset_dependencies()
    
    # Your test code here
    provider = get_email_provider()
    
    # Clean up after test
    reset_dependencies()
```

## Error Handling

### Common Errors

#### 1. COM Provider Not Available

**Scenario:** Windows or pywin32 not available

**Response:**
```json
{
  "status_code": 503,
  "detail": "COM email provider not available. Requires Windows and pywin32."
}
```

**Solution:** Falls back to Graph API or Mock provider automatically

#### 2. Authentication Failure

**Scenario:** Cannot connect to Outlook

**Response:**
```json
{
  "status_code": 503,
  "detail": "Failed to connect to Outlook COM interface"
}
```

**Solution:** Ensure Outlook is running and accessible

#### 3. AI Service Initialization Failure

**Scenario:** AI dependencies missing or Azure config invalid

**Response:**
```json
{
  "status_code": 503,
  "detail": "COM AI service initialization failed: [error details]"
}
```

**Solution:** Check Azure OpenAI configuration and dependencies

### Fallback Behavior

The system gracefully falls back to alternative providers:

```
get_email_provider() flow:
1. Try COM provider (if configured)
   └─ Fail → Log warning
2. Try Graph API provider (if configured)
   └─ Fail → Log warning
3. Use Mock provider (always available)
   └─ Success → Return instance
```

## Performance Considerations

### Singleton Benefits

- **Memory:** Single instance per provider/service
- **Connections:** Reused COM connections
- **Initialization:** One-time setup cost

### Lazy Initialization

- COM AI service initializes on first use
- Reduces startup time
- Minimizes resource usage when not needed

### Connection Pooling

COM providers maintain persistent connections:
- Outlook connection stays open
- Reduces per-request overhead
- Better performance for multiple operations

## Migration Guide

### From Direct Imports

**Before:**
```python
from backend.services.email_provider import get_email_provider

@router.get("/emails")
async def get_emails(provider = Depends(get_email_provider)):
    return provider.get_emails("Inbox")
```

**After:**
```python
from backend.core.dependencies import get_email_provider

@router.get("/emails")
async def get_emails(provider = Depends(get_email_provider)):
    return provider.get_emails("Inbox")  # Same usage, just different import
```

### From Direct Service Usage

**Before:**
```python
from backend.services.ai_service import AIService

service = AIService()
result = await service.classify_email_async(...)
```

**After:**
```python
from backend.core.dependencies import get_ai_service

service = get_ai_service()  # Gets configured service
result = await service.classify_email_async(...)
```

## Troubleshooting

### Issue: Provider/Service Always Uses Mock

**Symptoms:**
- Expected COM provider but getting mock data
- Configuration seems correct but not applied

**Solutions:**
1. Verify `USE_COM_BACKEND=true` in .env file
2. Check settings are being loaded: `print(settings.use_com_backend)`
3. Ensure pywin32 is installed on Windows
4. Verify Outlook is running

### Issue: Singleton State Persists Between Tests

**Symptoms:**
- Tests interfere with each other
- Unexpected provider instances in tests

**Solution:**
```python
from backend.core.dependencies import reset_dependencies

@pytest.fixture(autouse=True)
def reset_deps():
    reset_dependencies()
    yield
    reset_dependencies()
```

### Issue: Import Errors

**Symptoms:**
```
ImportError: No module named 'backend.services.com_email_provider'
```

**Solutions:**
1. Verify COM adapter files exist
2. Check Python path includes project root
3. Ensure all dependencies installed

## Security Considerations

### COM Provider Security

- COM connections use Windows authentication
- No credentials stored in code
- Outlook security applies to all operations

### Configuration Security

- Sensitive settings in environment variables
- Never commit .env files
- Use secure credential storage for production

## Future Enhancements

Potential improvements for future tasks:

1. **Connection Pooling:** Multiple COM connections for concurrent requests
2. **Health Checks:** Background health monitoring for providers
3. **Metrics:** Track provider usage and performance
4. **Caching:** Redis-based caching layer for frequently accessed data
5. **Retry Logic:** Configurable retry with exponential backoff
6. **Multi-Profile:** Support for multiple Outlook profiles

## Related Documentation

- [COM Email Provider README](../services/COM_EMAIL_PROVIDER_README.md)
- [COM AI Service Documentation](../../docs/COM_AI_SERVICE_ADAPTER.md)
- [Adapter Pattern Implementation](../../docs/implementation/ADAPTER_PATTERN_IMPLEMENTATION.md)
- [Backend API Specification](../../specs/backend/)

## Authors

- Implementation: GitHub Copilot
- Task: T1.3 - Update API Dependencies
- Date: October 14, 2025
- Related Tasks: T1.1 (COM Email Provider), T1.2 (COM AI Service)

## Changelog

- **2025-10-14**: Initial dependency injection system implementation
- **2025-10-14**: Unit tests created and verified (18/18 passing)
- **2025-10-14**: Integration tests and backward compatibility verified
- **2025-10-14**: Documentation completed
