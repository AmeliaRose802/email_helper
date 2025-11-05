# API Error Codes Reference

## Overview

The Email Helper API uses standard HTTP status codes combined with application-specific error codes to provide detailed error information. All errors follow a consistent JSON structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional context (optional)"
  }
}
```

## HTTP Status Codes

| Status Code | Meaning | When Used |
|-------------|---------|-----------|
| **200** | OK | Request succeeded |
| **201** | Created | Resource successfully created (e.g., new task) |
| **400** | Bad Request | Invalid request parameters or body |
| **404** | Not Found | Requested resource doesn't exist |
| **500** | Internal Server Error | Server encountered an error processing the request |
| **503** | Service Unavailable | Service or dependency is unavailable (e.g., database down, AI service offline) |

## Application Error Codes

### Validation Errors (400 Bad Request)

#### VALIDATION_ERROR
**Message:** "Missing required field: {field_name}" or "Invalid {field_name} value"

**Cause:** Request is missing required fields or contains invalid values.

**Examples:**
- Missing required field in email classification: `subject`, `sender`, or `content`
- Invalid category value not in allowed enum
- Invalid task status (must be: pending, in_progress, completed, cancelled)
- Invalid priority (must be: low, medium, high, urgent)

**Resolution:**
1. Check the API documentation for required fields
2. Verify all enum values match allowed options
3. Ensure field types match schema (e.g., integers for IDs, strings for text)

**Example Response:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Missing required field: subject",
    "details": "Request body must include subject, sender, and content"
  }
}
```

#### INVALID_PARAMETER
**Message:** "Invalid {parameter_name} value"

**Cause:** Query parameter value is outside allowed range or doesn't match expected format.

**Examples:**
- `limit` exceeds maximum of 50000
- `category` is not a valid email classification category
- `offset` is negative
- Invalid date format for `due_date`

**Resolution:**
1. Check parameter constraints in API documentation
2. Verify enum values against allowed list
3. Ensure numeric parameters are within valid ranges
4. Use ISO 8601 format for dates (e.g., "2025-11-08T17:00:00Z")

**Example Response:**
```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid category value",
    "details": "Category must be one of: fyi, action_required, newsletter, calendar_event, auto_response, receipts_confirmations, other"
  }
}
```

#### EMPTY_BATCH
**Message:** "Empty {array_name} array"

**Cause:** Batch operation endpoint received empty array when at least one item is required.

**Examples:**
- `email_ids` array is empty in `/api/ai/classifications`
- `task_ids` array is empty in `/api/tasks/updates`

**Resolution:**
1. Ensure array contains at least one item
2. Check that array is not accidentally overwritten before the request

**Example Response:**
```json
{
  "error": {
    "code": "EMPTY_BATCH",
    "message": "Empty email_ids array",
    "details": "Batch classification requires at least one email ID"
  }
}
```

### Resource Not Found (404 Not Found)

#### EMAIL_NOT_FOUND
**Message:** "Email not found: {email_id}"

**Cause:** Requested email ID doesn't exist in Outlook or database.

**Common Scenarios:**
- Email was deleted from Outlook
- Email ID is malformed or incorrect
- Email exists in Outlook but not yet synced to database (when using category filter)

**Resolution:**
1. Verify the email ID is correct
2. Check if email still exists in Outlook
3. If using database queries, ensure email has been classified and synced
4. Use `/api/emails?folder=Inbox` to browse live Outlook data

**Example Response:**
```json
{
  "error": {
    "code": "EMAIL_NOT_FOUND",
    "message": "Email not found: AAMkADc4...",
    "details": "Email may have been deleted or ID is incorrect"
  }
}
```

#### TASK_NOT_FOUND
**Message:** "Task not found: {task_id}"

**Cause:** Requested task ID doesn't exist in database.

**Resolution:**
1. Verify task ID is correct
2. Check that task wasn't already deleted
3. Use `/api/tasks` to list available tasks

**Example Response:**
```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task not found: 123"
  }
}
```

