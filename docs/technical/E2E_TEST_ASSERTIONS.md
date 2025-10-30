# E2E Test Assertion Guidelines

## Overview

This document provides guidelines for writing robust E2E tests that validate actual functionality beyond just UI presence. All test utilities are available in `frontend/tests/e2e/fixtures/test-helpers.ts`.

## Core Principles

1. **Test Behavior, Not Just Presence**: Validate that features work correctly, not just that elements appear
2. **Validate Data Accuracy**: Verify counts, values, and state match expected data
3. **Verify API Interactions**: Check that correct payloads are sent and responses are handled
4. **Test State Persistence**: Ensure data persists across page reloads when appropriate
5. **Validate Error Handling**: Verify error messages are helpful and accurate
6. **Check Accessibility**: Ensure components meet accessibility standards

## Available Assertion Utilities

### Data Validation

#### `assertEmailData(page, emailData)`
Validates email data accuracy in the UI.

```typescript
await assertEmailData(page, {
  count: 5,                              // Exact email count
  subject: 'Project Update Required',    // Email subject
  sender: 'manager@company.com',         // Sender email
  body: /update.*status/i,               // Body text (string or regex)
  category: 'required_personal_action'   // Email category
});
```

#### `assertTaskData(page, taskData)`
Validates task data accuracy in the UI.

```typescript
await assertTaskData(page, {
  count: 3,                              // Exact task count
  title: 'Complete documentation',       // Task title
  description: /write.*docs/i,           // Description (string or regex)
  status: 'in_progress',                 // Task status
  priority: 'high'                       // Task priority
});
```

### API Validation

#### `assertAPIPayload(page, urlPattern, expectedPayload, options)`
Validates that API requests contain correct payloads.

```typescript
// Validate task creation payload
await Promise.all([
  assertAPIPayload(
    page,
    '/api/tasks',
    {
      title: 'Test Task',
      description: 'Task description',
      priority: 'high',
      status: 'pending'
    },
    { method: 'POST', partial: true }  // partial: true allows extra fields
  ),
  clickElement(submitButton)
]);
```

#### `assertAPIResponseStructure(page, urlPattern, expectedStructure, options)`
Validates API response structure.

```typescript
const responseData = await assertAPIResponseStructure(
  page,
  '/api/emails',
  {
    requiredFields: ['emails', 'total', 'page'],
    optionalFields: ['limit', 'filters'],
    statusCode: 200
  }
);

// Further validate response data
expect(responseData.emails).toBeInstanceOf(Array);
expect(responseData.total).toBeGreaterThan(0);
```

### State Persistence

#### `assertStatePersistence(page, stateChecks)`
Validates state persistence across page reloads.

```typescript
// Apply filters
await filterDropdown.selectOption('required_personal_action');

// Verify localStorage persistence
await assertStatePersistence(page, {
  localStorage: {
    'email-filters': {
      category: 'required_personal_action'
    }
  }
});

// Reload and verify persistence
await page.reload();
await assertStatePersistence(page, {
  localStorage: {
    'email-filters': {
      category: 'required_personal_action'
    }
  }
});
```

#### `assertLocalStorage(page, key, expectedValue)`
Validates localStorage contains expected data.

```typescript
await assertLocalStorage(page, 'user-preferences', {
  theme: 'dark',
  emailsPerPage: 50
});
```

#### `assertSessionStorage(page, key, expectedValue)`
Validates sessionStorage contains expected data.

```typescript
await assertSessionStorage(page, 'current-session', {
  userId: 'user-123',
  sessionStart: expect.any(String)
});
```

### Error Validation

#### `assertErrorMessage(page, expectedError, options)`
Validates error message content and type.

```typescript
await assertErrorMessage(
  page,
  {
    message: /AI service.*unavailable/i,
    type: 'error',
    contains: ['service', 'unavailable', 'try again']
  },
  { timeout: 5000 }
);
```

#### `assertNotification(page, message, options)`
Validates toast/notification messages.

```typescript
await assertNotification(page, /saved successfully|changes saved/i);
```

### Accessibility

