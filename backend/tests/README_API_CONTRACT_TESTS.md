# API Contract Tests

This test suite provides comprehensive contract testing for all FastAPI endpoints in the Email Helper backend.

## Overview

The `test_api_contract.py` file contains contract tests that verify:
- **Request/Response Schema Compliance**: Validates that all endpoints accept and return data matching their OpenAPI specifications
- **Error Handling**: Tests proper HTTP status codes for various error scenarios (400, 404, 422, 500)
- **Endpoint Coverage**: Tests all major API routes including emails, tasks, AI processing, settings, and processing pipelines
- **CORS Configuration**: Validates CORS headers and cross-origin request handling
- **OpenAPI Documentation**: Ensures OpenAPI/Swagger documentation is accessible

## Test Coverage

### Health & Root Endpoints (2 tests)
- ✅ `/health` - Health check endpoint
- ✅ `/` - Root API information endpoint

### Email Endpoints (10 tests)
- ✅ `GET /api/emails` - List emails with pagination and filtering
- ✅ `GET /api/emails/{id}` - Get single email (skipped due to COM threading)
- ✅ `GET /api/folders` - List email folders
- ✅ `PUT /api/emails/{id}/classification` - Update email classification
- ✅ `POST /api/emails/bulk-apply-to-outlook` - Bulk apply classifications
- Tests for invalid inputs and error handling

### AI Processing Endpoints (5 tests)
- ✅ `POST /api/ai/classify` - Classify email content
- ⏭️ `POST /api/ai/action-items` - Extract action items (skipped - requires API keys)
- ⏭️ `POST /api/ai/summarize` - Generate email summary (skipped - requires API keys)
- ✅ Schema validation tests for request/response models

### Task Management Endpoints (8 tests)
- ✅ `POST /api/tasks` - Create new task
- ✅ `GET /api/tasks` - List tasks with pagination and filters
- ⏭️ `GET /api/tasks/{id}` - Get single task (skipped - requires DB)
- ⏭️ `PUT /api/tasks/{id}` - Update task (skipped - requires DB)
- ⏭️ `DELETE /api/tasks/{id}` - Delete task (skipped - requires DB)
- ✅ `GET /api/tasks/stats` - Get task statistics

### Settings Endpoints (2 tests)
- ✅ `GET /api/settings` - Get user settings
- ✅ `PUT /api/settings` - Update user settings

### Processing Pipeline Endpoints (2 tests)
- ⏭️ `POST /api/processing/start` - Start processing pipeline (skipped - complex dependencies)
- ⏭️ `GET /api/processing/{id}/status` - Get pipeline status (skipped - complex dependencies)

### Error Handling (3 tests)
- ✅ 404 Not Found responses
- ✅ 405 Method Not Allowed responses
- ✅ 422 Validation Error responses
- ⏭️ 500 Internal Server Error (skipped - difficult to mock)

### OpenAPI & Documentation (3 tests)
- ✅ OpenAPI schema accessibility
- ✅ `/docs` Swagger UI endpoint
- ✅ `/redoc` ReDoc endpoint

### CORS (2 tests)
- ✅ CORS header presence
- ✅ Cross-origin request handling

## Test Statistics

- **Total Tests**: 41
- **Passing**: 32 (78%)
- **Skipped**: 9 (22%)
- **Failing**: 0 (0%)

## Running the Tests

### Run all contract tests:
```bash
pytest backend/tests/test_api_contract.py -v
```

### Run specific test class:
```bash
pytest backend/tests/test_api_contract.py::TestEmailEndpoints -v
```

### Run with coverage:
```bash
pytest backend/tests/test_api_contract.py --cov=backend.api --cov-report=html
```

### Run without warnings:
```bash
pytest backend/tests/test_api_contract.py -v --disable-warnings
```

## Skipped Tests

Some tests are skipped due to environmental limitations:

1. **AI Service Tests** (action-items, summarize): Require real Azure OpenAI API keys
2. **Task CRUD Tests** (get/update/delete): Require database with pre-populated test data
3. **Processing Pipeline Tests**: Require complex job queue and worker setup
4. **500 Error Test**: Difficult to trigger with mocked dependencies

These can be enabled by:
- Setting up proper test fixtures with database data
- Configuring test API keys in environment
- Implementing better dependency injection mocking

## Test Architecture

### Fixtures

- `client`: FastAPI TestClient for making HTTP requests
- `mock_email_provider`: Mock email service provider
- `mock_ai_service`: Mock AI processing service
- `mock_task_service`: Mock task management service
- `mock_processing_service`: Mock email processing service

### Mocking Strategy

Tests use `unittest.mock` to mock external dependencies:
- Database connections
- Email providers (Outlook COM)
- AI services (Azure OpenAI)
- Job queues and workers

### Request Validation

All tests verify:
- Correct HTTP status codes
- Response schema matches OpenAPI specification
- Required fields are present
- Data types are correct
- Error messages are descriptive

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
- Fast execution (<15 seconds)
- No external API dependencies (with mocks)
- Deterministic results
- Clear failure messages

## Future Improvements

1. Add integration tests with real database
2. Add performance/load testing
3. Add authentication/authorization tests
4. Improve mocking to enable skipped tests
5. Add WebSocket endpoint tests
6. Add rate limiting tests

## Dependencies

- `pytest`: Test framework
- `fastapi.testclient`: HTTP client for testing FastAPI apps
- `unittest.mock`: Mocking framework
- `pydantic`: Data validation

## Related Documentation

- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Backend API Documentation](../docs/API.md)
