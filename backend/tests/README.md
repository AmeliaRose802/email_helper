# Backend Tests Documentation

This directory contains comprehensive tests for the Email Helper backend API, including unit tests, integration tests, and end-to-end workflow tests.

## Directory Structure

```
backend/tests/
├── __init__.py                           # Test package initialization
├── README.md                             # This file
├── integration/                          # Integration tests
│   ├── __init__.py
│   ├── test_com_outlook_integration.py   # COM Outlook adapter integration tests
│   ├── test_ai_processing_integration.py # AI service integration tests
│   └── test_full_workflow_integration.py # Complete workflow tests
├── test_ai_api.py                        # AI API endpoint tests
├── test_ai_service.py                    # AI service unit tests
├── test_auth.py                          # Authentication tests
├── test_com_ai_service.py                # COM AI service unit tests
├── test_com_email_provider.py            # COM email provider unit tests
├── test_database.py                      # Database tests
├── test_dependencies.py                  # Dependency injection tests
├── test_di_integration.py                # DI integration tests
├── test_email_api.py                     # Email API endpoint tests
├── test_email_provider.py                # Email provider interface tests
├── test_graph_client.py                  # Microsoft Graph client tests
├── test_job_queue.py                     # Job queue tests
├── test_main.py                          # Main application tests
├── test_processing_pipeline.py           # Processing pipeline tests
├── test_task_api.py                      # Task API endpoint tests
├── test_task_integration.py              # Task integration tests
└── test_task_service.py                  # Task service tests
```

## Test Categories

### Unit Tests
Unit tests validate individual components in isolation with mocked dependencies:
- `test_com_email_provider.py` - Tests COMEmailProvider wrapper
- `test_com_ai_service.py` - Tests COMAIService adapter
- `test_ai_service.py` - Tests standard AIService
- `test_email_provider.py` - Tests base EmailProvider interface
- `test_task_service.py` - Tests TaskService operations
- `test_database.py` - Tests database operations

### Integration Tests
Integration tests verify interactions between multiple components with mocked external dependencies:

#### `test_com_outlook_integration.py`
Tests COM Outlook adapter integration:
- **Email Retrieval Workflows** - Complete authentication and email fetching
- **Pagination Support** - Multi-page email retrieval
- **Folder Operations** - Folder listing and navigation
- **Email Content Access** - Detailed email content retrieval
- **Email Manipulation** - Mark as read, move operations
- **Conversation Threads** - Thread retrieval and tracking
- **Error Handling** - Authentication failures, connection losses, COM exceptions
- **Concurrency** - Multiple operations and batch processing

**Coverage:** 80%+ of COM email provider integration paths

#### `test_ai_processing_integration.py`
Tests AI service integration workflows:
- **Email Classification** - Single and batch classification
- **Classification Types** - Different email categories (action, event, FYI)
- **Context-Aware Classification** - Using additional context
- **Action Item Extraction** - Parsing action items with deadlines and priorities
- **Summarization** - Brief and detailed summary generation
- **Email Provider Integration** - Combined email retrieval and AI processing
- **Error Resilience** - Timeout handling, retry logic, fallback responses

**Coverage:** 80%+ of AI processing integration paths

#### `test_full_workflow_integration.py`
Tests complete end-to-end workflows:
- **Retrieval → Classification Pipeline** - Full email classification workflow
- **Retrieval → Action Extraction Pipeline** - Complete action item extraction
- **Retrieval → Summarization Pipeline** - End-to-end summarization
- **Complete Processing Pipeline** - Classify + Extract + Summarize
- **Error Recovery** - Graceful degradation and partial failure handling
- **Performance** - Batch processing and concurrent operations
- **Data Persistence** - State tracking and categorization persistence

**Coverage:** 80%+ of complete workflow paths

### API Integration Tests
API tests verify endpoint behavior with dependency injection:
- `test_di_integration.py` - Tests DI with COM and standard providers
- `test_email_api.py` - Tests email API endpoints
- `test_ai_api.py` - Tests AI API endpoints
- `test_task_api.py` - Tests task management endpoints

### End-to-End Tests
- `test_task_integration.py` - Complete task management workflow
- `test_processing_pipeline.py` - Email processing pipeline

## Running Tests

### Run All Tests
```bash
pytest backend/tests/
```

### Run Unit Tests Only
```bash
pytest backend/tests/ -m "not integration"
```

### Run Integration Tests Only
```bash
pytest backend/tests/integration/ -m integration
```

### Run Specific Test File
```bash
pytest backend/tests/integration/test_com_outlook_integration.py -v
```

### Run Specific Test Class
```bash
pytest backend/tests/integration/test_com_outlook_integration.py::TestCOMOutlookIntegration -v
```

