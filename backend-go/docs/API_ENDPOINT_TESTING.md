# API Endpoint Testing Guide

## Overview

This document describes the comprehensive API endpoint testing suite for the Email Helper Go backend. The test script (`test-endpoints.ps1`) validates all API endpoints defined in `api-spec.yml` with real Azure OpenAI credentials.

## Quick Start

### Prerequisites

1. **Go Backend Running**: Start the backend server
   ```powershell
   go run cmd/api/main.go
   # Or using make
   make run
   ```

2. **Azure OpenAI Configured**: Ensure Azure OpenAI credentials are set in your environment or database settings

### Running Tests

```powershell
# Run all tests (default: http://localhost:8000)
.\test-endpoints.ps1

# Run with verbose output
.\test-endpoints.ps1 -Verbose

# Run against different base URL
.\test-endpoints.ps1 -BaseUrl "http://localhost:8080"

# Skip AI tests (if Azure OpenAI not configured)
.\test-endpoints.ps1 -SkipAI
```

## Test Coverage

### 1. Health & Status Endpoints

| Endpoint | Method | Status | Validates |
|----------|--------|--------|-----------|
| `/health` | GET | ✓ | Service health status, database connection |
| `/` | GET | ✓ | API root information, version, links |

**Expected Response Format:**
```json
{
  "status": "healthy",
  "service": "email-helper-api",
  "version": "1.0.0",
  "database": "healthy"
}
```

### 2. AI Processing Endpoints

| Endpoint | Method | Status | Validates |
|----------|--------|--------|-----------|
| `/api/ai/health` | GET | ✓ | Azure OpenAI connectivity |
| `/api/ai/classify` | POST | ✓ | Email classification with category & confidence |
| `/api/ai/action-items` | POST | ✓ | Action item extraction with urgency |
| `/api/ai/summarize` | POST | ✓ | Email summarization (brief/detailed) |
| `/api/ai/templates` | GET | ✓ | Available prompt templates list |

**Classification Test:**
```json
{
  "subject": "Team meeting tomorrow at 2 PM",
  "sender": "manager@company.com",
  "content": "Hi team, please join us for our weekly sync...",
  "context": ""
}
```

**Expected Classification Response:**
```json
{
  "category": "required_personal_action",
  "confidence": 0.85,
  "reasoning": "Meeting invitation requires attendance",
  "one_line_summary": "Weekly team sync tomorrow at 2 PM"
}
```

**Action Items Test:**
```json
{
  "email_content": "Please review the proposal by Friday and update Jira.",
  "context": ""
}
```

**Expected Action Items Response:**
```json
{
  "action_items": ["Review proposal", "Update Jira timeline"],
  "urgency": "medium",
  "deadline": "2024-11-01",
  "confidence": 0.8
}
```

### 3. Email Management Endpoints

| Endpoint | Method | Status | Validates |
|----------|--------|--------|-----------|
| `/api/emails` | GET | ✓ | Pagination, filtering, email list |
| `/api/emails/stats` | GET | ✓ | Email statistics (total, unread, by folder) |
| `/api/emails/search` | GET | ✓ | Search functionality with query params |
| `/api/emails/:id` | GET | ✓ | Specific email retrieval |
| `/api/folders` | GET | ✓ | Outlook folder list |

**Email List Parameters:**
- `folder`: Folder name (default: Inbox)
- `limit`: Max results (1-50000, default: 50)
- `offset`: Skip count (default: 0)
- `category`: Filter by category
- `source`: outlook or database (default: outlook)

**Expected Email List Response:**
```json
{
  "emails": [...],
  "total": 150,
  "offset": 0,
  "limit": 50,
  "has_more": true
}
```

**Expected Stats Response:**
```json
{
  "total_emails": 1500,
  "unread_emails": 45,
  "emails_by_folder": {
    "Inbox": 100,
    "Sent": 500
  },
  "emails_by_sender": {
    "manager@company.com": 25
  }
}
```

### 4. Task Management Endpoints