#### FOLDER_NOT_FOUND
**Message:** "Outlook folder not found: {folder_name}"

**Cause:** Specified Outlook folder doesn't exist.

**Resolution:**
1. Use `/api/folders` to list available folders
2. Check spelling and capitalization (folder names are case-sensitive)
3. Verify folder exists in Outlook

**Example Response:**
```json
{
  "error": {
    "code": "FOLDER_NOT_FOUND",
    "message": "Outlook folder not found: Projects",
    "details": "Use /api/folders to see available folders"
  }
}
```

### AI Service Errors (500 Internal Server Error)

#### AI_SERVICE_ERROR
**Message:** "Failed to classify/summarize email"

**Cause:** Azure OpenAI service is unavailable or returned an error.

**Common Scenarios:**
- Azure OpenAI service quota exceeded
- Network connectivity issues
- Azure OpenAI API key invalid or expired
- Azure deployment not found

**Resolution:**
1. Check Azure OpenAI service status
2. Verify API key in user settings (`/api/settings`)
3. Ensure Azure OpenAI deployment name is correct
4. Check network connectivity
5. Review Azure OpenAI quota limits
6. Use `/api/ai/health` to check AI service status

**Example Response:**
```json
{
  "error": {
    "code": "AI_SERVICE_ERROR",
    "message": "Failed to classify email",
    "details": "Azure OpenAI service returned 503 - Service Unavailable"
  }
}
```

#### REQUEST_TIMEOUT
**Message:** "AI {operation} timed out after {seconds} seconds"

**Cause:** AI service took too long to respond (default timeout: 30 seconds).

**Common Scenarios:**
- Very long email content
- High AI service latency
- Azure OpenAI service overloaded

**Resolution:**
1. Retry the request (may succeed on subsequent attempts)
2. For very long emails, consider summarizing email content first
3. Check Azure OpenAI service performance metrics

**Example Response:**
```json
{
  "error": {
    "code": "REQUEST_TIMEOUT",
    "message": "AI classification timed out after 30 seconds",
    "details": "Try again or consider summarizing long email content"
  }
}
```

#### PROMPT_TEMPLATE_ERROR
**Message:** "Failed to load prompt template: {template_name}"

**Cause:** AI prompt template file is missing or invalid.

**Resolution:**
1. Ensure `prompts/` directory exists
2. Verify prompt template files are not corrupted
3. Check file permissions
4. Use `/api/ai/templates` to list available templates

**Example Response:**
```json
{
  "error": {
    "code": "PROMPT_TEMPLATE_ERROR",
    "message": "Failed to load prompt template: email_classifier_with_explanation",
    "details": "Template file may be missing or corrupted"
  }
}
```

### Outlook Integration Errors (500 Internal Server Error)

#### OUTLOOK_ERROR
**Message:** "Failed to retrieve emails from Outlook" or "Failed to update email in Outlook"

**Cause:** Windows COM interface to Outlook failed.

**Common Scenarios:**
- Outlook is not running
- Outlook COM interface unavailable
- Insufficient permissions to access Outlook data
- Outlook is in safe mode or offline

**Resolution:**
1. Ensure Outlook desktop app is running
2. Restart Outlook if it's unresponsive
3. Check Windows COM security settings
4. Verify user has permissions to access Outlook
5. Ensure Outlook is not in safe mode or offline mode

**Example Response:**
```json
{
  "error": {
    "code": "OUTLOOK_ERROR",
    "message": "Failed to retrieve emails from Outlook",
    "details": "Outlook is not running or COM interface unavailable"
  }
}
```

#### EMAIL_MOVE_FAILED
**Message:** "Failed to move email to folder: {folder_name}"

**Cause:** Could not move email to specified Outlook folder.

**Common Scenarios:**
- Target folder doesn't exist
- Email was already deleted
- Insufficient permissions for target folder

**Resolution:**
1. Verify target folder exists using `/api/folders`
2. Check that email still exists
3. Ensure user has write permissions for target folder

