# Comprehensive E2E Tests - Critical User Flows

## Overview

This test suite covers the top 5 critical user journeys for the Email Helper application, with both happy path and error scenarios for each flow.

## Test Coverage

### 1. Email Retrieval and Classification Flow
**Happy Path:**
- User navigates to emails page
- System retrieves and displays emails from backend
- User selects an email
- User triggers AI classification
- System displays classification results with category and confidence

**Error Scenarios:**
- AI classification service unavailable (500 error)
- Empty email list handling
- Network timeouts during email fetch

**API Endpoints Tested:**
- `GET /api/emails` - List emails with pagination
- `POST /api/ai/classify` - Classify single email
- `GET /api/emails/:id` - Get email details

### 2. Task Creation and Management Flow
**Happy Path:**
- User selects an email
- User creates a task from the email
- Task is saved with title and description
- User navigates to tasks page
- User updates task status to "in_progress"
- User marks task as "completed"

**Error Scenarios:**
- Task creation failure (400 bad request)
- Invalid task data
- Network errors during task save

**API Endpoints Tested:**
- `POST /api/tasks` - Create new task
- `GET /api/tasks` - List all tasks
- `PATCH /api/tasks/:id` - Update task status
- `DELETE /api/tasks/:id` - Delete task

### 3. Bulk Processing and Category Review Flow
**Happy Path:**
- User selects multiple emails (select all checkbox)
- User triggers bulk classification
- System processes all selected emails
- User reviews assigned categories
- User edits a classification manually

**Error Scenarios:**
- Partial batch processing failures
- Some emails succeed, some fail
- Proper error reporting for failed items

**API Endpoints Tested:**
- `POST /api/processing/process-batch` - Batch process emails
- `PATCH /api/emails/:id` - Update email category
- `GET /api/emails/stats` - Get email statistics by category

### 4. Settings Configuration Flow
**Happy Path:**
- User navigates to settings page
- User updates username
- User saves settings
- System persists changes to database
- User reloads page to verify persistence
- User toggles auto-classify setting

**Error Scenarios:**
- Settings save failure (500 database error)
- Network errors during save
- Proper error message display

**API Endpoints Tested:**
- `GET /api/settings` - Load user settings
- `PUT /api/settings` - Update settings
- `PATCH /api/settings` - Partial settings update

### 5. Error Recovery and Retry Flow
**Happy Path:**
- System encounters network timeout on first attempt
- User clicks retry button (or automatic retry)
- Second attempt succeeds
- Data loads correctly

**Error Scenarios:**
- Network timeout with retry
- 500 server error with manual retry
- 404 not found error with graceful handling
- AI classification failure with retry
- Multiple consecutive failures

**API Endpoints Tested:**
- All endpoints with error simulations
- Retry logic for transient failures
- Proper error state management

## Test Utilities

### Fixtures (from `test-setup.ts`)
- `mockEmails` - Pre-generated mock email data
- `mockTasks` - Pre-generated mock task data
- `mockEmailAPI` - Email API route mocking
- `mockTaskAPI` - Task API route mocking
- `mockAIAPI` - AI classification API mocking
- `navigateToEmails` - Helper to navigate to emails page
- `navigateToTasks` - Helper to navigate to tasks page
- `navigateToProcessing` - Helper to navigate to processing page

### Mock Data Generators
- `generateMockEmails(count)` - Create test email data
- `generateMockTasks(count)` - Create test task data

## Running the Tests

### Run all critical flow tests:
```bash
npm run test:e2e -- critical-user-flows.spec.ts
```

### Run specific test suite:
```bash
npm run test:e2e -- critical-user-flows.spec.ts -g "Email Retrieval"
npm run test:e2e -- critical-user-flows.spec.ts -g "Task Creation"
npm run test:e2e -- critical-user-flows.spec.ts -g "Bulk Processing"
npm run test:e2e -- critical-user-flows.spec.ts -g "Settings"
npm run test:e2e -- critical-user-flows.spec.ts -g "Error Recovery"
```

### Run with UI mode for debugging:
```bash
npm run test:e2e:ui -- critical-user-flows.spec.ts
```

### Run in headed mode to see browser:
```bash
npm run test:e2e:headed -- critical-user-flows.spec.ts
```

### Debug specific test:
```bash
npm run test:e2e:debug -- critical-user-flows.spec.ts -g "should retrieve emails"
```

## Test Validation Strategy

### Data Accuracy Validation
- **Email counts**: Verify correct number of emails displayed
- **Task statuses**: Verify task status changes persist
- **Category assignments**: Verify classifications are correctly saved
- **Settings persistence**: Verify settings survive page reload

### API Call Verification
- **Request payloads**: Verify correct data sent to backend
- **Response handling**: Verify responses processed correctly
- **Status codes**: Verify appropriate status codes returned
- **Error responses**: Verify error responses handled gracefully

### State Persistence Validation
- **localStorage**: Verify user preferences saved locally
- **sessionStorage**: Verify temporary state preserved
- **Database persistence**: Verify data saved to backend
- **Page reload**: Verify state survives navigation

### Error Message Validation
- **Error visibility**: Error messages displayed to user
- **Error content**: Error messages are meaningful
- **Error clearing**: Errors clear after retry succeeds
- **Error actions**: Retry/dismiss buttons available

### Accessibility Compliance
- **Role attributes**: Proper ARIA roles used
- **Alert regions**: Errors use `role="alert"`
- **Keyboard navigation**: All actions keyboard accessible
- **Screen reader support**: Proper labels and descriptions

## Test Execution Time

Target execution time: **< 5 minutes**

Actual execution times (approximate):
- Email Retrieval flow: 30-45 seconds
- Task Management flow: 45-60 seconds
- Bulk Processing flow: 60-75 seconds
- Settings Configuration flow: 30-45 seconds
- Error Recovery flow: 60-90 seconds

Total: ~4-5 minutes with retries on failure

## Known Limitations

1. **Sequential Execution**: Tests run sequentially (workers: 1) due to COM backend limitations
2. **Mock Dependencies**: Tests use mocked APIs, not real backend integration
3. **Timing Sensitivity**: Some tests use `waitForTimeout` which can be flaky
4. **UI Selector Flexibility**: Tests use multiple selector strategies to handle UI variations

## Maintenance Notes

### When to Update Tests

1. **API Changes**: When backend API endpoints or payloads change
2. **UI Changes**: When frontend selectors or component structure changes
3. **New Features**: When adding new critical user flows
4. **Bug Fixes**: When fixing bugs that weren't caught by existing tests

### Best Practices

1. **Selector Strategy**: Use data-testid attributes first, then semantic selectors
2. **Wait Strategy**: Use `waitForResponse` for API calls, not arbitrary timeouts
3. **Error Handling**: Always test both happy path and error scenarios
4. **Isolation**: Each test should be independent and not rely on previous test state
5. **Clarity**: Test names should clearly describe the scenario being tested

## Integration with CI/CD

These tests are designed to be integrated into the CI/CD pipeline (see `email_helper-22`):
- Run on PR creation/update
- Execute against staging environment
- Generate test reports with screenshots
- Capture videos on failure
- Parallel execution where possible

## Success Criteria

✅ All 13 test cases passing (5 flows × 2-3 scenarios each)
✅ < 5 minute execution time
✅ Clear failure reporting with screenshots
✅ 70%+ coverage of critical user journeys
✅ No false positives/flaky tests
