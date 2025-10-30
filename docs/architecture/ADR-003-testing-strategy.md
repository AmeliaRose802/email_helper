# ADR-003: Testing Strategy

## Status
**Accepted** (October 2025)

## Context

The Email Helper project has complex testing requirements:

**Complexity Factors:**
- Multiple integration points (Outlook COM, Azure OpenAI, SQLite)
- Both synchronous (desktop) and asynchronous (API) code paths
- UI components (Tkinter GUI, React frontend)
- External service dependencies (Outlook, Azure)
- Multiple deployment targets (desktop, web, mobile)

**Testing Challenges:**
- Running tests without Outlook installation
- Testing AI features without Azure credentials
- Testing UI without manual interaction
- Fast test execution for CI/CD
- Test isolation and repeatability
- Coverage across unit, integration, and E2E tests

**Goals:**
1. High code coverage (>80%) without sacrificing quality
2. Fast test suite for developer productivity
3. Comprehensive integration testing
4. Easy-to-run tests for CI/CD
5. Clear test organization

## Decision

We implement a **multi-layered testing strategy** using pytest with clear markers and organization:

### Test Organization

```
test/
├── unit/                    # Fast, isolated unit tests
│   ├── test_ai_processor.py
│   ├── test_outlook_manager.py
│   └── test_task_persistence.py
├── integration/             # Integration with real components
│   ├── test_com_integration.py
│   ├── test_database_integration.py
│   └── test_ai_integration.py
├── e2e/                    # End-to-end workflows
│   ├── test_email_classification_workflow.py
│   └── test_task_management_workflow.py
└── conftest.py             # Shared fixtures and configuration

backend/tests/
├── test_api_endpoints.py   # API unit tests
├── test_dependencies.py    # DI system tests
└── test_integration.py     # API integration tests
```

### Pytest Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = test
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (require services)
    e2e: End-to-end workflow tests
    slow: Slow running tests
    ui: UI/GUI tests
    com: Tests requiring COM/Outlook
    mock: Tests using mocked dependencies
    regression: Regression prevention tests

addopts =
    -v
    --tb=short
    --strict-markers
    --cov=src
    --cov=backend
    --cov-report=term-missing
    --cov-report=html
    --maxfail=10

timeout = 300
```

### Test Markers Usage

```python
# Unit test - fast, mocked dependencies
@pytest.mark.unit
@pytest.mark.mock
def test_classify_email_structure():
    """Test email classification logic with mocked AI."""
    ai_processor = AIProcessor(mock_client=True)
    result = ai_processor.classify_email(sample_email)
    assert result.category in VALID_CATEGORIES

# Integration test - real services
@pytest.mark.integration
@pytest.mark.com
def test_outlook_folder_access():
    """Test real Outlook folder access via COM."""
    manager = OutlookManager()
    folders = manager.get_folders()
    assert len(folders) > 0

# E2E test - complete workflow
@pytest.mark.e2e
@pytest.mark.slow
def test_email_processing_workflow():
    """Test complete email fetch -> classify -> persist workflow."""
    # End-to-end test with all real components
```

### Test Fixtures

Centralized fixtures in `conftest.py`:

```python
# conftest.py
@pytest.fixture
def mock_ai_client():
    """Provides mock AI client for testing."""
    return MockAzureOpenAI()

@pytest.fixture
def test_database():
    """Provides isolated test database."""
    db_path = Path("test_data/test.db")
    db = DatabaseManager(db_path)
    yield db
    db_path.unlink(missing_ok=True)

@pytest.fixture
def sample_emails():
    """Provides sample email data."""
    return load_json("test_data/sample_emails.json")

@pytest.fixture
def outlook_manager_mock():
    """Provides mocked Outlook manager."""
    with patch('src.outlook_manager.OutlookManager') as mock:
        yield mock
```

### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests (fast)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run excluding slow tests
pytest -m "not slow"

# Run with coverage
pytest --cov=src --cov=backend

# Run specific test file
pytest test/unit/test_ai_processor.py -v

# Run tests matching pattern
pytest -k "test_classify" -v
```

## Consequences

### Positive

✅ **Clear Organization**: Developers know where to find and add tests
✅ **Selective Execution**: Can run fast unit tests during development
✅ **CI/CD Friendly**: Can skip slow/integration tests for quick checks
✅ **Good Coverage**: Comprehensive coverage configuration built-in
✅ **Isolated Tests**: Fixtures provide clean test isolation
✅ **Documentation**: Markers serve as test documentation
✅ **Fast Feedback**: Unit tests run in seconds, integration tests as needed
✅ **Maintainable**: Shared fixtures reduce duplication

### Negative

❌ **Initial Setup Cost**: Takes time to write comprehensive test suite
❌ **Marker Discipline**: Developers must remember to use correct markers
❌ **Fixture Complexity**: Can be hard to track fixture dependencies
❌ **Integration Tests**: Require real services (Outlook, Azure) for some tests
❌ **Test Data Management**: Need to maintain sample data files

### Neutral

⚠️ **Learning Curve**: Team needs to understand pytest markers and fixtures
⚠️ **Coverage Goals**: Need to balance coverage percentage with test quality
⚠️ **Mock Strategy**: Need clear guidelines on when to mock vs. use real services

## Alternatives Considered

### Alternative 1: Flat Test Structure
```
test/
├── test_everything.py
└── test_more_stuff.py
```

**Rejected because:**
- Hard to find relevant tests
- No organization by test type
- Can't selectively run test subsets
- Becomes unmaintainable as project grows

### Alternative 2: BDD Framework (Behave/pytest-bdd)
```gherkin
Feature: Email Classification
  Scenario: Classify urgent email
    Given an email with urgent subject
    When I classify the email
    Then it should be categorized as urgent
```

