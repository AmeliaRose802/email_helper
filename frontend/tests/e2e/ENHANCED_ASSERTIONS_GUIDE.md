# Enhanced E2E Test Assertions Guide

## Overview

This guide documents the enhanced assertion utilities available for E2E tests. These utilities go beyond simple visibility checks to validate actual functionality, data accuracy, API behavior, and user experience.

## Table of Contents

1. [Data Validation Assertions](#data-validation-assertions)
2. [API Validation Assertions](#api-validation-assertions)
3. [State Persistence Assertions](#state-persistence-assertions)
4. [Error Handling Assertions](#error-handling-assertions)
5. [Accessibility Assertions](#accessibility-assertions)
6. [Form Validation Assertions](#form-validation-assertions)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

## Data Validation Assertions

### `assertEmailData(page, emailData)`

Validates email data accuracy in the UI, ensuring actual content matches expectations.

**Parameters:**
- `page`: Playwright Page object
- `emailData`: Object with optional properties:
  - `subject?: string | RegExp` - Expected email subject
  - `sender?: string | RegExp` - Expected sender
  - `body?: string | RegExp` - Expected body content
  - `category?: string` - Expected category classification
  - `count?: number` - Expected number of emails displayed

**Example:**
```typescript
// Validate exact count
await assertEmailData(page, { count: 5 });

// Validate specific email content
await assertEmailData(page, {
  subject: 'Project Update',
  sender: 'manager@company.com',
  category: 'required_personal_action'
});

// Use regex for flexible matching
await assertEmailData(page, {
  subject: /project.*update/i,
  body: /deadline.*friday/i
});
```

**Why this matters:** Tests should verify that the correct data is displayed, not just that something is visible. This catches data transformation bugs, filtering issues, and rendering errors.

### `assertTaskData(page, taskData)`

Validates task data accuracy in the UI.

**Parameters:**
- `page`: Playwright Page object
- `taskData`: Object with optional properties:
  - `title?: string | RegExp` - Expected task title
  - `description?: string | RegExp` - Expected description
  - `status?: string` - Expected status (e.g., 'pending', 'in_progress', 'completed')
  - `priority?: string` - Expected priority (e.g., 'low', 'medium', 'high')
  - `count?: number` - Expected number of tasks displayed

**Example:**
```typescript
// Validate task count
await assertTaskData(page, { count: 3 });

// Validate specific task details
await assertTaskData(page, {
  title: 'Complete documentation',
  status: 'in_progress',
  priority: 'high'
});
```

## API Validation Assertions

### `assertAPIPayload(page, urlPattern, expectedPayload, options)`

Captures and validates that API requests contain the correct payload data.

**Parameters:**
- `page`: Playwright Page object
- `urlPattern`: string or RegExp to match API URL
- `expectedPayload`: Object with expected payload fields
- `options`: Optional configuration
  - `timeout?: number` - Wait timeout (default: 10000ms)
  - `method?: string` - HTTP method (default: 'POST')
  - `partial?: boolean` - If true, only checks specified fields (default: false)

**Example:**
```typescript
// Full payload validation
await assertAPIPayload(
  page,
  '/api/tasks',
  {
    title: 'New Task',
    description: 'Task description',
    priority: 'high',
    status: 'pending'
  }
);

// Partial payload validation (only check specific fields)
await assertAPIPayload(
  page,
  '/api/ai/classify',
  {
    email_id: 'email-123',
    subject: 'Important Email'
  },
  { partial: true }
);
```

**Why this matters:** Validates that the frontend sends correct data to backend APIs. Catches bugs in data transformation, serialization, and parameter passing.

### `assertAPIResponseStructure(page, urlPattern, expectedStructure, options)`

Validates that API responses have the required structure and fields.

**Parameters:**
- `page`: Playwright Page object
- `urlPattern`: string or RegExp to match API URL
- `expectedStructure`: Object with:
  - `requiredFields: string[]` - Fields that must exist
  - `optionalFields?: string[]` - Fields that may exist
  - `statusCode?: number` - Expected status code (default: 200)
- `options`: Optional `{ timeout?: number }`

**Returns:** The response data object

**Example:**
```typescript
const responseData = await assertAPIResponseStructure(
  page,
  '/api/emails',
  {
    requiredFields: ['emails', 'total', 'page'],
    optionalFields: ['nextCursor', 'hasMore'],
    statusCode: 200
  }
);

// Further validate response
expect(responseData.emails).toBeInstanceOf(Array);
expect(responseData.total).toBeGreaterThan(0);
```

**Why this matters:** Ensures API contracts are maintained. Detects breaking changes in API responses and missing required data.

### `assertAPICallSequence(page, expectedSequence, options)`

Validates that API calls happen in the expected order.

**Parameters:**
- `page`: Playwright Page object
- `expectedSequence`: Array of expected API calls with:
  - `urlPattern: string | RegExp` - URL pattern to match
  - `method: string` - HTTP method
  - `order: number` - Expected position in sequence
- `options`: Optional `{ timeout?: number }`

**Example:**
```typescript
await assertAPICallSequence(
  page,
  [
    { urlPattern: '/api/auth/validate', method: 'GET', order: 1 },
    { urlPattern: '/api/emails', method: 'GET', order: 2 },
    { urlPattern: '/api/tasks', method: 'GET', order: 3 }
  ]
);
```

**Why this matters:** Validates application flow and prevents race conditions. Ensures dependent API calls happen in the correct order.

## State Persistence Assertions

### `assertStatePersistence(page, stateChecks)`

Validates that application state persists correctly across page loads and navigation.

**Parameters:**
- `page`: Playwright Page object
- `stateChecks`: Object with:
  - `localStorage?: Record<string, any>` - Expected localStorage values
  - `sessionStorage?: Record<string, any>` - Expected sessionStorage values
  - `urlParams?: Record<string, string>` - Expected URL parameters

**Example:**
```typescript
// Check localStorage persistence
await assertStatePersistence(page, {
  localStorage: {
    'user-preferences': {
      theme: 'dark',
      emailsPerPage: 50
    },
    'email-filters': {
      category: 'required_personal_action'
    }
  }
});

// Check URL parameter persistence
await assertStatePersistence(page, {
  urlParams: {
    'page': '2',
    'sort': 'date-desc'
  }
});

// Check sessionStorage
await assertStatePersistence(page, {
  sessionStorage: {
    'active-tab': 'emails',
    'scroll-position': '500'
  }
});
```

**Why this matters:** Validates that user preferences, filters, and navigation state persist correctly. Ensures good UX and prevents data loss.

## Error Handling Assertions

### `assertErrorMessage(page, expectedError, options)`

Validates that error messages display the correct content and type.

**Parameters:**
- `page`: Playwright Page object
- `expectedError`: Object with:
  - `message: string | RegExp` - Expected error message pattern
  - `type?: 'error' | 'warning' | 'info'` - Error severity type
  - `contains?: string[]` - Keywords that must appear in error
- `options`: Optional `{ timeout?: number }`

**Example:**
```typescript
// Validate error message content
await assertErrorMessage(
  page,
  {
    message: /AI service.*unavailable/i,
    type: 'error',
    contains: ['service', 'unavailable', 'try again']
  }
);

// Validate warning message
await assertErrorMessage(
  page,
  {
    message: /no emails found/i,
    type: 'warning'
  }
);
```

**Why this matters:** Validates that users receive helpful, accurate error messages. Ensures error handling works correctly and provides good UX.

## Accessibility Assertions

### `assertAccessibility(locator, checks)`

Validates that UI elements have proper accessibility attributes.

**Parameters:**
- `locator`: Playwright Locator for the element
- `checks`: Object with:
  - `role?: string` - Expected ARIA role
  - `ariaLabel?: string | RegExp` - Expected aria-label
  - `ariaDescribedBy?: boolean` - Check if aria-describedby exists
  - `tabIndex?: number` - Expected tabindex value
  - `hasAltText?: boolean` - For images, check alt text exists

**Example:**
```typescript
// Validate button accessibility
const submitButton = page.locator('button[type="submit"]');
await assertAccessibility(submitButton, {
  role: 'button',
  ariaLabel: /submit|save/i,
  tabIndex: 0
});

// Validate form input accessibility
const emailInput = page.locator('input[name="email"]');
await assertAccessibility(emailInput, {
  ariaLabel: 'Email address',
  ariaDescribedBy: true
});

// Validate image has alt text
const logo = page.locator('img.logo');
await assertAccessibility(logo, {
  hasAltText: true
});
```

**Why this matters:** Ensures the application is accessible to users with disabilities. Validates WCAG compliance and semantic HTML usage.

## Form Validation Assertions

### `assertFormValidation(page, formSelector, validationTests)`

Validates that form fields show correct validation errors for invalid input.

**Parameters:**
- `page`: Playwright Page object
- `formSelector`: CSS selector for the form
- `validationTests`: Array of validation test cases:
  - `field: string` - Field name or ID
  - `invalidValue: string` - Invalid value to test
  - `expectedError: string | RegExp` - Expected error message

**Example:**
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
      expectedError: /at least 3 characters/i
    },
    {
      field: 'email',
      invalidValue: 'invalid-email',
      expectedError: /valid email address/i
    }
  ]
);
```

**Why this matters:** Validates that form validation works correctly and provides helpful feedback. Prevents invalid data submission.

## Best Practices

### 1. Always Validate Data Accuracy, Not Just Presence

❌ **Bad:** Only checking if something exists
```typescript
const emailCount = await page.locator('.email-item').count();
expect(emailCount).toBeGreaterThan(0);
```

✅ **Good:** Validating actual data
```typescript
await assertEmailData(page, {
  count: 5,
  subject: 'Expected Subject',
  sender: 'expected@example.com'
});
```

### 2. Validate API Payloads for Critical Operations

❌ **Bad:** Just triggering action without validation
```typescript
await page.click('button:has-text("Save")');
await page.waitForTimeout(1000);
```

✅ **Good:** Validating correct data is sent
```typescript
await Promise.all([
  assertAPIPayload(page, '/api/tasks', {
    title: 'My Task',
    priority: 'high'
  }),
  page.click('button:has-text("Save")')
]);
```

### 3. Check State Persistence for User Workflows

❌ **Bad:** Not testing persistence
```typescript
await page.selectOption('select[name="filter"]', 'important');
// Test ends without checking if filter persists
```

✅ **Good:** Validating state persists
```typescript
await page.selectOption('select[name="filter"]', 'important');
await assertStatePersistence(page, {
  localStorage: {
    'email-filters': { category: 'important' }
  }
});

await page.reload();
await assertStatePersistence(page, {
  localStorage: {
    'email-filters': { category: 'important' }
  }
});
```

### 4. Validate Error Message Content, Not Just Presence

❌ **Bad:** Only checking error exists
```typescript
const errorExists = await page.locator('.error').count() > 0;
expect(errorExists).toBe(true);
```

✅ **Good:** Validating error content
```typescript
await assertErrorMessage(page, {
  message: /failed to save.*network error/i,
  type: 'error',
  contains: ['network', 'retry']
});
```

### 5. Test API Response Structure

❌ **Bad:** Assuming response structure
```typescript
const response = await page.waitForResponse('/api/emails');
const data = await response.json();
// Use data without validation
```

✅ **Good:** Validating response structure
```typescript
const data = await assertAPIResponseStructure(
  page,
  '/api/emails',
  {
    requiredFields: ['emails', 'total', 'page'],
    statusCode: 200
  }
);

expect(data.emails).toBeInstanceOf(Array);
expect(data.total).toBeGreaterThanOrEqual(data.emails.length);
```

## Examples

### Example 1: Complete Email Classification Flow

```typescript
test('should classify email with full validation', async ({ page, mockEmailAPI, mockAIAPI }) => {
  const testEmail = {
    id: 'email-123',
    subject: 'Urgent: Action Required',
    sender: 'boss@company.com',
    body: 'Please review this immediately'
  };

  await mockEmailAPI(page, [testEmail]);
  await mockAIAPI(page);
  await page.goto('/emails');

  // 1. Validate email data displays correctly
  await assertEmailData(page, {
    count: 1,
    subject: 'Urgent: Action Required',
    sender: 'boss@company.com'
  });

  // 2. Click classify and validate API payload
  const classifyButton = await waitForElement(page, 'button:has-text("Classify")');
  await Promise.all([
    assertAPIPayload(page, '/api/ai/classify', {
      email_id: 'email-123',
      subject: 'Urgent: Action Required'
    }, { partial: true }),
    clickElement(classifyButton)
  ]);

  // 3. Validate response structure
  const classificationData = await assertAPIResponseStructure(
    page,
    '/api/ai/classify',
    {
      requiredFields: ['category', 'confidence', 'action_items'],
      statusCode: 200
    }
  );

  // 4. Validate classification result displays
  await assertEmailData(page, {
    category: classificationData.category
  });

  // 5. Validate state persists
  await assertStatePersistence(page, {
    localStorage: {
      'classified-emails': expect.arrayContaining(['email-123'])
    }
  });
});
```

### Example 2: Task Creation with Validation

```typescript
test('should create task with full validation', async ({ page, mockTaskAPI }) => {
  await mockTaskAPI(page, []);
  await page.goto('/tasks');

  const createButton = await waitForElement(page, 'button:has-text("Create")');
  await clickElement(createButton);

  // 1. Test form validation
  await assertFormValidation(
    page,
    'form[data-testid="task-form"]',
    [
      {
        field: 'title',
        invalidValue: '',
        expectedError: /required/i
      },
      {
        field: 'title',
        invalidValue: 'ab',
        expectedError: /at least 3 characters/i
      }
    ]
  );

  // 2. Fill valid data
  await fillField(page.locator('input[name="title"]'), 'Complete project docs');
  await fillField(page.locator('textarea[name="description"]'), 'Write comprehensive documentation');
  await selectOption(page.locator('select[name="priority"]'), 'high');

  // 3. Validate API payload on submit
  const submitButton = await waitForElement(page, 'button[type="submit"]');
  await Promise.all([
    assertAPIPayload(page, '/api/tasks', {
      title: 'Complete project docs',
      description: 'Write comprehensive documentation',
      priority: 'high',
      status: 'pending'
    }),
    clickElement(submitButton)
  ]);

  // 4. Validate task appears in list
  await assertTaskData(page, {
    count: 1,
    title: 'Complete project docs',
    priority: 'high',
    status: 'pending'
  });
});
```

### Example 3: Error Handling with Recovery

```typescript
test('should handle API error with proper messaging', async ({ page, mockEmailAPI }) => {
  await mockEmailAPI(page, [{
    id: '1',
    subject: 'Test',
    sender: 'test@example.com',
    body: 'Test body'
  }]);

  // Mock API failure
  await page.route('**/api/ai/classify*', async (route) => {
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({
        error: 'AI service temporarily unavailable. Please try again in a few minutes.'
      })
    });
  });

  await page.goto('/emails');
  
  const firstEmail = await waitForElement(page, '[data-testid="email-item"]');
  await clickElement(firstEmail);

  const classifyButton = await waitForElement(page, 'button:has-text("Classify")');
  await clickElement(classifyButton);

  // Validate error message content
  await assertErrorMessage(page, {
    message: /AI service.*unavailable/i,
    type: 'error',
    contains: ['service', 'unavailable', 'try again']
  });

  // Verify retry button exists
  const retryButton = await waitForElement(page, 'button:has-text("Retry")');
  await expect(retryButton).toBeVisible();

  // Validate accessibility of error message
  const errorAlert = page.locator('[role="alert"]');
  await assertAccessibility(errorAlert, {
    role: 'alert',
    ariaLabel: /error|alert/i
  });
});
```

## Migration Guide

To update existing tests to use enhanced assertions:

1. **Replace simple count checks:**
   ```typescript
   // Before
   const count = await page.locator('.email-item').count();
   expect(count).toBe(5);
   
   // After
   await assertEmailData(page, { count: 5 });
   ```

2. **Add API payload validation:**
   ```typescript
   // Before
   await page.click('button:has-text("Save")');
   
   // After
   await Promise.all([
     assertAPIPayload(page, '/api/tasks', expectedPayload),
     page.click('button:has-text("Save")')
   ]);
   ```

3. **Enhance error checks:**
   ```typescript
   // Before
   const hasError = await page.locator('.error').isVisible();
   expect(hasError).toBe(true);
   
   // After
   await assertErrorMessage(page, {
     message: /expected error pattern/i,
     type: 'error',
     contains: ['keyword1', 'keyword2']
   });
   ```

4. **Add state persistence checks:**
   ```typescript
   // Before
   await page.selectOption('select', 'value');
   // No validation
   
   // After
   await page.selectOption('select', 'value');
   await assertStatePersistence(page, {
     localStorage: { 'key': 'value' }
   });
   ```

## Summary

These enhanced assertions help ensure:
- ✅ Tests validate actual functionality, not just UI presence
- ✅ API contracts are maintained between frontend and backend
- ✅ Data accuracy is verified at every step
- ✅ Error handling provides good user experience
- ✅ State persists correctly across user workflows
- ✅ Forms validate input appropriately
- ✅ Accessibility standards are met

Use these utilities to write more comprehensive, meaningful E2E tests that catch real bugs and ensure quality user experience.