| Endpoint | Method | Status | Validates |
|----------|--------|--------|-----------|
| `/api/tasks` | GET | ✓ | Pagination, filtering, task list |
| `/api/tasks` | POST | ✓ | Task creation with all fields |
| `/api/tasks/stats` | GET | ✓ | Task statistics (total, by status/priority) |
| `/api/tasks/:id` | GET | ✓ | Specific task retrieval |
| `/api/tasks/:id` | PUT | ✓ | Task update (status, fields) |
| `/api/tasks/:id` | DELETE | ✓ | Task deletion |

**Create Task Test:**
```json
{
  "title": "Test Task - API Validation",
  "description": "Created by endpoint testing script",
  "status": "pending",
  "priority": "medium",
  "category": "testing"
}
```

**Expected Task Response:**
```json
{
  "id": 123,
  "title": "Test Task - API Validation",
  "status": "pending",
  "priority": "medium",
  "category": "testing",
  "created_at": "2024-10-31T15:30:00Z",
  "updated_at": "2024-10-31T15:30:00Z"
}
```

**Update Task Test:**
```json
{
  "title": "Test Task - Updated",
  "status": "in_progress"
}
```

**Expected Stats Response:**
```json
{
  "total_tasks": 45,
  "pending_tasks": 12,
  "completed_tasks": 20,
  "overdue_tasks": 3,
  "tasks_by_priority": {
    "high": 5,
    "medium": 30,
    "low": 10
  }
}
```

### 5. Settings Management Endpoints

| Endpoint | Method | Status | Validates |
|----------|--------|--------|-----------|
| `/api/settings` | GET | ✓ | User settings retrieval |
| `/api/settings` | PUT | ✓ | Settings update |
| `/api/settings` | DELETE | ✓ | Reset to defaults |

**Expected Settings Response:**
```json
{
  "username": "user",
  "job_context": "Software Engineer",
  "newsletter_interests": "tech,ai",
  "azure_openai_endpoint": "https://...",
  "azure_openai_deployment": "gpt-4"
}
```

### 6. Processing Pipeline Endpoints

| Endpoint | Method | Status | Validates |
|----------|--------|--------|-----------|
| `/api/processing/stats` | GET | ✓ | Pipeline statistics |
| `/api/processing/start` | POST | ⊘ | Skipped (avoids processing real data) |

## Test Workflow

### Full Test Cycle

1. **Health Check**: Verify service is running and database is connected
2. **AI Service Check**: Validate Azure OpenAI connectivity
3. **Email Operations**: 
   - List emails with pagination
   - Get email statistics
   - Search emails
   - Retrieve specific email
   - List folders
4. **Task Operations**:
   - Create test task
   - Get task by ID
   - Update task status
   - Delete task
   - Get task statistics
5. **Settings Operations**:
   - Retrieve current settings
   - Update settings
6. **Processing Stats**: Check pipeline statistics

### Test Execution Flow

```
┌─────────────────────┐
│  Start Test Suite   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Health Endpoints   │  ← Verify service is running
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   AI Endpoints      │  ← Test Azure OpenAI integration
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Email Endpoints    │  ← Test email management
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Task Endpoints    │  ← Test task CRUD operations
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Settings Endpoints  │  ← Test settings management
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Processing Stats    │  ← Test pipeline stats
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Generate Report    │  ← Save results to JSON
└─────────────────────┘
```

## Output

### Console Output

```
═══════════════════════════════════════════════════════════════
  Health & Status Endpoints
═══════════════════════════════════════════════════════════════
[15:30:01] ✓ GET /health
[15:30:01] ✓ GET /

═══════════════════════════════════════════════════════════════
  AI Processing Endpoints
═══════════════════════════════════════════════════════════════
[15:30:02] ✓ GET /api/ai/health
[15:30:04] ✓ POST /api/ai/classify
    Category: required_personal_action (confidence: 0.85)
[15:30:06] ✓ POST /api/ai/action-items
    Action Items: Review proposal, Update Jira timeline
[15:30:08] ✓ POST /api/ai/summarize
    Summary: Q4 planning discussion with budget, capacity, and OKRs
[15:30:09] ✓ GET /api/ai/templates

═══════════════════════════════════════════════════════════════
  Test Summary
═══════════════════════════════════════════════════════════════

  Total Tests:   25
  ✓ Passed:      23
  ✗ Failed:      0
  ⊘ Skipped:     2

  Duration:      12.45 seconds

  Results saved to: test-results-20241031-153010.json
```