**Example Response:**
```json
{
  "error": {
    "code": "EMAIL_MOVE_FAILED",
    "message": "Failed to move email to folder: Archive",
    "details": "Folder may not exist or insufficient permissions"
  }
}
```

#### CLASSIFICATION_APPLY_FAILED
**Message:** "Failed to apply classification to Outlook"

**Cause:** Could not update email category in Outlook.

**Common Scenarios:**
- Email doesn't exist in Outlook
- Outlook category not configured
- COM interface error

**Resolution:**
1. Verify email exists in Outlook
2. Ensure Outlook categories are properly configured
3. Check Outlook COM interface is available

**Example Response:**
```json
{
  "error": {
    "code": "CLASSIFICATION_APPLY_FAILED",
    "message": "Failed to apply classification to Outlook",
    "details": "Email may have been deleted or Outlook COM interface unavailable"
  }
}
```

### Database Errors (500 Internal Server Error)

#### DATABASE_ERROR
**Message:** "Failed to query/insert/update database"

**Cause:** SQLite database operation failed.

**Common Scenarios:**
- Database file is locked (another process accessing it)
- Disk full
- Database file corrupted
- Insufficient permissions to write to database file

**Resolution:**
1. Check if database file is locked by another process
2. Verify sufficient disk space
3. Restart the API server
4. Check file permissions on database file
5. If database is corrupted, restore from backup or reinitialize

**Example Response:**
```json
{
  "error": {
    "code": "DATABASE_ERROR",
    "message": "Failed to query database",
    "details": "SQLite error: database is locked"
  }
}
```

#### DATABASE_UNAVAILABLE
**Message:** "Failed to connect to database"

**Cause:** Cannot establish database connection.

**Common Scenarios:**
- Database file doesn't exist
- Database initialization failed
- File system errors

**Resolution:**
1. Check that database file exists in expected location
2. Verify file permissions
3. Restart API server to reinitialize database
4. Check disk space and file system health

**Example Response:**
```json
{
  "error": {
    "code": "DATABASE_UNAVAILABLE",
    "message": "Failed to connect to database",
    "details": "Database file may not exist or initialization failed"
  }
}
```

## Error Handling Best Practices

### For API Clients

1. **Always check HTTP status code first** - Use it to determine broad error category
2. **Parse error.code for specific handling** - Use application error codes for detailed error handling
3. **Display error.message to users** - It's human-readable and localized
4. **Log error.details for debugging** - Contains technical context useful for troubleshooting
5. **Implement retries for 500/503 errors** - Temporary failures often succeed on retry
6. **Don't retry 400/404 errors** - These indicate client-side issues that won't be fixed by retrying

### Retry Strategy

```javascript
async function retryWithBackoff(apiCall, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await apiCall();
    } catch (error) {
      // Only retry on 500/503 errors
      if (error.status === 500 || error.status === 503) {
        if (i < maxRetries - 1) {
          // Exponential backoff: 1s, 2s, 4s
          await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
          continue;
        }
      }
      // Don't retry 400/404 or if max retries exceeded
      throw error;
    }
  }
}
```

### Example Error Handling

```javascript
try {
  const response = await fetch('http://localhost:8000/api/ai/classification', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ subject, sender, content, context: '' })
  });
  
  if (!response.ok) {
    const error = await response.json();
    
    switch (error.error.code) {
      case 'VALIDATION_ERROR':
        // Show field-specific validation errors to user
        showFieldError(error.error.message);
        break;
        
      case 'AI_SERVICE_ERROR':
        // Retry or show AI service unavailable message
        if (await confirmRetry()) {
          return retryClassification();
        }
        break;
        
      case 'REQUEST_TIMEOUT':
        // Offer to retry or simplify email content
        showTimeoutDialog();
        break;
        
      default:
        // Generic error handling
        showError(error.error.message);
    }
  }
  
  const result = await response.json();
  return result;
  
} catch (networkError) {
  // Handle network/connection errors separately
  showError('Network error: Please check your connection');
}
```

## Common Error Scenarios