### Run Specific Test
```bash
pytest backend/tests/integration/test_com_outlook_integration.py::TestCOMOutlookIntegration::test_email_retrieval_workflow -v
```

### Run with Coverage
```bash
pytest backend/tests/ --cov=backend --cov-report=html
```

### Run Async Tests
```bash
pytest backend/tests/integration/test_ai_processing_integration.py -v
```

## Test Markers

Tests are organized with pytest markers for selective execution:

- `@pytest.mark.integration` - Integration tests requiring multiple components
- `@pytest.mark.asyncio` - Async tests requiring asyncio support
- `@pytest.mark.unit` - Unit tests for isolated components
- `@pytest.mark.slow` - Slow-running tests (may be skipped for quick runs)

### Using Markers
```bash
# Run only integration tests
pytest -m integration

# Run only async tests
pytest -m asyncio

# Skip slow tests
pytest -m "not slow"

# Combine markers
pytest -m "integration and asyncio"
```

## Test Fixtures

### Common Fixtures

#### Email Provider Fixtures
- `mock_outlook_adapter` - Mock OutlookEmailAdapter with common operations
- `com_email_provider` - COMEmailProvider with mocked adapter
- `mock_complete_email_provider` - Comprehensive email provider with sample data

#### AI Service Fixtures
- `mock_ai_processor` - Mock AIProcessor for AI operations
- `mock_azure_config` - Mock Azure OpenAI configuration
- `com_ai_service` - COMAIService with mocked dependencies
- `mock_complete_ai_service` - Comprehensive AI service with intelligent responses

#### API Fixtures
- `client` - FastAPI TestClient for API testing
- `mock_auth` - Mock authentication for bypassing auth requirements

## Writing New Tests

### Integration Test Template

```python
import pytest
from unittest.mock import Mock, MagicMock, patch

@pytest.mark.integration
class TestNewIntegration:
    """Integration tests for new feature."""
    
    @pytest.fixture
    def mock_dependency(self):
        """Create mock dependency."""
        mock = MagicMock()
        mock.method.return_value = "result"
        return mock
    
    def test_integration_workflow(self, mock_dependency):
        """Test complete workflow."""
        # Setup
        # Execute
        # Assert
        pass
```

### Async Integration Test Template

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncIntegration:
    """Async integration tests."""
    
    async def test_async_workflow(self, com_ai_service):
        """Test async workflow."""
        result = await com_ai_service.classify_email("Test")
        assert 'category' in result
```

## Test Best Practices

### 1. Isolation
- Each test should be independent and not rely on other tests
- Use fixtures to set up and tear down test state
- Mock external dependencies (COM, AI services, databases)

### 2. Clear Naming
- Use descriptive test names: `test_<action>_<expected_result>`
- Example: `test_email_retrieval_workflow`, `test_classification_with_context`

### 3. Arrange-Act-Assert
- **Arrange:** Set up test data and mocks
- **Act:** Execute the code being tested
- **Assert:** Verify expected outcomes

### 4. Error Testing
- Test both success and failure scenarios
- Verify error handling and exception raising
- Test edge cases and boundary conditions

### 5. Mock Strategy
- Mock at the appropriate level (service boundaries)
- Don't mock the code you're testing
- Use realistic mock data that represents actual usage

### 6. Coverage Goals
- Unit tests: 90%+ coverage
- Integration tests: 80%+ coverage of integration paths
- Focus on critical paths and error handling

## Continuous Integration

Tests are automatically run on:
- Every pull request
- Commits to main branches
- Nightly builds for comprehensive testing

### CI Configuration
```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: |
    pytest backend/tests/ \
      --cov=backend \
      --cov-report=xml \
      --junitxml=test-results.xml
```

## Troubleshooting

### Import Errors
If you encounter import errors:
```bash
export PYTHONPATH=/path/to/email_helper:$PYTHONPATH
```

### COM Not Available
COM tests require Windows. On Linux/Mac:
- Tests automatically mock COM dependencies
- Use `COM_AVAILABLE` flag to check platform

### Async Test Failures
Ensure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

### Coverage Issues
Generate detailed coverage report:
```bash
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```

## Dependencies

Required testing packages:
```
pytest>=7.0
pytest-asyncio>=0.21
pytest-mock>=3.10
pytest-cov>=4.0
fastapi
httpx
```

Install test dependencies:
```bash
pip install -r requirements-test.txt
```

## Contributing

When adding new features:
1. Write unit tests for new components
2. Write integration tests for component interactions
3. Update this README if adding new test categories
4. Ensure tests pass: `pytest backend/tests/`
5. Verify coverage: `pytest --cov=backend`

## Support

For questions or issues with tests:
- Check test output for detailed error messages
- Review test logs in CI/CD pipeline
- Consult existing test examples
- Create an issue with test failure details
