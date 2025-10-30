# Testing Guide for Email Helper

## Overview

This guide covers the comprehensive test infrastructure, patterns, and best practices for the Email Helper project.

## Table of Contents

- [Test Organization](#test-organization)
- [Running Tests](#running-tests)
- [Test Markers](#test-markers)
- [Fixtures](#fixtures)
- [Mock Factories](#mock-factories)
- [Test Data Generators](#test-data-generators)
- [Assertion Helpers](#assertion-helpers)
- [Testing Patterns](#testing-patterns)
- [Best Practices](#best-practices)

---

## Test Organization

### Directory Structure

```
email_helper/
├── test/                          # Main test suite (src/ code)
│   ├── conftest.py               # Shared fixtures
│   ├── test_utils.py             # Utilities and helpers
│   ├── test_*.py                 # Test modules
│   └── test_data/                # Test data files
├── backend/tests/                # Backend API tests
│   ├── conftest.py               # Backend fixtures
│   ├── utils.py                  # Backend test utils
│   └── test_*.py                 # Backend test modules
└── frontend/tests/               # Frontend tests
    └── *.test.ts                 # Vitest/Playwright tests
```

### Test Categories

1. **Unit Tests** - Test individual functions/classes in isolation
2. **Integration Tests** - Test component interactions
3. **E2E Tests** - Test complete workflows
4. **Smoke Tests** - Quick critical path validation
5. **Regression Tests** - Prevent known issues from returning

---

## Running Tests

### Basic Commands

```powershell
# Run all tests
python -m pytest

# Run specific test file
python -m pytest test/test_ai_processor_enhanced.py

# Run tests with specific marker
python -m pytest -m unit
python -m pytest -m "integration and not slow"

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run only fast tests
python -m pytest -m fast

# Run critical tests only
python -m pytest -m critical
```

### Coverage Reports

Coverage reports are generated in:
- **Terminal**: `--cov-report=term-missing`
- **HTML**: `runtime_data/coverage_html/index.html`
- **JSON**: `runtime_data/coverage.json`
- **XML**: `runtime_data/coverage.xml`

### Test Logs

Test logs are written to:
- `runtime_data/logs/pytest.log` (detailed debug logs)
- Console output (INFO level)

---

## Test Markers

### Available Markers

#### Test Types
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.smoke` - Smoke tests

#### Component-Specific
- `@pytest.mark.ui` - UI/GUI tests
- `@pytest.mark.api` - API tests
- `@pytest.mark.service` - Service layer tests
- `@pytest.mark.adapter` - Adapter tests
- `@pytest.mark.com` - COM adapter tests
- `@pytest.mark.database` - Database tests

#### Test Characteristics
- `@pytest.mark.slow` - Slow tests (>1 second)
- `@pytest.mark.fast` - Fast tests (<0.1 second)
- `@pytest.mark.mock` - Tests with mocks
- `@pytest.mark.real` - Tests requiring real services

#### Test Categories
- `@pytest.mark.regression` - Regression tests
- `@pytest.mark.workflow` - Workflow tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.critical` - Critical path tests

### Using Markers

```python
import pytest

@pytest.mark.unit
@pytest.mark.fast
def test_email_id_generation():
    """Test that email IDs are generated correctly."""
    from test.test_utils import DataGenerator
    email_id = DataGenerator.generate_email_id("test")
    assert email_id.startswith("test-")

@pytest.mark.integration
@pytest.mark.database
def test_save_email_to_database(database_with_schema):
    """Test saving email to database."""
    # Test implementation
    pass

@pytest.mark.slow
@pytest.mark.real
def test_real_outlook_connection():
    """Test real Outlook connection (requires credentials)."""
    # Skip if no credentials available
    pass
```

---

## Fixtures

### Database Fixtures

#### `temp_database`
Creates a temporary database file.

```python
def test_with_temp_db(temp_database):
    conn = sqlite3.connect(temp_database)
    # Use database
    conn.close()
```

#### `in_memory_database`
Creates an in-memory SQLite database (fast).

```python
def test_fast_db_operations(in_memory_database):
    cursor = in_memory_database.cursor()
    cursor.execute("SELECT 1")
    assert cursor.fetchone()[0] == 1
```

#### `database_with_schema`
In-memory database with full schema already created.

```python
def test_with_schema(database_with_schema):
    cursor = database_with_schema.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    assert "emails" in tables
```

### File System Fixtures

#### `temp_directory`
Provides a temporary directory that's automatically cleaned up.

```python
def test_file_operations(temp_directory):
    test_file = temp_directory / "test.txt"
    test_file.write_text("content")
    assert test_file.exists()
```

#### `temp_prompts_directory`
Temporary directory with sample .prompty files.

```python
def test_prompts_loading(temp_prompts_directory):
    classifier = temp_prompts_directory / "email_classifier.prompty"
    assert classifier.exists()
```

### Mock Fixtures

#### `mock_outlook_manager`
Pre-configured mock OutlookManager.

```python
def test_email_retrieval(mock_outlook_manager):
    emails = mock_outlook_manager.get_emails()
    assert emails == []
```

#### `mock_ai_processor`
Pre-configured mock AIProcessor with standard responses.

```python
def test_classification(mock_ai_processor):
    category = mock_ai_processor.classify_email("Test email")
    assert category == "required_personal_action"
```

#### `mock_outlook_manager_with_emails`
Mock manager with sample emails pre-loaded.

```python
def test_process_batch(mock_outlook_manager_with_emails):
    emails = mock_outlook_manager_with_emails.get_emails()
    assert len(emails) == 5
```

### Email Data Fixtures

#### `sample_email_data`
Single sample email.

```python
def test_email_structure(sample_email_data):
    assert "subject" in sample_email_data
    assert "body" in sample_email_data
```

#### `sample_email_list`
List of 5 sample emails.

```python
def test_batch_processing(sample_email_list):
    for email in sample_email_list:
        process_email(email)
```

#### `sample_action_item_email`
Email containing action items.

```python
def test_action_extraction(sample_action_item_email):
    actions = extract_actions(sample_action_item_email)
    assert len(actions) > 0
```

### Time Fixtures

#### `fixed_datetime`
Fixed datetime for deterministic tests.

```python
def test_with_fixed_time(fixed_datetime):
    assert fixed_datetime.year == 2025
    assert fixed_datetime.month == 1
```

#### `mock_datetime_now`
Mocks datetime.now() to return fixed time.

```python
def test_time_dependent_logic(mock_datetime_now):
    now = datetime.now()
    assert now.year == 2025
```

---

## Mock Factories

### MockFactory Class

Central factory for creating mock objects.

#### Create Mock OutlookManager

```python
from test.test_utils import MockFactory

def test_with_custom_mock():
    manager = MockFactory.create_outlook_manager(
        connected=True,
        emails=[{"id": "1", "subject": "Test"}]
    )
    assert manager.is_connected
    assert len(manager.get_emails()) == 1
```

#### Create Mock AIProcessor

```python
def test_with_ai_mock():
    processor = MockFactory.create_ai_processor(
        classification="spam",
        confidence=0.95
    )
    result = processor.classify_email("Test")
    assert result == "spam"
```

#### Create Mock TaskPersistence

```python
def test_task_operations():
    persistence = MockFactory.create_task_persistence(
        existing_tasks=[{"id": "task-1", "title": "Test"}]
    )
    task = persistence.get_task("task-1")
    assert task["title"] == "Test"
```

---

## Test Data Generators

### DataGenerator Class

Generate realistic test data on demand.

#### Generate Emails

```python
from test.test_utils import DataGenerator

# Single email
email = DataGenerator.create_email(
    subject="Important Meeting",
    body="Please attend...",
    sender="boss@company.com"
)

# Batch of emails
emails = DataGenerator.create_email_batch(
    count=10,
    base_subject="Newsletter"
)

# Specialized emails
action_email = DataGenerator.create_action_item_email(
    action="Review budget",
    due_date="Friday",
    priority="high"
)

meeting_email = DataGenerator.create_meeting_email(
    meeting_time=datetime.now() + timedelta(days=1),
    duration_minutes=30
)

newsletter = DataGenerator.create_newsletter_email("Tech Weekly")
```

#### Generate Tasks

```python
task = DataGenerator.create_task(
    title="Complete report",
    description="Q4 financial report",
    priority="high",
    status="pending"
)
```

#### Generate Unique IDs

```python
email_id = DataGenerator.generate_email_id("test")
# Returns: "test-1234567890123456"
```

---

## Assertion Helpers

### AssertionHelper Class

Specialized assertions for common validations.

#### Assert Email Structure

```python
from test.test_utils import AssertionHelper

def test_email_valid(sample_email_data):
    AssertionHelper.assert_email_structure(sample_email_data)
    # Passes if email has required fields
```

#### Assert Classification Valid

```python
def test_classification():
    category = classify_email("test")
    AssertionHelper.assert_classification_valid(
        category,
        valid_categories=["spam", "work", "personal"]
    )
```

#### Assert Action Items Structure

```python
def test_action_items():
    items = extract_action_items(email)
    AssertionHelper.assert_action_items_structure(items)
```

#### Assert Task Structure

```python
def test_task_creation():
    task = create_task("Test task")
    AssertionHelper.assert_task_structure(task)
```

#### Assert Database Table Exists

```python
def test_database_schema(database_connection):
    AssertionHelper.assert_database_has_table(
        database_connection,
        "emails"
    )
```

#### Assert Mock Called With Email

```python
def test_mock_interaction():
    mock = Mock()
    mock.process("email-123")
    AssertionHelper.assert_mock_called_with_email(mock, "email-123")
```

---

## Testing Patterns

### Pattern: Arrange-Act-Assert

```python
def test_email_classification(mock_ai_processor, sample_email_data):
    # ARRANGE
    processor = mock_ai_processor
    email = sample_email_data
    
    # ACT
    result = processor.classify_email(email["body"])
    
    # ASSERT
    assert result == "required_personal_action"
```

### Pattern: Test Data Builder

```python
from test.test_utils import FixtureBuilder

def test_complete_workflow():
    # Build complex scenario
    scenario = FixtureBuilder.build_email_workflow_scenario(
        num_emails=5,
        include_action_items=True,
        include_meetings=True
    )
    
    emails = scenario["emails"]
    assert scenario["total_count"] == 8
    assert scenario["action_items_count"] == 2
```

### Pattern: Parameterized Tests

```python
@pytest.mark.parametrize("category,confidence", [
    ("spam", 0.95),
    ("work_relevant", 0.85),
    ("personal", 0.90)
])
def test_various_classifications(category, confidence):
    processor = MockFactory.create_ai_processor(
        classification=category,
        confidence=confidence
    )
    result = processor.classify_email("test")
    assert result == category
```

### Pattern: Fixture Composition

```python
@pytest.fixture
def complete_test_environment(
    database_with_schema,
    mock_outlook_manager_with_emails,
    mock_ai_processor,
    temp_directory
):
    """Combine multiple fixtures into complete environment."""
    return {
        "database": database_with_schema,
        "outlook": mock_outlook_manager_with_emails,
        "ai": mock_ai_processor,
        "temp_dir": temp_directory
    }

def test_with_environment(complete_test_environment):
    env = complete_test_environment
    # Use all components together
```

### Pattern: Context Manager Testing

```python
def test_database_transaction(database_connection):
    with database_connection:
        cursor = database_connection.cursor()
        cursor.execute("INSERT INTO emails ...")
        # Transaction auto-commits on exit
```

---

## Best Practices

### 1. Use Appropriate Test Markers

Mark tests clearly so they can be run selectively:

```python
@pytest.mark.unit
@pytest.mark.fast
def test_simple_function():
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_complex_workflow():
    pass
```

### 2. Keep Tests Isolated

Each test should be independent:

```python
# GOOD - Each test is independent
def test_email_creation():
    email = DataGenerator.create_email()
    assert email["id"]

def test_email_processing():
    email = DataGenerator.create_email()
    process(email)

# BAD - Tests depend on shared state
shared_email = None

def test_create_shared_email():
    global shared_email
    shared_email = DataGenerator.create_email()

def test_use_shared_email():
    process(shared_email)  # Fails if previous test didn't run
```

### 3. Use Fixtures for Setup/Teardown

```python
@pytest.fixture
def setup_test_environment():
    # Setup
    config = load_config()
    yield config
    # Teardown happens automatically
```

### 4. Test Edge Cases

```python
def test_email_with_empty_subject():
    email = DataGenerator.create_email(subject="")
    # Test how system handles edge case

def test_email_with_very_long_body():
    email = DataGenerator.create_email(body="x" * 100000)
    # Test limits

def test_classification_with_low_confidence():
    processor = MockFactory.create_ai_processor(confidence=0.3)
    # Test boundary conditions
```

### 5. Use Descriptive Test Names

```python
# GOOD - Clear what's being tested
def test_email_classification_returns_correct_category():
    pass

def test_outlook_manager_raises_error_when_disconnected():
    pass

# BAD - Unclear purpose
def test_email():
    pass

def test_manager():
    pass
```

### 6. Mock External Dependencies

```python
@pytest.mark.mock
def test_with_mocked_ai(mock_ai_processor):
    # Fast, no API calls
    result = mock_ai_processor.classify_email("test")
    assert result

@pytest.mark.real
def test_with_real_ai():
    # Slow, requires credentials
    # Only run when needed
    pass
```

### 7. Use Assertion Helpers

```python
# GOOD - Reusable, consistent
def test_email_structure(sample_email_data):
    AssertionHelper.assert_email_structure(sample_email_data)

# BAD - Repetitive, inconsistent
def test_email_structure(sample_email_data):
    assert "id" in sample_email_data
    assert "subject" in sample_email_data
    assert isinstance(sample_email_data["id"], str)
    # ... etc
```

### 8. Test Error Conditions

```python
def test_database_connection_failure(temp_database):
    # Test graceful error handling
    os.unlink(temp_database)  # Delete database
    with pytest.raises(sqlite3.OperationalError):
        conn = sqlite3.connect(temp_database)
        conn.execute("SELECT * FROM emails")

def test_ai_service_timeout(mock_ai_processor):
    mock_ai_processor.classify_email.side_effect = TimeoutError
    with pytest.raises(TimeoutError):
        process_email_with_ai(mock_ai_processor, email)
```

### 9. Use Parametrized Tests for Multiple Cases

```python
@pytest.mark.parametrize("email_type,expected_category", [
    ("action_item", "required_personal_action"),
    ("newsletter", "newsletter"),
    ("meeting", "required_personal_action"),
    ("spam", "spam")
])
def test_email_classification_types(email_type, expected_category):
    # One test function, multiple scenarios
    pass
```

### 10. Keep Tests Fast

```python
# GOOD - Fast with mocks
@pytest.mark.fast
def test_quick_classification(mock_ai_processor):
    result = mock_ai_processor.classify_email("test")
    # Runs in milliseconds

# SLOW - Mark appropriately
@pytest.mark.slow
@pytest.mark.real
def test_full_integration_with_real_services():
    # Takes seconds/minutes
    pass
```

---

## Common Patterns

### Testing Database Operations

```python
def test_save_and_retrieve_email(database_with_schema):
    email = DataGenerator.create_email()
    
    # Save
    cursor = database_with_schema.cursor()
    cursor.execute(
        "INSERT INTO emails (id, subject, body) VALUES (?, ?, ?)",
        (email["id"], email["subject"], email["body"])
    )
    database_with_schema.commit()
    
    # Retrieve
    cursor.execute("SELECT * FROM emails WHERE id = ?", (email["id"],))
    result = cursor.fetchone()
    
    assert result["subject"] == email["subject"]
```

### Testing File Operations

```python
def test_save_summary_to_file(temp_directory):
    summary_file = temp_directory / "summary.json"
    data = {"summary": "Test"}
    
    summary_file.write_text(json.dumps(data))
    
    loaded = json.loads(summary_file.read_text())
    assert loaded["summary"] == "Test"
```

### Testing API Endpoints

```python
@pytest.mark.api
def test_email_endpoint(client, mock_outlook_manager_with_emails):
    response = client.get("/api/emails")
    assert response.status_code == 200
    assert len(response.json()["emails"]) == 5
```

---

## Troubleshooting

### Tests Fail With Import Errors

Ensure virtual environment is activated:
```powershell
.venv\Scripts\Activate.ps1
```

### Coverage Reports Not Generated

Check that `runtime_data/` directory exists and is writable.

### Fixtures Not Found

Verify `conftest.py` is in the correct directory and imports are correct.

### Slow Test Suite

Run only fast tests during development:
```powershell
python -m pytest -m "not slow"
```

---

## Summary

This testing infrastructure provides:

1. **Comprehensive Fixtures** - Database, files, mocks, test data
2. **Mock Factories** - Easy creation of mock objects
3. **Data Generators** - Realistic test data on demand
4. **Assertion Helpers** - Reusable validation functions
5. **Test Markers** - Organize and filter tests
6. **Best Practices** - Patterns for reliable testing

Use these tools to write fast, reliable, maintainable tests that catch bugs early and enable confident refactoring.