### JSON Report

The test script generates a JSON report with detailed results:

```json
{
  "summary": {
    "total": 25,
    "passed": 23,
    "failed": 0,
    "skipped": 2,
    "duration_seconds": 12.45
  },
  "base_url": "http://localhost:8000",
  "timestamp": "2024-10-31T15:30:10Z",
  "tests": [
    {
      "Name": "GET /health",
      "Status": "PASS",
      "Message": "",
      "Timestamp": "15:30:01"
    },
    ...
  ]
}
```

## Validation Criteria

### Response Format Validation

Each endpoint test validates:

1. **Status Code**: Matches expected HTTP status (200, 201, etc.)
2. **Response Structure**: Contains required fields per API spec
3. **Data Types**: Fields have correct types (string, number, boolean, array, object)
4. **Business Logic**: Values make sense (e.g., confidence between 0-1)

### AI Endpoint Validation

- **Classification**: Category is valid enum value, confidence is 0-1
- **Action Items**: Returns array of action items with metadata
- **Summarization**: Returns non-empty summary string
- **Templates**: Returns array of available template names

### Email Endpoint Validation

- **Email List**: Returns array with pagination metadata
- **Stats**: Returns numeric counts and breakdown objects
- **Search**: Returns filtered results matching query
- **Email Detail**: Returns complete email object with all fields

### Task Endpoint Validation

- **Task Creation**: Returns new task with generated ID
- **Task Update**: Returns updated task with modified fields
- **Task Deletion**: Returns success confirmation
- **Task Stats**: Returns numeric aggregations

## Troubleshooting

### Common Issues

**Issue: AI tests fail with "AI service unavailable"**
```
Solution: Verify Azure OpenAI credentials in settings
- Check AZURE_OPENAI_ENDPOINT environment variable
- Verify AZURE_OPENAI_API_KEY is set
- Run: .\test-endpoints.ps1 -SkipAI to skip AI tests
```

**Issue: Email endpoints return empty lists**
```
Solution: Ensure Outlook is running and COM backend is enabled
- Start Outlook application
- Verify UseComBackend=true in config
- Check emails exist in Inbox folder
```

**Issue: Connection refused errors**
```
Solution: Ensure backend is running
- Run: go run cmd/api/main.go
- Check server is listening on correct port
- Verify no firewall blocking localhost:8000
```

**Issue: All tests timeout**
```
Solution: Increase timeout or check server performance
- Backend may be processing large email volume
- Check CPU/memory usage
- Consider reducing concurrent requests
```

## Continuous Integration

### GitHub Actions Integration

```yaml
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      
      - name: Start Backend
        run: |
          go run cmd/api/main.go &
          Start-Sleep -Seconds 5
      
      - name: Run API Tests
        run: .\test-endpoints.ps1 -SkipAI
      
      - name: Upload Test Results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results-*.json
```

## Future Enhancements

### Planned Improvements

1. **Schema Validation**: Add JSON schema validation for all responses
2. **Performance Testing**: Add latency measurements and benchmarking
3. **Load Testing**: Test concurrent request handling
4. **Error Testing**: Add negative test cases for error scenarios
5. **Authentication**: Add tests for auth flows when implemented
6. **WebSocket Tests**: Add WebSocket endpoint testing
7. **Database State**: Verify database state changes after operations
8. **Cleanup**: Automatic cleanup of test data after completion

### Additional Test Scenarios

- **Batch Operations**: Test bulk email classification
- **Error Handling**: Test invalid inputs and edge cases
- **Rate Limiting**: Test API rate limits if implemented
- **Concurrent Requests**: Test thread safety
- **Large Data**: Test with large email/task volumes
- **Edge Cases**: Empty strings, null values, boundary conditions

## References

- **API Specification**: [api-spec.yml](../api-spec.yml)
- **Backend Code**: [cmd/api/main.go](../cmd/api/main.go)
- **Test Runner**: [TEST_RUNNER.md](../TEST_RUNNER.md)
- **Configuration**: [config/config.go](../config/config.go)
