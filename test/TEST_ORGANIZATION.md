# Test Organization Guide

## Overview
This directory contains all tests for the Email Helper application, organized by component and test type.

## Directory Structure

### Core Component Tests
Tests for individual system components:

- **test_ai_processor_enhanced.py** - AI processing and Azure OpenAI integration tests
- **test_classification_improvements.py** - Email classification accuracy tests
- **test_accuracy_tracking.py** - Accuracy tracker functionality tests
- **test_accuracy.py** - General accuracy measurement tests
- **test_accuracy_dashboard_integration.py** - Accuracy dashboard UI integration
- **test_accuracy_dashboard_data.py** - Accuracy dashboard data processing

### Feature-Specific Tests
Tests for specific features:

- **test_deduplication.py** - Basic action item deduplication tests
- **test_advanced_deduplication.py** - Advanced AI-powered deduplication tests
- **test_content_deduplication.py** - Content-based deduplication tests
- **test_integration_deduplication.py** - Integration tests for deduplication pipeline
- **test_new_categories.py** - Newsletter and job posting categorization tests
- **test_fyi_items.py** - FYI item processing tests
- **test_deferred_processing.py** - Deferred email processing tests
- **test_thread_email_moving.py** - Email thread movement tests
- **test_action_items_sync.py** - Action item synchronization tests
- **test_accepted_suggestions.py** - User suggestion acceptance tests
- **test_entryid_consistency.py** - Entry ID consistency validation tests

### Test Suites
Consolidated test runners:

- **consolidated_test_suite.py** - Main comprehensive test suite
- **core_test_suite.py** - Core functionality test suite
- **essential_tests.py** - Critical path tests for CI/CD

### UI Tests
User interface testing:

- **ui_test_framework.py** - UI testing framework and utilities
- **demo_ui_testing.py** - Demo UI tests
- **quick_ui_tests.py** - Fast UI smoke tests
- **simple_functionality_test.py** - Basic functionality UI tests
- **manual_gui_link_test.py** - Manual GUI link interaction test (requires human interaction)
- **manual_link_verification_test.py** - Manual link verification (requires human interaction)

### Test Configuration
- **conftest.py** - Pytest configuration and shared fixtures
- **test_data/** - Test data files and fixtures

### Backend Tests (Separate)
Backend API tests are located in `backend/tests/` and should remain separate:
- Authentication tests
- API endpoint tests
- Database tests
- Service layer tests

## Running Tests

### Run All Tests
```powershell
python -m pytest test/
```

### Run Specific Test Suite
```powershell
python -m pytest test/consolidated_test_suite.py
```

### Run Core Tests Only
```powershell
python -m pytest test/core_test_suite.py
```

### Run Essential Tests (Fast)
```powershell
python -m pytest test/essential_tests.py
```

### Run Tests by Component
```powershell
# AI Processor tests
python -m pytest test/test_ai_processor_enhanced.py

# Deduplication tests
python -m pytest test/test_*deduplication*.py

# Accuracy tests
python -m pytest test/test_accuracy*.py
```

### Run Tests with Coverage
```powershell
python -m pytest test/ --cov=src --cov-report=html
```

## Test Categories

### Unit Tests
Tests that verify individual functions or methods in isolation:
- test_ai_processor_enhanced.py
- test_classification_improvements.py
- test_content_deduplication.py

### Integration Tests
Tests that verify components working together:
- test_integration_deduplication.py
- test_accuracy_dashboard_integration.py
- test_action_items_sync.py

### UI Tests
Tests that verify user interface functionality:
- ui_test_framework.py
- demo_ui_testing.py
- quick_ui_tests.py

### Manual Tests
Tests requiring human interaction:
- manual_gui_link_test.py
- manual_link_verification_test.py

## Test Naming Conventions

- **test_*.py** - Automated pytest tests
- **manual_*.py** - Manual tests requiring human interaction
- **core_*.py** - Core functionality test suites
- **essential_*.py** - Critical path tests

## Adding New Tests

1. **Component Tests**: Add to `test_<component>_<feature>.py`
2. **Integration Tests**: Add to `test_integration_<feature>.py`
3. **UI Tests**: Add to `ui_test_framework.py` or create new file
4. **Update Suites**: Add to appropriate test suite file

## Test Best Practices

1. **Use Fixtures**: Define reusable test fixtures in `conftest.py`
2. **Mock External Dependencies**: Mock Outlook COM, Azure OpenAI, file I/O
3. **Test Data**: Store test data in `test_data/` directory
4. **Descriptive Names**: Use clear, descriptive test function names
5. **Documentation**: Add docstrings explaining test purpose
6. **Assertions**: Use specific assertions with clear failure messages

## CI/CD Integration

For continuous integration, run:
```powershell
python -m pytest test/essential_tests.py --junitxml=test-results.xml
```

This runs critical tests quickly without requiring Outlook or full environment setup.

## Notes

- Backend tests in `backend/tests/` are separate and use different dependencies
- Manual tests require GUI interaction and cannot run in CI/CD
- Some tests require Outlook COM interface (Windows only)
- Azure OpenAI tests may require valid API keys or mocking

## Maintenance

When cleaning up tests:
1. Check for duplicate test coverage
2. Remove obsolete tests after feature changes
3. Update test data when formats change
4. Keep test suites synchronized with new tests
5. Document breaking changes in test behavior