**Rejected because:**
- Added complexity and learning curve
- Overhead of maintaining .feature files
- Not necessary for current team size
- pytest is sufficient for our needs

### Alternative 3: unittest Framework
```python
import unittest

class TestAIProcessor(unittest.TestCase):
    def test_classify_email(self):
        self.assertEqual(result, expected)
```

**Rejected because:**
- More verbose than pytest
- Fixtures less powerful than pytest
- No built-in markers system
- Less modern than pytest

### Alternative 4: No Test Organization
Just write tests wherever, run all tests every time.

**Rejected because:**
- Slow test suite hinders development
- Can't distinguish unit from integration tests
- No way to run subset of tests
- Poor developer experience

## Implementation Details

### Test Categories

**Unit Tests** (`@pytest.mark.unit`)
- Test single functions or classes in isolation
- All external dependencies mocked
- Fast execution (<1s per test)
- Run on every commit
- Goal: >80% code coverage

**Integration Tests** (`@pytest.mark.integration`)
- Test component interactions
- May use real services (database, COM)
- Moderate execution time (1-10s per test)
- Run before merge
- Goal: Cover critical integration points

**E2E Tests** (`@pytest.mark.e2e`)
- Test complete user workflows
- Use real services and data
- Slow execution (>10s per test)
- Run nightly or before release
- Goal: Validate key user journeys

### Mock Strategy

```python
# ✅ GOOD: Mock external services
@pytest.mark.unit
def test_ai_classification_logic(mock_ai_client):
    """Test classification logic without hitting Azure."""
    processor = AIProcessor(client=mock_ai_client)
    result = processor.classify_email(email)
    assert result.confidence > 0.8

# ✅ GOOD: Use real services for integration
@pytest.mark.integration
@pytest.mark.com
def test_outlook_real_connection():
    """Test actual Outlook connection."""
    manager = OutlookManager()  # Real COM interface
    folders = manager.get_folders()
    assert "Inbox" in [f.name for f in folders]

# ❌ BAD: Mock too much in integration test
@pytest.mark.integration  # Marked integration but everything mocked!
def test_fake_integration(mock_outlook, mock_ai, mock_db):
    # This is actually a unit test
    pass
```

### Fixture Best Practices

```python
# ✅ GOOD: Reusable fixture
@pytest.fixture
def temp_database():
    """Provides clean database for each test."""
    db_path = Path(f"test_{uuid.uuid4()}.db")
    db = DatabaseManager(db_path)
    yield db
    db.close()
    db_path.unlink(missing_ok=True)

# ✅ GOOD: Fixture with cleanup
@pytest.fixture
def sample_email_file():
    """Creates temp email file."""
    path = Path("temp_email.txt")
    path.write_text("test email content")
    yield path
    path.unlink(missing_ok=True)

# ❌ BAD: Fixture with side effects
@pytest.fixture
def bad_fixture():
    # Modifies global state without cleanup!
    os.environ['SETTING'] = 'value'
    return None
    # Missing cleanup!
```

### Coverage Configuration

```ini
# pytest.ini
[tool:pytest]
addopts =
    --cov=src              # Cover src/ directory
    --cov=backend          # Cover backend/ directory
    --cov-report=term-missing  # Show missing lines
    --cov-report=html          # Generate HTML report
    --cov-fail-under=80        # Fail if coverage < 80%

# .coveragerc
[run]
omit =
    */tests/*
    */test_*.py
    */__pycache__/*
    */migrations/*
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run unit tests
        run: pytest -m unit --cov --cov-report=xml
      
  integration-tests:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run integration tests
        run: pytest -m integration
        # Only on main branch merges
        if: github.ref == 'refs/heads/main'
```

## Testing Guidelines

### When to Write Each Test Type

**Write Unit Tests When:**
- Testing pure functions
- Testing business logic
- Testing data transformations
- Testing error handling
- Fast feedback needed

**Write Integration Tests When:**
- Testing service interactions
- Testing database operations
- Testing COM interface
- Testing API endpoints
- Validating component integration

**Write E2E Tests When:**
- Testing critical user workflows
- Validating complete features
- Regression testing
- Release validation
- Acceptance criteria testing

### Test Naming Convention

```python
# Pattern: test_<what>_<condition>_<expected>

# ✅ GOOD: Clear test names
def test_classify_email_urgent_keyword_returns_urgent_category():
    """Test that emails with urgent keywords are classified as urgent."""
    
def test_get_folders_outlook_closed_raises_connection_error():
    """Test that accessing folders when Outlook closed raises error."""

# ❌ BAD: Vague test names
def test_email():
    """What does this test?"""
    
def test_it_works():
    """Too vague."""
```

## Related Decisions

- [ADR-002: Dependency Injection Pattern](ADR-002-dependency-injection-pattern.md) - DI enables easy mocking
- [ADR-004: Error Handling Approach](ADR-004-error-handling-approach.md) - Error handling affects test design

## Future Enhancements

1. **Mutation Testing**: Use mutmut or similar to verify test quality
2. **Performance Testing**: Add benchmarks for critical paths
3. **Visual Regression**: Add visual testing for UI components
4. **Contract Testing**: Add contract tests for API consumers
5. **Load Testing**: Add load tests for backend API

## References

- Configuration: `pytest.ini`
- Test Organization: `test/TEST_ORGANIZATION.md`
- Fixtures: `test/conftest.py`, `backend/tests/conftest.py`
- Pytest Docs: https://docs.pytest.org/
- Coverage Docs: https://coverage.readthedocs.io/

## Authors

- Architecture: Development Team
- Implementation: GitHub Copilot
- Documentation: GitHub Copilot
- Review: Project Maintainers
