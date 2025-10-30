# Dependency Injection Guide

## Overview

This codebase now uses dependency injection throughout, making it easier to test, maintain, and extend. Services declare their dependencies via constructor parameters instead of creating them internally or using global variables.

## Core Interfaces

All major components implement interfaces defined in `src/core/interfaces.py`:

- `OutlookManagerInterface` - Outlook COM operations
- `TaskPersistenceInterface` - Task storage and lifecycle
- `DatabaseManagerInterface` - Database connections
- `EmailProvider` - Email access abstraction
- `AIProvider` - AI processing abstraction
- `StorageProvider` - Generic storage abstraction

## Using the ServiceFactory

The `ServiceFactory` is the recommended way to obtain service instances:

```python
from src.core.service_factory import ServiceFactory

# Create factory
factory = ServiceFactory()

# Get services with proper dependencies injected
outlook_manager = factory.get_outlook_manager()
task_persistence = factory.get_task_persistence()
database_manager = factory.get_database_manager()
```

## Constructor Injection Pattern

Services now accept their dependencies via constructors:

### Example: TaskService

```python
from src.core.interfaces import TaskPersistenceInterface, DatabaseManagerInterface

class TaskService:
    def __init__(
        self, 
        task_persistence: Optional[TaskPersistenceInterface] = None,
        database_manager: Optional[DatabaseManagerInterface] = None
    ):
        # Use injected dependencies or fall back to defaults
        self.task_persistence = task_persistence or TaskPersistence()
        self.database_manager = database_manager or db_manager
```

### Example: COMEmailProvider

```python
from adapters.outlook_email_adapter import OutlookEmailAdapter

class COMEmailProvider(EmailProvider):
    def __init__(self, outlook_adapter: Optional[OutlookEmailAdapter] = None):
        self.adapter = outlook_adapter or OutlookEmailAdapter()
```

## Testing with Mock Implementations

The `src/core/mock_services.py` module provides mock implementations for all interfaces:

```python
from src.core.mock_services import MockOutlookManager, MockTaskPersistence
from src.core.service_factory import ServiceFactory

# In your test setup
factory = ServiceFactory()
factory.override_service('outlook_manager', MockOutlookManager())
factory.override_service('task_persistence', MockTaskPersistence())

# Now all services created by factory use mocks
outlook = factory.get_outlook_manager()  # Returns MockOutlookManager
```

### Writing Tests with Dependency Injection

```python
import pytest
from src.core.mock_services import MockTaskPersistence, MockDatabaseManager
from backend.services.task_service import TaskService

def test_task_creation():
    # Create mock dependencies
    mock_persistence = MockTaskPersistence()
    mock_db = MockDatabaseManager()
    
    # Inject mocks into service
    service = TaskService(
        task_persistence=mock_persistence,
        database_manager=mock_db
    )
    
    # Test without real Outlook or database
    task = service.create_task(task_data, user_id=1)
    assert task.title == "Test Task"
```

## Benefits of This Approach

1. **Testability**: Easy to inject mocks and test components in isolation
2. **Flexibility**: Swap implementations without changing dependent code
3. **Clear Dependencies**: Constructor parameters show what each service needs
4. **No Globals**: Reduced reliance on global state and singletons
5. **Easier Debugging**: Clear dependency graphs make issues easier to trace

## Migration Strategy

When updating existing code:

1. **Add interface implementations** to your classes
2. **Add constructor parameters** for dependencies
3. **Use optional parameters** with defaults for backward compatibility
4. **Update callers gradually** to pass dependencies explicitly
5. **Write tests** using mock implementations

## Example: Before and After

### Before (Tight Coupling)
```python
class EmailProcessor:
    def __init__(self):
        self.outlook = OutlookManager()  # Hard-coded dependency
        self.outlook.connect_to_outlook()
```

### After (Dependency Injection)
```python
class EmailProcessor:
    def __init__(self, outlook_manager: Optional[OutlookManagerInterface] = None):
        # Accept dependency via constructor
        self.outlook = outlook_manager or OutlookManager()
        if not outlook_manager:
            self.outlook.connect_to_outlook()
```

### Using in Tests
```python
def test_email_processor():
    mock_outlook = MockOutlookManager()
    mock_outlook.emails = [create_mock_email()]
    
    processor = EmailProcessor(outlook_manager=mock_outlook)
    result = processor.process_emails()
    
    assert len(result) == 1
    assert mock_outlook.connected
```

## ServiceFactory Features

### Basic Usage
```python
factory = ServiceFactory()
ai_processor = factory.get_ai_processor()
```

### Custom Configuration
```python
config = {'storage_dir': '/custom/path'}
factory = ServiceFactory(config)
task_persistence = factory.get_task_persistence(storage_dir='/custom/path')
```

### Override for Testing
```python
factory.override_service('outlook_manager', MockOutlookManager())
```

### Reset Between Tests
```python
factory.reset()  # Clears all cached instances
```

### Check Service Existence
```python
if factory.has_service('outlook_manager'):
    outlook = factory.get_outlook_manager()
```

## Best Practices

1. **Always use interfaces** in type hints, not concrete classes
2. **Provide optional parameters** with sensible defaults
3. **Don't create dependencies** inside methods - accept them
4. **Use ServiceFactory** for production code
5. **Use direct injection** in tests
6. **Keep interfaces focused** - single responsibility
7. **Document dependencies** in constructor docstrings

## Common Patterns

### Pattern: Service with Multiple Dependencies
```python
class EmailClassifier:
    def __init__(
        self,
        ai_processor: Optional[AIProvider] = None,
        task_persistence: Optional[TaskPersistenceInterface] = None,
        outlook_manager: Optional[OutlookManagerInterface] = None
    ):
        self.ai = ai_processor or AIProcessor()
        self.persistence = task_persistence or TaskPersistence()
        self.outlook = outlook_manager or OutlookManager()
```

### Pattern: Factory Method for Complex Setup
```python
@classmethod
def create_with_mocks(cls):
    """Factory method for creating instance with all mock dependencies."""
    return cls(
        ai_processor=MockAIProcessor(),
        task_persistence=MockTaskPersistence(),
        outlook_manager=MockOutlookManager()
    )
```

### Pattern: Conditional Dependency
```python
def __init__(self, database_manager: Optional[DatabaseManagerInterface] = None):
    # Some components only need database in certain contexts
    self.database_manager = database_manager
    
def save_to_database(self, data):
    if self.database_manager:
        with self.database_manager.get_connection() as conn:
            # Save data
            pass
```

## Troubleshooting

### Issue: Circular Import
**Solution**: Use `TYPE_CHECKING` for type hints:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.outlook_manager import OutlookManager

def __init__(self, outlook: Optional['OutlookManager'] = None):
    ...
```

### Issue: Mock Not Working
**Solution**: Ensure you're using the interface type, not concrete class:
```python
# Wrong
def __init__(self, outlook: OutlookManager):
    
# Right
def __init__(self, outlook: OutlookManagerInterface):
```

### Issue: Global State Conflicts
**Solution**: Use `factory.reset()` between tests:
```python
@pytest.fixture(autouse=True)
def reset_factory():
    factory = ServiceFactory()
    yield factory
    factory.reset()
```

## Further Reading

- `src/core/interfaces.py` - All interface definitions
- `src/core/service_factory.py` - ServiceFactory implementation
- `src/core/mock_services.py` - Mock implementations for testing
- `backend/services/task_service.py` - Example of DI in practice