### Scenario: User tries to classify email without Azure OpenAI configured

**Request:**
```bash
curl -X POST "http://localhost:8000/api/ai/classification" \
  -H "Content-Type: application/json" \
  -d '{"subject":"Test","sender":"test@test.com","content":"Test email"}'
```

**Response:** 500 Internal Server Error
```json
{
  "error": {
    "code": "AI_SERVICE_ERROR",
    "message": "Failed to classify email",
    "details": "Azure OpenAI endpoint not configured in settings"
  }
}
```

**Resolution:** Configure Azure OpenAI settings via `/api/settings` or in user settings UI.

### Scenario: Batch operation with some failures

**Request:**
```bash
curl -X POST "http://localhost:8000/api/ai/classifications" \
  -H "Content-Type: application/json" \
  -d '{"email_ids":["valid-id","invalid-id","another-valid-id"]}'
```

**Response:** 200 OK (with partial failures)
```json
{
  "total": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "email_id": "valid-id",
      "success": true,
      "classification": { "category": "fyi", "confidence": 0.95 }
    },
    {
      "email_id": "invalid-id",
      "success": false,
      "error": "EMAIL_NOT_FOUND: Email not found: invalid-id"
    },
    {
      "email_id": "another-valid-id",
      "success": true,
      "classification": { "category": "action_required", "confidence": 0.88 }
    }
  ]
}
```

**Note:** Batch operations return 200 OK even with partial failures. Check the `failed` count and individual `success` flags in results.

### Scenario: Pagination beyond available data

**Request:**
```bash
curl -X GET "http://localhost:8000/api/emails?limit=50&offset=200"
```

**Response:** 200 OK (with empty results)
```json
{
  "emails": [],
  "total": 127,
  "offset": 200,
  "limit": 50,
  "has_more": false
}
```

**Note:** Returns empty array when offset exceeds available data, not an error. Use `has_more` flag to detect end of data.

## Health Check Endpoint

Use `/health` to verify service availability before making other API calls:

```bash
curl -X GET "http://localhost:8000/health"
```

**Healthy Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "email-helper-api",
  "version": "1.0.0",
  "database": "healthy"
}
```

**Unhealthy Response (503 Service Unavailable):**
```json
{
  "error": {
    "code": "DATABASE_UNAVAILABLE",
    "message": "Failed to connect to database",
    "details": "Connection refused"
  }
}
```

## AI Service Health Check

Use `/api/ai/health` to specifically check AI service availability:

```bash
curl -X GET "http://localhost:8000/api/ai/health"
```

**Available (200 OK):** No content or `{"status": "healthy"}`

**Unavailable (503 Service Unavailable):**
```json
{
  "error": {
    "code": "AI_SERVICE_ERROR",
    "message": "AI service unavailable",
    "details": "Azure OpenAI endpoint not configured or unreachable"
  }
}
```

## Troubleshooting Guide

### Problem: All API requests failing with connection refused

**Likely Cause:** API server is not running

**Resolution:**
1. Start the Go backend: `cd backend-go && ./build.ps1 -Run`
2. Or use the startup script: `./start-go-backend.ps1`
3. Verify server is listening on port 8000: `curl http://localhost:8000/health`

### Problem: Classification requests timing out

**Likely Cause:** Azure OpenAI service slow or overloaded

**Resolution:**
1. Check Azure OpenAI service status
2. Try smaller batch sizes
3. Increase timeout in client application
4. Consider caching frequent classifications

### Problem: Outlook integration errors

**Likely Cause:** Outlook COM interface unavailable

**Resolution:**
1. Ensure Outlook desktop is running
2. Restart Outlook if unresponsive
3. Run API server with administrator privileges if needed
4. Check Windows COM security settings

### Problem: Database locked errors

**Likely Cause:** Multiple processes accessing SQLite database

**Resolution:**
1. Ensure only one API server instance is running
2. Close any tools that may have database open (e.g., DB Browser)
3. Restart API server
4. Consider using SQLite Write-Ahead Logging (WAL) mode for better concurrency