#### `assertAccessibility(locator, checks)`
Validates accessibility attributes.

```typescript
const submitButton = await page.locator('button[type="submit"]');

await assertAccessibility(submitButton, {
  role: 'button',
  ariaLabel: /submit|save/i,
  tabIndex: 0
});
```

### Form Validation

#### `assertFormValidation(page, formSelector, validationTests)`
Validates form validation behavior.

```typescript
await assertFormValidation(
  page,
  'form[data-testid="task-form"]',
  [
    {
      field: 'title',
      invalidValue: '',
      expectedError: /title.*required/i
    },
    {
      field: 'title',
      invalidValue: 'ab',
      expectedError: /at least.*3.*characters/i
    },
    {
      field: 'email',
      invalidValue: 'not-an-email',
      expectedError: /valid email/i
    }
  ]
);
```

## Test Patterns

### Pattern 1: Complete User Flow with Data Validation

```typescript
test('should create task from email with accurate data', async ({ 
  page, 
  mockEmailAPI, 
  mockTaskAPI 
}) => {
  const testEmail = {
    id: 'email-123',
    subject: 'Review Required',
    sender: 'boss@company.com',
    body: 'Please review this document'
  };

  await mockEmailAPI(page, [testEmail]);
  await page.goto('/emails');
  
  // Select email and verify data
  await assertEmailData(page, {
    subject: 'Review Required',
    sender: 'boss@company.com'
  });
  
  // Open task creation
  await clickElement(await waitForTestId(page, 'create-task-button'));
  
  // Fill form
  const titleInput = await waitForTestId(page, 'task-title-input');
  await fillField(titleInput, 'Review document');
  
  // Validate API payload
  await Promise.all([
    assertAPIPayload(
      page,
      '/api/tasks',
      {
        title: 'Review document',
        source_email_id: 'email-123'
      },
      { partial: true }
    ),
    clickElement(await waitForTestId(page, 'submit-button'))
  ]);
  
  // Verify success notification
  await assertNotification(page, /task created/i);
  
  // Verify task appears with correct data
  await page.goto('/tasks');
  await assertTaskData(page, {
    title: 'Review document',
    status: 'pending'
  });
});
```

### Pattern 2: Error Handling with Retry

```typescript
test('should handle API failure and retry successfully', async ({ page }) => {
  let attemptCount = 0;
  
  await page.route('**/api/emails*', async (route) => {
    attemptCount++;
    
    if (attemptCount === 1) {
      // First attempt fails
      await route.fulfill({
        status: 503,
        body: JSON.stringify({ error: 'Service unavailable' })
      });
    } else {
      // Second attempt succeeds
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ emails: [], total: 0 })
      });
    }
  });
  
  await page.goto('/emails');
  
  // Verify error message
  await assertErrorMessage(page, {
    message: /service unavailable/i,
    type: 'error'
  });
  
  // Click retry
  const retryButton = await waitForElement(page, 'button:has-text("Retry")');
  await clickElement(retryButton);
  
  // Verify success after retry
  await waitForLoadingComplete(page);
  expect(attemptCount).toBe(2);
});
```

### Pattern 3: State Persistence Validation

```typescript
test('should persist filters across page reload', async ({ 
  page, 
  mockEmailAPI 
}) => {
  await mockEmailAPI(page, []);
  await page.goto('/emails');
  
  // Apply filter
  const categoryFilter = await waitForElement(page, 'select[name="category"]');
  await selectOption(categoryFilter, 'required_personal_action');
  
  // Verify localStorage
  await assertStatePersistence(page, {
    localStorage: {
      'email-filters': {
        category: 'required_personal_action'
      }
    }
  });
  
  // Reload page
  await page.reload();
  await waitForLoadingComplete(page);
  
  // Verify filter persisted
  await assertStatePersistence(page, {
    localStorage: {
      'email-filters': {
        category: 'required_personal_action'
      }
    }
  });
  
  // Verify UI reflects persisted state
  const selectedValue = await categoryFilter.inputValue();
  expect(selectedValue).toBe('required_personal_action');
});
```

## Migration Guide: Upgrading Existing Tests

