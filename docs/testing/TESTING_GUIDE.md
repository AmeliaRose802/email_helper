# Email Helper Testing Strategy and Guidelines

## Table of Contents

1. [Overview](#overview)
2. [When to Write Unit vs Integration Tests](#when-to-write-unit-vs-integration-tests)
3. [How to Write Effective Mocks](#how-to-write-effective-mocks)
4. [Test Naming Conventions](#test-naming-conventions)
5. [Coverage Expectations](#coverage-expectations)
6. [Test Organization](#test-organization)
7. [Running Tests](#running-tests)
8. [Best Practices](#best-practices)
9. [Common Patterns](#common-patterns)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides comprehensive testing strategies and guidelines for the Email Helper project. Our testing philosophy prioritizes:

- **Fast feedback loops** - Unit tests run in milliseconds
- **Reliable integration tests** - Test component interactions without external dependencies
- **Comprehensive E2E tests** - Verify complete user workflows
- **Mock-based testing for speed** - Use real dependencies only when necessary
- **Clear test intentions** - Tests serve as executable documentation

### Testing Pyramid

```
        /\
       /  \     E2E Tests (Slow, High Value)
      /____\    10-15% of tests
     /      \
    /        \  Integration Tests (Medium Speed)
   /          \ 25-30% of tests
  /____________\
 /              \
/________________\ Unit Tests (Fast, Focused)
                   55-65% of tests
```

---

## When to Write Unit vs Integration Tests

### Unit Tests

**Use unit tests when:**

- Testing a **single function or class** in isolation
- The component has **no external dependencies** (or they can be easily mocked)
- You need **fast feedback** during development
- Testing **edge cases, error conditions, and boundary values**
- Verifying **business logic** that doesn't require database or API calls

**Examples of what to unit test:**

```python
# ✅ Pure functions - Perfect for unit tests
def calculate_email_priority(importance: str, has_action_items: bool) -> int:
    """Calculate priority score for email."""
    if importance == "high":
        return 10 if has_action_items else 8
    return 5 if has_action_items else 3

# Test example
def test_calculate_email_priority_high_with_actions():
    assert calculate_email_priority("high", True) == 10

def test_calculate_email_priority_edge_case():
    assert calculate_email_priority("low", False) == 3
```

```python
# ✅ Data validation - Unit test
def validate_email_structure(email: Dict[str, Any]) -> bool:
    """Validate email has required fields."""
    required_fields = ["id", "subject", "body", "from"]
    return all(field in email for field in required_fields)

# Test with mock data
def test_validate_email_structure_valid():
    email = {"id": "1", "subject": "Test", "body": "Body", "from": "sender@test.com"}
    assert validate_email_structure(email) is True

def test_validate_email_structure_missing_field():
    email = {"id": "1", "subject": "Test"}  # Missing body and from
    assert validate_email_structure(email) is False
```

**Unit test markers:**
```python
import pytest

@pytest.mark.unit
@pytest.mark.fast
def test_email_id_generation():
    """Unit tests should be marked as 'unit' and 'fast'."""
    pass
```

### Integration Tests

**Use integration tests when:**

- Testing **multiple components working together**
- Verifying **database operations** (with test database)
- Testing **API endpoints** (with mocked external services)
- Checking **service layer interactions**
- Verifying **data flow between components**

**Examples of what to integration test:**

```python
# ✅ API endpoint with service layer - Integration test
@pytest.mark.integration
def test_classify_email_endpoint(client, mock_ai_service):
    """Test email classification endpoint with mocked AI service."""
    response = client.post("/api/emails/classify", json={
        "email_id": "test-1",
        "subject": "Important Meeting",
        "body": "Please review the attached documents."
    })
    
    assert response.status_code == 200
    assert response.json()["category"] in ["work_relevant", "required_personal_action"]
```

```python
# ✅ Database operations - Integration test
@pytest.mark.integration
@pytest.mark.database
def test_save_and_retrieve_email(database_with_schema):
    """Test saving email to database and retrieving it."""
    # Arrange
    email_data = {
        "id": "test-email-1",
        "subject": "Test Subject",
        "body": "Test body content",
        "from": "sender@test.com"
    }
    
    # Act - Save
    cursor = database_with_schema.cursor()
    cursor.execute(
        "INSERT INTO emails (id, subject, body, sender) VALUES (?, ?, ?, ?)",
        (email_data["id"], email_data["subject"], email_data["body"], email_data["from"])
    )
    database_with_schema.commit()
    
    # Act - Retrieve
    cursor.execute("SELECT * FROM emails WHERE id = ?", (email_data["id"],))
    result = cursor.fetchone()
    
    # Assert
    assert result["subject"] == email_data["subject"]
    assert result["body"] == email_data["body"]
```

```python
# ✅ Service interaction - Integration test
@pytest.mark.integration
async def test_email_processing_pipeline(mock_email_provider, mock_ai_service):
    """Test complete email processing pipeline."""
    # Arrange
    mock_email_provider.get_emails.return_value = [
        {"id": "1", "subject": "Meeting", "body": "Team meeting tomorrow"}
    ]
    
    # Act
    pipeline = EmailProcessingPipeline(mock_email_provider, mock_ai_service)
    results = await pipeline.process_all_emails()
    
    # Assert
    assert len(results) == 1
    assert results[0]["classified"] is True
    mock_ai_service.classify_email.assert_called_once()
```

**Integration test markers:**
```python
@pytest.mark.integration
@pytest.mark.slow  # Optional if test takes >1 second
def test_component_interaction():
    """Integration tests are marked as 'integration'."""
    pass
```

### E2E (End-to-End) Tests

**Use E2E tests when:**

- Testing **complete user workflows** through the UI
- Verifying **critical user paths** (email retrieval, classification, task creation)
- Testing **real browser interactions**
- Validating **frontend and backend integration**

**Examples:**

```typescript
// ✅ Complete user workflow - E2E test
test('User can retrieve, classify, and create task from email', async ({ page }) => {
  // Navigate to emails page
  await page.goto('/');
  await page.click('[data-testid="nav-emails"]');
  
  // Wait for emails to load
  await page.waitForSelector('[data-testid="email-item"]');
  
  // Click first email
  await page.click('[data-testid="email-item"]:first-child');
  
  // Classify email
  await page.click('[data-testid="classify-button"]');
  await page.waitForSelector('[data-testid="classification-result"]');
  
  // Create task from email
  await page.click('[data-testid="create-task-button"]');
  await page.fill('[data-testid="task-title"]', 'Follow up on meeting');
  await page.click('[data-testid="save-task-button"]');
  
  // Verify task was created
  await page.goto('/tasks');
  await expect(page.locator('text=Follow up on meeting')).toBeVisible();
});
```

### Decision Matrix

| Scenario | Test Type | Why |
|----------|-----------|-----|
| Validate email data structure | Unit | Pure validation logic, no dependencies |
| Calculate email priority score | Unit | Pure function, deterministic |
| Parse email subject line | Unit | String manipulation, no side effects |
| Save email to database | Integration | Tests database interaction |
| API endpoint returns correct data | Integration | Tests endpoint + service layer |
| Email provider fetches from Outlook | Integration | Tests COM interface (mocked) |
| AI service classifies email | Integration | Tests service + mocked AI API |
| User clicks email and sees details | E2E | Tests complete UI workflow |
| User processes 10 emails in batch | E2E | Tests critical user path |
| Settings page saves configuration | E2E | Tests UI + backend persistence |

---

## How to Write Effective Mocks

### CRITICAL: Mock Usage Policy

**⚠️ NEVER use mocks in production code**

- ❌ **NEVER** use `MockEmailProvider`, `MockAIProvider`, or any mock classes outside test files
- ❌ **NEVER** create fallback logic that uses mocks when real implementations fail
- ✅ **ALWAYS** throw explicit errors when required services are unavailable
- ✅ **ONLY** use mocks in `test/`, `backend/tests/`, `frontend/tests/` directories

### When to Mock

**Mock external dependencies:**
- ✅ Outlook COM interface (slow, requires Outlook installed)
- ✅ Azure OpenAI API (costs money, rate limited, requires credentials)
- ✅ File system operations (creates test pollution)
- ✅ Network requests (slow, unreliable)
- ✅ Date/time (makes tests deterministic)

**Don't mock:**
- ❌ Your own business logic
- ❌ Simple data structures
- ❌ Pure functions
- ❌ Fast, deterministic operations

### Mock Patterns

#### Pattern 1: Simple Mock with unittest.mock

```python
from unittest.mock import Mock, MagicMock, patch

def test_email_classification_with_mock():
    """Mock the AI service to test classification logic."""
    # Create mock
    mock_ai_service = Mock()
    mock_ai_service.classify_email.return_value = {
        "category": "work_relevant",
        "confidence": 0.92
    }
    
    # Use mock
    processor = EmailProcessor(ai_service=mock_ai_service)
    result = processor.process_email({"subject": "Meeting", "body": "Team sync"})
    
    # Verify mock was called correctly
    assert result["category"] == "work_relevant"
    mock_ai_service.classify_email.assert_called_once()
```

#### Pattern 2: Patch External Dependencies

```python
@patch('backend.services.ai_service.AIOrchestrator')
def test_ai_service_initialization(mock_orchestrator):
    """Patch AIOrchestrator to avoid real initialization."""
    mock_instance = MagicMock()
    mock_orchestrator.return_value = mock_instance
    
    service = AIService()
    service._ensure_initialized()
    
    assert service._initialized is True
    mock_orchestrator.assert_called_once()
```

#### Pattern 3: Fixture-Based Mocks (Preferred for Reusability)

```python
# In conftest.py
@pytest.fixture
def mock_email_provider():
    """Reusable mock email provider fixture."""
    provider = Mock()
    provider.get_emails.return_value = []
    provider.get_email_body.return_value = "Test body"
    provider.is_connected = True
    return provider

# In test file
def test_with_fixture(mock_email_provider):
    """Use fixture to get pre-configured mock."""
    emails = mock_email_provider.get_emails()
    assert emails == []
```

#### Pattern 4: Mock Factories for Complex Objects

```python
# In test/test_utils.py or backend/tests/utils.py
class MockFactory:
    """Factory for creating mock objects with sensible defaults."""
    
    @staticmethod
    def create_email_provider(emails=None, connected=True):
        """Create mock email provider with custom data."""
        provider = Mock()
        provider.is_connected = connected
        provider.get_emails.return_value = emails or []
        provider.get_folders.return_value = ["Inbox", "Sent", "Drafts"]
        provider.mark_as_read.return_value = True
        provider.move_email.return_value = True
        return provider
    
    @staticmethod
    def create_ai_service(classification="work_relevant", confidence=0.85):
        """Create mock AI service with custom responses."""
        service = Mock()
        service.classify_email.return_value = {
            "category": classification,
            "confidence": confidence
        }
        service.extract_action_items.return_value = []
        return service

# Usage in tests
def test_with_custom_mock():
    provider = MockFactory.create_email_provider(
        emails=[{"id": "1", "subject": "Test"}],
        connected=True
    )
    assert len(provider.get_emails()) == 1
```

#### Pattern 5: AsyncMock for Async Functions

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_classification():
    """Mock async AI service calls."""
    mock_ai_service = AsyncMock()
    mock_ai_service.classify_email_async.return_value = {
        "category": "spam",
        "confidence": 0.98
    }
    
    result = await mock_ai_service.classify_email_async("Buy now!")
    
    assert result["category"] == "spam"
    mock_ai_service.classify_email_async.assert_awaited_once()
```

### Mock Best Practices

#### ✅ DO: Mock at the boundary

```python
# GOOD - Mock at the service boundary
@patch('backend.services.com_email_provider.OutlookEmailAdapter')
def test_email_retrieval(mock_adapter):
    """Mock the Outlook adapter, not our service logic."""
    mock_instance = MagicMock()
    mock_adapter.return_value = mock_instance
    mock_instance.get_emails.return_value = [{"id": "1"}]
    
    provider = COMEmailProvider()
    emails = provider.get_emails()
    
    assert len(emails) == 1
```

#### ❌ DON'T: Mock your own functions

```python
# BAD - Mocking our own function defeats the purpose
@patch('backend.services.email_service.process_email')
def test_batch_processing(mock_process):
    """This test verifies nothing - we mocked what we're testing!"""
    mock_process.return_value = {"processed": True}
    
    result = process_email_batch([email1, email2])
    # We're not actually testing our batch processing logic!
```

#### ✅ DO: Use realistic test data

```python
# GOOD - Mock returns realistic data structure
def test_with_realistic_mock():
    mock_provider = Mock()
    mock_provider.get_emails.return_value = [
        {
            "id": "AAMkAGI2T...",
            "subject": "Q4 Budget Review",
            "body": "Please review the attached budget...",
            "from": "finance@company.com",
            "from_name": "Finance Department",
            "received_time": "2025-10-30T14:30:00Z",
            "is_read": False,
            "importance": "high"
        }
    ]
```

#### ❌ DON'T: Use minimal/unrealistic data

```python
# BAD - Minimal data may miss edge cases
def test_with_minimal_mock():
    mock_provider = Mock()
    mock_provider.get_emails.return_value = [{"id": "1"}]
    # Missing fields that production code expects!
```

#### ✅ DO: Verify mock interactions

```python
def test_verify_mock_calls():
    mock_ai = Mock()
    mock_ai.classify_email.return_value = {"category": "work"}
    
    processor = EmailProcessor(mock_ai)
    processor.process_email({"subject": "Test", "body": "Content"})
    
    # Verify the mock was called with correct arguments
    mock_ai.classify_email.assert_called_once()
    call_args = mock_ai.classify_email.call_args
    assert "subject" in call_args[0][0]  # Email data passed to mock
```

#### ✅ DO: Test error conditions with mocks

```python
def test_handle_ai_service_failure():
    """Test graceful error handling when AI service fails."""
    mock_ai = Mock()
    mock_ai.classify_email.side_effect = TimeoutError("AI service timeout")
    
    processor = EmailProcessor(mock_ai)
    result = processor.process_email({"subject": "Test", "body": "Content"})
    
    # Verify fallback behavior
    assert result["category"] == "uncategorized"
    assert "error" in result
```

### Frontend Mocking (TypeScript/JavaScript)

```typescript
// Mock API responses in E2E tests
test('should display emails from mocked API', async ({ page }) => {
  // Intercept API call and return mock data
  await page.route('**/api/emails', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        emails: [
          {
            id: 'email-1',
            subject: 'Test Email',
            body: 'Test body content',
            from: 'sender@test.com'
          }
        ]
      })
    });
  });
  
  await page.goto('/');
  await expect(page.locator('[data-testid="email-item"]')).toHaveCount(1);
});
```

---

## Test Naming Conventions

### General Rules

1. **Use descriptive names that explain what is being tested**
2. **Follow the pattern: `test_<what>_<condition>_<expected_result>`**
3. **Use snake_case for Python tests**
4. **Use camelCase for TypeScript/JavaScript tests**
5. **Start test files with `test_` prefix (Python) or end with `.spec.ts` / `.test.ts` (TypeScript)**

### Python Test Naming

```python
# ✅ GOOD - Clear, descriptive names
def test_classify_email_with_action_items_returns_required_action_category():
    """When email contains action items, classify as required_personal_action."""
    pass

def test_save_email_to_database_creates_new_record():
    """Saving a new email should create a database record."""
    pass

def test_get_emails_when_outlook_disconnected_raises_connection_error():
    """Getting emails while disconnected should raise ConnectionError."""
    pass

# ❌ BAD - Vague, unclear names
def test_email():
    """What about email? What's being tested?"""
    pass

def test_classification():
    """Classification of what? What's the expected result?"""
    pass

def test_database():
    """Too generic - what database operation?"""
    pass
```

### Test Class Naming

```python
# ✅ GOOD - Grouped by component or feature
class TestEmailClassification:
    """Tests for email classification functionality."""
    
    def test_classify_work_email_returns_work_relevant(self):
        pass
    
    def test_classify_spam_email_returns_spam(self):
        pass
    
    def test_classify_with_low_confidence_returns_uncategorized(self):
        pass

class TestDatabaseOperations:
    """Tests for database CRUD operations."""
    
    def test_insert_email_creates_record(self):
        pass
    
    def test_update_email_modifies_existing_record(self):
        pass
    
    def test_delete_email_removes_record(self):
        pass
```

### Frontend Test Naming (TypeScript)

```typescript
// ✅ GOOD - Descriptive test names
describe('Email Processing Workflow', () => {
  test('should retrieve and display emails from backend', async () => {
    // ...
  });
  
  test('should classify email when classify button is clicked', async () => {
    // ...
  });
  
  test('should show error message when classification fails', async () => {
    // ...
  });
});

// ❌ BAD - Vague names
describe('Emails', () => {
  test('test 1', async () => {
    // What does test 1 do?
  });
  
  test('works', async () => {
    // What works?
  });
});
```

### Test File Naming

```
# Python Backend Tests
backend/tests/
  ├── test_ai_service.py           # Tests for AIService class
  ├── test_email_provider.py       # Tests for EmailProvider implementations
  ├── test_email_api.py            # Tests for email API endpoints
  └── integration/
      └── test_full_workflow_integration.py  # End-to-end workflow tests

# Frontend Tests
frontend/tests/
  ├── e2e/
  │   ├── email-processing.spec.ts     # E2E tests for email processing
  │   ├── task-management.spec.ts      # E2E tests for task management
  │   └── settings.spec.ts             # E2E tests for settings page
  └── unit/
      ├── EmailList.test.tsx           # Unit tests for EmailList component
      └── TaskCard.test.tsx            # Unit tests for TaskCard component
```

### Docstring Conventions

```python
def test_classify_email_with_high_importance_prioritizes_correctly():
    """Test that emails marked as high importance receive higher priority.
    
    This test verifies the priority calculation logic when an email is marked
    as high importance by the sender. High importance emails should receive
    a priority boost regardless of their content classification.
    
    Expected behavior:
    - High importance email without action items: priority = 8
    - High importance email with action items: priority = 10
    """
    # Test implementation
```

---

## Coverage Expectations

### Overall Project Coverage Goals

| Module | Target Coverage | Priority | Notes |
|--------|----------------|----------|-------|
| **Core Business Logic** | 90-95% | Critical | ai_processor.py, email_classification_service.py |
| **Service Layer** | 85-90% | High | ai_service.py, email_provider.py, task_service.py |
| **API Endpoints** | 80-85% | High | All FastAPI routes and handlers |
| **Data Models** | 70-80% | Medium | Pydantic models, validation logic |
| **Utilities** | 75-85% | Medium | Helper functions, formatters |
| **UI Components** | 60-70% | Medium | React components (focus on logic, not styling) |

### Coverage by Test Type

```
Unit Tests:        50-60% of total coverage
Integration Tests: 30-35% of total coverage
E2E Tests:         10-15% of total coverage
```

### What to Prioritize for Coverage

#### High Priority (Must be tested)

1. **Business logic** - Classification, priority calculation, action item extraction
2. **Data validation** - Input validation, data structure checks
3. **Error handling** - Exception handling, fallback behavior
4. **Database operations** - CRUD operations, queries
5. **API endpoints** - All public API routes
6. **Critical user paths** - Email retrieval, classification, task creation

#### Medium Priority (Should be tested)

1. **Utility functions** - Formatters, parsers, helpers
2. **Configuration loading** - Settings, environment variables
3. **Service initialization** - Dependency injection, setup
4. **UI components with logic** - Components with state or complex interactions

#### Low Priority (Nice to have)

1. **Simple getters/setters** - Trivial property access
2. **UI styling** - CSS, visual appearance (use visual regression tools instead)
3. **Third-party library wrappers** - If they're just pass-through calls
4. **Generated code** - Auto-generated models, migrations

### Running Coverage Reports

```bash
# Generate coverage for all test suites
npm run test:coverage

# View coverage reports
# Backend: runtime_data/coverage/backend/index.html
# Src: runtime_data/coverage/src/index.html
# Frontend: frontend/coverage/index.html
```

### Coverage Report Example

```bash
# Backend coverage report
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
backend/services/ai_service.py            145      8    94%
backend/services/email_provider.py         98     12    88%
backend/api/emails.py                     234     28    88%
backend/models/email.py                    45      3    93%
-----------------------------------------------------------
TOTAL                                    1523    127    92%
```

### Interpreting Coverage

- **90%+ coverage** = Excellent, comprehensive testing
- **80-89% coverage** = Good, most critical paths tested
- **70-79% coverage** = Acceptable, but gaps in testing
- **Below 70%** = Needs improvement, significant gaps

### Coverage Gaps to Address

```python
# Example: Coverage report shows line 45 not covered
def process_email_batch(emails: List[Dict]) -> List[Dict]:
    results = []
    for email in emails:
        try:
            result = process_email(email)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process email: {e}")
            # Line 45: This error path is not tested! ⚠️
            results.append({"id": email["id"], "error": str(e)})
    return results

# Add test for the uncovered error path
def test_process_email_batch_handles_individual_failures():
    """Test that batch processing continues after individual email failures."""
    emails = [
        {"id": "1", "subject": "Valid"},
        {"id": "2", "subject": None},  # Will cause error
        {"id": "3", "subject": "Valid"}
    ]
    
    results = process_email_batch(emails)
    
    assert len(results) == 3
    assert "error" in results[1]  # Middle email failed
    assert results[0]["processed"] is True  # First email succeeded
    assert results[2]["processed"] is True  # Third email succeeded
```

---

## Test Organization

### Directory Structure

```
email_helper/
├── backend/tests/              # Backend API and service tests
│   ├── conftest.py            # Shared fixtures
│   ├── fixtures/              # Reusable test fixtures
│   │   ├── email_fixtures.py  # Email test data
│   │   └── ai_response_fixtures.py  # AI response mocks
│   ├── integration/           # Integration tests
│   ├── api/                   # API endpoint tests
│   ├── test_*.py              # Test modules
│   └── utils.py               # Test utilities
│
├── frontend/tests/            # Frontend tests
│   ├── e2e/                   # End-to-end tests (Playwright)
│   │   ├── fixtures/          # E2E test fixtures
│   │   ├── *.spec.ts          # E2E test files
│   │   └── README.md
│   └── unit/                  # Unit tests (Vitest)
│       └── *.test.tsx
│
└── docs/testing/              # Testing documentation
    ├── TESTING_GUIDE.md       # This file
    └── EXAMPLES.md            # Additional examples
```

### Organizing Tests by Feature

```python
# backend/tests/test_email_classification.py
"""Tests for email classification feature."""

class TestEmailClassificationBasic:
    """Basic classification tests."""
    def test_classify_work_email(self): pass
    def test_classify_personal_email(self): pass
    def test_classify_spam_email(self): pass

class TestEmailClassificationEdgeCases:
    """Edge cases and error conditions."""
    def test_classify_empty_email(self): pass
    def test_classify_very_long_email(self): pass
    def test_classify_with_special_characters(self): pass

class TestEmailClassificationIntegration:
    """Integration tests with dependencies."""
    def test_classify_with_real_ai_service(self): pass
    def test_classify_and_save_to_database(self): pass
```

---

## Running Tests

### Quick Reference

```bash
# Run all tests
npm test

# Run specific test suite
npm run test:backend          # Backend Python tests
npm run test:src              # Src Python tests
npm run test:frontend         # Frontend unit tests
npm run test:e2e              # Frontend E2E tests

# Run with coverage
npm run test:coverage

# Run specific test file
python -m pytest backend/tests/test_ai_service.py
cd frontend && npx playwright test email-processing.spec.ts

# Run specific test by name
python -m pytest -k "test_classify_email"
cd frontend && npx playwright test -g "should retrieve emails"

# Run tests with markers
python -m pytest -m "unit and fast"      # Only fast unit tests
python -m pytest -m "integration"        # Only integration tests
python -m pytest -m "not slow"           # Skip slow tests

# Run in watch mode (frontend)
cd frontend && npm run test:watch
```

### Advanced pytest Options

```bash
# Run with verbose output
python -m pytest -v

# Stop on first failure
python -m pytest -x

# Run last failed tests
python -m pytest --lf

# Run tests in parallel (requires pytest-xdist)
python -m pytest -n auto

# Show print statements
python -m pytest -s

# Show coverage for specific module
python -m pytest --cov=backend.services.ai_service --cov-report=term-missing
```

---

## Best Practices

### 1. Arrange-Act-Assert Pattern

```python
def test_email_classification_with_action_items():
    # ARRANGE - Set up test data and dependencies
    email = {
        "subject": "Action Required: Complete Survey",
        "body": "Please complete by Friday"
    }
    mock_ai = MockFactory.create_ai_service(
        classification="required_personal_action",
        confidence=0.95
    )
    processor = EmailProcessor(mock_ai)
    
    # ACT - Perform the action being tested
    result = processor.process_email(email)
    
    # ASSERT - Verify the expected outcome
    assert result["category"] == "required_personal_action"
    assert result["confidence"] > 0.9
    assert "action_items" in result
```

### 2. One Assertion Per Test (When Possible)

```python
# ✅ GOOD - Focused test with single logical assertion
def test_high_importance_email_gets_priority_boost():
    email = {"importance": "high", "has_action_items": False}
    priority = calculate_priority(email)
    assert priority == 8

# ✅ ALSO GOOD - Multiple assertions testing same logical condition
def test_email_validation_checks_all_required_fields():
    email = {"id": "1", "subject": "Test", "body": "Content", "from": "sender@test.com"}
    assert validate_email(email) is True
    assert "id" in email
    assert "subject" in email
    assert "body" in email

# ❌ BAD - Testing multiple unrelated things
def test_email_processing():
    # Testing too many things in one test
    assert classify_email(email1) == "work"
    assert save_to_database(email1) is True
    assert send_notification(email1) is True
    assert update_ui(email1) is True
    # If this fails, which part failed?
```

### 3. Test Independence

```python
# ✅ GOOD - Each test is independent
def test_create_email():
    email = EmailFactory.create()
    assert email["id"] is not None

def test_update_email():
    email = EmailFactory.create()  # Create fresh data
    updated = update_email(email, {"subject": "New Subject"})
    assert updated["subject"] == "New Subject"

# ❌ BAD - Tests depend on order
class TestEmailFlow:
    email_id = None
    
    def test_1_create_email(self):
        email = create_email()
        self.email_id = email["id"]  # Shared state!
    
    def test_2_update_email(self):
        # Fails if test_1 didn't run or failed
        update_email(self.email_id, {"subject": "New"})
```

### 4. Use Fixtures for Common Setup

```python
# ✅ GOOD - Reusable fixture
@pytest.fixture
def authenticated_client():
    """Create authenticated API client."""
    client = TestClient(app)
    client.headers["Authorization"] = "Bearer test_token"
    return client

def test_get_emails_authenticated(authenticated_client):
    response = authenticated_client.get("/api/emails")
    assert response.status_code == 200

def test_create_task_authenticated(authenticated_client):
    response = authenticated_client.post("/api/tasks", json={"title": "Test"})
    assert response.status_code == 201
```

### 5. Test Error Conditions

```python
def test_classify_email_handles_ai_service_timeout():
    """Verify graceful handling of AI service timeout."""
    mock_ai = Mock()
    mock_ai.classify_email.side_effect = TimeoutError("Service timeout")
    
    processor = EmailProcessor(mock_ai)
    result = processor.process_email({"subject": "Test", "body": "Content"})
    
    assert result["category"] == "uncategorized"
    assert result["error"] == "AI service timeout"
    assert result["fallback_used"] is True

def test_get_emails_when_outlook_not_installed():
    """Verify clear error when Outlook is not available."""
    with patch('win32com.client.Dispatch', side_effect=ImportError):
        provider = COMEmailProvider()
        with pytest.raises(RuntimeError, match="Outlook not available"):
            provider.connect()
```

### 6. Parameterized Tests for Multiple Cases

```python
@pytest.mark.parametrize("email_type,expected_category", [
    ("work_meeting", "required_personal_action"),
    ("newsletter", "newsletter"),
    ("notification", "notification"),
    ("spam", "spam"),
    ("personal", "personal"),
])
def test_email_classification_types(email_type, expected_category):
    """Test classification of various email types."""
    email = EmailFactory.create(type=email_type)
    result = classify_email(email)
    assert result["category"] == expected_category
```

### 7. Clear Test Data

```python
# ✅ GOOD - Obvious test data
def test_spam_detection():
    spam_email = {
        "subject": "BUY NOW! Limited Time Offer!!!",
        "body": "Click here to claim your prize: http://suspicious-link.com"
    }
    assert classify_email(spam_email)["category"] == "spam"

# ❌ BAD - Unclear what makes this spam
def test_spam_detection():
    email = {"subject": "Hi", "body": "Test"}
    assert classify_email(email)["category"] == "spam"
    # Why is "Hi" / "Test" considered spam?
```

### 8. Meaningful Test Descriptions

```python
# ✅ GOOD - Docstring explains the test
def test_batch_processing_continues_after_individual_failures():
    """Test that batch email processing continues even if individual emails fail.
    
    When processing a batch of emails, if one email fails to process (e.g., due
    to invalid data or service timeout), the batch processor should log the error,
    mark that email as failed, and continue processing the remaining emails.
    
    This ensures that one bad email doesn't block processing of the entire batch.
    """
    # Test implementation
```

---

## Common Patterns

### Pattern: Testing Async Functions

```python
import pytest

@pytest.mark.asyncio
async def test_async_email_classification():
    """Test async classification with proper async/await."""
    mock_ai = AsyncMock()
    mock_ai.classify_email_async.return_value = {
        "category": "work_relevant",
        "confidence": 0.88
    }
    
    service = AIService(mock_ai)
    result = await service.classify_email_async("Test email")
    
    assert result["category"] == "work_relevant"
    mock_ai.classify_email_async.assert_awaited_once()
```

### Pattern: Testing Database Transactions

```python
def test_database_rollback_on_error(database_with_schema):
    """Test that database rolls back on error."""
    try:
        with database_with_schema:
            cursor = database_with_schema.cursor()
            cursor.execute("INSERT INTO emails (id, subject) VALUES (?, ?)", ("1", "Test"))
            # Simulate error
            raise ValueError("Simulated error")
    except ValueError:
        pass
    
    # Verify rollback happened
    cursor = database_with_schema.cursor()
    cursor.execute("SELECT * FROM emails WHERE id = ?", ("1",))
    assert cursor.fetchone() is None  # Should be rolled back
```

### Pattern: Testing with Fixtures

```python
@pytest.fixture
def sample_emails():
    """Provide sample email data for tests."""
    return [
        {"id": "1", "subject": "Meeting", "body": "Team sync tomorrow"},
        {"id": "2", "subject": "Newsletter", "body": "Weekly updates"},
        {"id": "3", "subject": "Action Required", "body": "Complete survey"}
    ]

def test_batch_classification(sample_emails, mock_ai_service):
    """Test classifying multiple emails."""
    processor = EmailProcessor(mock_ai_service)
    results = processor.process_batch(sample_emails)
    
    assert len(results) == 3
    assert all("category" in result for result in results)
```

### Pattern: Testing API Endpoints

```python
from fastapi.testclient import TestClient

def test_get_emails_endpoint(client, mock_email_provider):
    """Test GET /api/emails endpoint."""
    # Arrange
    mock_email_provider.get_emails.return_value = [
        {"id": "1", "subject": "Test Email"}
    ]
    
    # Act
    response = client.get("/api/emails")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "emails" in data
    assert len(data["emails"]) == 1
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: Tests fail with import errors

**Solution:**
```bash
# Ensure virtual environment is activated
.venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
cd frontend && npm install
```

#### Issue: Fixtures not found

**Solution:**
- Verify `conftest.py` is in the correct directory
- Check that fixture is defined before being used
- Ensure fixture has `@pytest.fixture` decorator

```python
# conftest.py must be in the same directory or parent directory
@pytest.fixture
def my_fixture():
    return "test_data"
```

#### Issue: Async tests fail

**Solution:**
```python
# Must use @pytest.mark.asyncio
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

#### Issue: Mock not being called

**Solution:**
```python
# Ensure you're patching the correct import path
# Patch where it's used, not where it's defined

# ❌ WRONG - Patching where defined
@patch('src.ai_processor.AIOrchestrator')

# ✅ CORRECT - Patching where imported and used
@patch('backend.services.ai_service.AIOrchestrator')
```

#### Issue: Database tests interfering with each other

**Solution:**
```python
# Use fixtures with proper cleanup
@pytest.fixture
def clean_database():
    db = create_test_database()
    yield db
    db.execute("DELETE FROM emails")  # Clean up after test
    db.close()
```

#### Issue: E2E tests timing out

**Solution:**
```typescript
// Increase timeout for slow operations
test('slow operation', async ({ page }) => {
  await page.goto('/', { timeout: 60000 }); // 60 second timeout
  await page.waitForSelector('[data-testid="email-item"]', { 
    timeout: 30000 
  });
});
```

---

## Additional Resources

### Documentation Links

- [Backend Testing Guide](../../backend/tests/README.md)
- [Frontend E2E Testing Guide](../../frontend/tests/e2e/README.md)
- [Test Runner Documentation](../technical/TEST_RUNNER.md)
- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/)

### Example Test Files

**Backend:**
- `backend/tests/test_ai_service.py` - Service layer tests
- `backend/tests/test_email_api.py` - API endpoint tests
- `backend/tests/integration/test_full_workflow_integration.py` - Integration tests

**Frontend:**
- `frontend/tests/e2e/email-processing.spec.ts` - E2E workflow tests
- `frontend/tests/e2e/task-management.spec.ts` - Task management tests

### Running Tests

```bash
# Quick start - run all tests
npm test

# Development - skip slow E2E tests
.\run-all-tests.ps1 -SkipE2E

# Full test suite with coverage
npm run test:coverage
```

---

## Summary

This guide covers the essential testing strategies for the Email Helper project:

1. **Unit tests** for fast, focused testing of individual functions
2. **Integration tests** for component interactions and database operations
3. **E2E tests** for complete user workflows
4. **Effective mocking** to isolate dependencies and speed up tests
5. **Clear naming conventions** for maintainable test suites
6. **Coverage targets** to ensure critical paths are tested
7. **Best practices** for writing reliable, maintainable tests

**Key Takeaway:** Write tests that are fast, reliable, and clearly communicate intent. Use the testing pyramid to balance unit, integration, and E2E tests. Mock external dependencies, but test your own logic thoroughly.

For questions or suggestions, refer to the project's CONTRIBUTING.md or create an issue.
