# ADR-002: Dependency Injection Pattern

## Status
**Accepted** (October 2025)

## Context

The Email Helper backend needs to support multiple service implementations with flexible switching:

**Email Providers:**
- COM Provider (local Outlook via Windows COM)
- Graph API Provider (Microsoft Graph API for cloud)
- Mock Provider (testing and development)

**AI Services:**
- COM AI Service (direct Azure OpenAI integration)
- Standard AI Service (with different configuration)
- Mock AI Service (testing)

Key requirements:
1. **Environment-Based Selection**: Choose provider based on configuration (localhost vs. cloud)
2. **Testability**: Easy to inject mocks for testing without real services
3. **Loose Coupling**: API endpoints shouldn't depend on specific implementations
4. **Singleton Behavior**: Reuse expensive resources (connections, credentials)
5. **Graceful Degradation**: Fallback to alternative providers when primary unavailable
6. **Backward Compatibility**: Existing code should work without changes

## Decision

We use **FastAPI's native dependency injection system** with smart provider selection:

```python
# backend/core/dependencies.py

# Singletons for expensive resources
_email_provider_instance: Optional[EmailProvider] = None
_ai_service_instance: Optional[AIService] = None

def get_email_provider() -> EmailProvider:
    """Get appropriate email provider based on configuration.
    
    Priority:
    1. COM provider (if Windows + USE_COM_BACKEND=true)
    2. Graph API provider (if configured)
    3. Mock provider (fallback)
    """
    global _email_provider_instance
    
    if _email_provider_instance is None:
        if settings.use_com_backend:
            try:
                _email_provider_instance = COMEmailProvider()
            except Exception as e:
                logger.warning(f"COM provider failed: {e}")
                # Fall back to next option
        
        if _email_provider_instance is None:
            # Try Graph API, then Mock...
            
    return _email_provider_instance

# Usage in endpoints
@router.get("/emails")
async def get_emails(
    provider: EmailProvider = Depends(get_email_provider)
):
    return provider.get_emails("Inbox", count=50)
```

**Key Design Elements:**

1. **Dependency Functions**: Top-level functions that return service instances
2. **Singleton Pattern**: Cached instances for expensive resources
3. **Smart Selection**: Configuration-based provider selection with fallbacks
4. **FastAPI Integration**: Uses `Depends()` for automatic injection
5. **Reset Mechanism**: `reset_dependencies()` for testing isolation

## Consequences

### Positive

✅ **Loose Coupling**: Endpoints depend on interfaces, not implementations
✅ **Easy Testing**: Can inject mocks via dependency override:
```python
app.dependency_overrides[get_email_provider] = lambda: MockEmailProvider()
```
✅ **Configuration-Driven**: Provider selection based on environment without code changes
✅ **Resource Efficiency**: Singleton pattern reuses expensive connections
✅ **Graceful Degradation**: Automatic fallback when preferred provider unavailable
✅ **Type Safety**: Full type hints and IDE support
✅ **FastAPI Native**: Uses framework's built-in DI, no external libraries
✅ **Backward Compatible**: Existing code works without changes

### Negative

❌ **Global State**: Singleton pattern uses module-level variables
❌ **Test Isolation**: Need explicit `reset_dependencies()` between tests
❌ **Hidden Dependencies**: Provider selection logic not visible at call site
❌ **Initialization Order**: Must ensure dependencies available before first request

### Neutral

⚠️ **Learning Curve**: Team needs to understand FastAPI dependency injection
⚠️ **Documentation**: Requires clear docs on how to add new providers

## Alternatives Considered

### Alternative 1: Manual Instantiation
```python
@router.get("/emails")
async def get_emails():
    provider = COMEmailProvider()  # Direct instantiation
    return provider.get_emails("Inbox")
```

**Rejected because:**
- Hard-coded dependencies
- Impossible to test without real services
- No flexibility for different environments
- Resource inefficiency (new instance per request)

### Alternative 2: Factory Pattern
```python
class EmailProviderFactory:
    @staticmethod
    def create() -> EmailProvider:
        if settings.use_com_backend:
            return COMEmailProvider()
        return GraphAPIProvider()

@router.get("/emails")
async def get_emails():
    provider = EmailProviderFactory.create()
    return provider.get_emails("Inbox")
```

**Rejected because:**
- Doesn't leverage FastAPI's DI system
- Still hard to test (need to mock factory)
- No singleton behavior (new instance per request)
- More boilerplate than FastAPI Depends()

### Alternative 3: Third-Party DI Framework (e.g., dependency-injector)
```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    email_provider = providers.Singleton(
        COMEmailProvider,
        config=config.email
    )
```