### Before: Presence-Only Testing
```typescript
test('should display emails', async ({ page }) => {
  await page.goto('/emails');
  await expect(page.locator('.email-item')).toBeVisible();
});
```

### After: Behavior and Data Validation
```typescript
test('should display emails with accurate data', async ({ 
  page, 
  mockEmailAPI,
  mockEmails 
}) => {
  await mockEmailAPI(page, mockEmails);
  await page.goto('/emails');
  
  // Validate API response structure
  const responseData = await assertAPIResponseStructure(
    page,
    '/api/emails',
    {
      requiredFields: ['emails', 'total'],
      statusCode: 200
    }
  );
  
  // Validate data accuracy
  await assertEmailData(page, { 
    count: responseData.emails.length 
  });
  
  // Validate specific email data
  if (mockEmails.length > 0) {
    await assertEmailData(page, {
      subject: mockEmails[0].subject,
      sender: mockEmails[0].sender
    });
  }
});
```

## Common Validation Scenarios

### Scenario 1: List Display
- ✅ Validate exact count matches API response
- ✅ Verify data accuracy for at least first item
- ✅ Check API response structure
- ❌ Don't just check visibility

### Scenario 2: Form Submission
- ✅ Validate API payload contains correct data
- ✅ Verify success notification appears
- ✅ Check data appears in list after creation
- ✅ Validate form validation errors
- ❌ Don't just check form closes

### Scenario 3: Error Handling
- ✅ Validate error message content
- ✅ Verify error type (error/warning/info)
- ✅ Check error contains helpful keywords
- ✅ Test retry/recovery flow
- ❌ Don't just check error appears

### Scenario 4: State Management
- ✅ Verify localStorage/sessionStorage persistence
- ✅ Test state survives page reload
- ✅ Validate URL parameters reflect state
- ❌ Don't skip persistence testing

## Best Practices

1. **Always validate API interactions**: Use `assertAPIPayload` and `assertAPIResponseStructure` for API tests
2. **Test with real data**: Use mock data that resembles production data
3. **Validate error states**: Every happy path should have a corresponding error test
4. **Check accessibility**: Use `assertAccessibility` for interactive elements
5. **Test state persistence**: Verify important state survives page reloads
6. **Use specific assertions**: Prefer `assertEmailData` over generic locator checks
7. **Validate notifications**: Check that users get feedback for their actions
8. **Test form validation**: Verify validation rules work correctly

## Running Tests with Enhanced Assertions

```bash
# Run all E2E tests
npm run test:e2e

# Run specific test file
npx playwright test frontend/tests/e2e/email-processing.spec.ts

# Run with UI mode for debugging
npx playwright test --ui

# Run and see detailed assertion output
npx playwright test --reporter=line
```

## Examples to Reference

- `frontend/tests/e2e/enhanced-assertions-example.spec.ts` - Comprehensive examples of all assertion types
- `frontend/tests/e2e/task-management.spec.ts` - Enhanced task management tests
- `frontend/tests/e2e/email-processing.spec.ts` - Enhanced email processing tests
- `frontend/tests/e2e/fixtures/test-helpers.ts` - All available utilities

## Troubleshooting

### Problem: Assertion timeout
**Solution**: Increase timeout in options parameter
```typescript
await assertEmailData(page, { count: 5 }, { timeout: 10000 });
```

### Problem: API payload not captured
**Solution**: Ensure assertion happens before/during action
```typescript
await Promise.all([
  assertAPIPayload(page, '/api/tasks', expectedPayload),
  clickElement(submitButton)  // Action that triggers API call
]);
```

### Problem: localStorage not persisted
**Solution**: Check if app actually saves to localStorage
```typescript
// Debug what's actually in localStorage
const stored = await page.evaluate(() => 
  Object.entries(localStorage).reduce((acc, [k, v]) => {
    acc[k] = v;
    return acc;
  }, {})
);
console.log('localStorage contents:', stored);
```

## Future Enhancements

- Add visual regression testing utilities
- Add performance assertion helpers
- Add network timing validation
- Add database state validation for backend tests
- Add real browser accessibility scanning integration