**Rejected because:**
- Additional dependency to maintain
- More complex setup and learning curve
- FastAPI's DI is sufficient for our needs
- Over-engineering for current scale

### Alternative 4: Service Locator Pattern
```python
class ServiceLocator:
    _services = {}
    
    @classmethod
    def get_service(cls, name: str):
        return cls._services[name]

provider = ServiceLocator.get_service('email_provider')
```

**Rejected because:**
- Anti-pattern in modern Python
- Runtime errors instead of type checking
- Hidden dependencies
- Harder to test than dependency injection

## Implementation Details

### Provider Registration

Each provider implements a common interface:

```python
# Protocol for type safety
from typing import Protocol

class EmailProvider(Protocol):
    def get_emails(self, folder_name: str, count: int) -> List[Email]:
        ...
    
    def get_folders(self) -> List[Folder]:
        ...
```

Implementations:
- `COMEmailProvider`: Windows Outlook COM interface
- `GraphAPIEmailProvider`: Microsoft Graph API
- `MockEmailProvider`: In-memory test data

### Configuration

Settings control provider selection:

```python
# .env
USE_COM_BACKEND=true           # Enable COM provider
COM_CONNECTION_TIMEOUT=30      # Connection timeout
COM_RETRY_ATTEMPTS=3           # Retry count

# For Graph API
GRAPH_CLIENT_ID=...
GRAPH_CLIENT_SECRET=...
```

### Testing

Test isolation using dependency override:

```python
from fastapi.testclient import TestClient
from backend.core.dependencies import get_email_provider
from backend.tests.mocks import MockEmailProvider

def test_get_emails():
    # Override dependency
    app.dependency_overrides[get_email_provider] = lambda: MockEmailProvider()
    
    client = TestClient(app)
    response = client.get("/emails")
    
    assert response.status_code == 200
    
    # Clean up
    app.dependency_overrides.clear()
```

Or using the reset utility:

```python
from backend.core.dependencies import reset_dependencies

@pytest.fixture(autouse=True)
def reset_deps():
    reset_dependencies()
    yield
    reset_dependencies()
```

### Error Handling

Dependencies raise appropriate HTTP exceptions:

```python
def get_email_provider() -> EmailProvider:
    try:
        return _get_or_create_provider()
    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Email provider unavailable: {str(e)}"
        )
```

### Lifespan Management

Some providers need cleanup:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown - cleanup providers
    if _email_provider_instance:
        await _email_provider_instance.close()
```

## Best Practices

### Adding a New Provider

1. **Implement Interface**: Create class matching EmailProvider protocol
2. **Add to Selection Logic**: Update `get_email_provider()` with new option
3. **Add Configuration**: Add settings for new provider
4. **Write Tests**: Add tests for new provider selection
5. **Document**: Update provider documentation

### Using in Endpoints

```python
# ✅ GOOD: Use dependency injection
@router.get("/emails")
async def get_emails(
    provider: EmailProvider = Depends(get_email_provider)
):
    return provider.get_emails("Inbox")

# ❌ BAD: Direct instantiation
@router.get("/emails")
async def get_emails():
    provider = COMEmailProvider()  # Hard-coded!
    return provider.get_emails("Inbox")
```

### Testing

```python
# ✅ GOOD: Override dependency
app.dependency_overrides[get_email_provider] = lambda: MockEmailProvider()

# ❌ BAD: Mock the module
with patch('backend.services.email_provider.COMEmailProvider'):
    ...  # Fragile, bypasses DI system
```

## Related Decisions

- [ADR-001: Backend/Src Separation](ADR-001-backend-src-separation.md) - Explains how DI adapts shared services
- [ADR-003: Testing Strategy](ADR-003-testing-strategy.md) - How DI enables testing strategy
- [ADR-004: Error Handling Approach](ADR-004-error-handling-approach.md) - How DI handles provider failures

## Future Enhancements

1. **Health Checks**: Add provider health monitoring
2. **Connection Pooling**: Multiple provider instances for concurrency
3. **Circuit Breaker**: Automatic provider switching on repeated failures
4. **Metrics**: Track provider usage and performance
5. **Hot Reload**: Switch providers without restart

## References

- Implementation: `backend/core/dependencies.py`
- Documentation: `backend/core/DEPENDENCY_INJECTION_README.md`
- Tests: `backend/tests/test_dependencies.py` (18/18 passing)
- FastAPI DI Docs: https://fastapi.tiangolo.com/tutorial/dependencies/

## Authors

- Architecture: Development Team
- Implementation: GitHub Copilot (Task T1.3)
- Documentation: GitHub Copilot
- Review: Project Maintainers
