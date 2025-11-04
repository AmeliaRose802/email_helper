/**
 * Example E2E Tests Demonstrating Enhanced Assertions
 *
 * This file demonstrates how to use the enhanced assertion utilities
 * to validate actual functionality beyond just UI presence.
 *
 * Tests validate:
 * - Data accuracy (email counts, task statuses, field values)
 * - API payload correctness
 * - State persistence (localStorage, sessionStorage, URL params)
 * - Error message content
 * - Response structure validation
 * - Accessibility compliance
 * - Form validation behavior
 */

import { test, expect } from './fixtures/test-setup';
import {
  assertAPIPayload,
  assertEmailData,
  assertTaskData,
  assertErrorMessage,
  assertAPIResponseStructure,
  assertStatePersistence,
  assertAccessibility,
  assertFormValidation,
  waitForElement,
  clickElement,
} from './fixtures/test-helpers';

test.describe('Enhanced Assertions: Email Data Validation', () => {
  test('should validate email count and content accuracy', async ({
    page,
    mockEmailAPI,
    navigateToEmails
  }) => {
    const testEmails = [
      {
        id: '1',
        subject: 'Project Update Required',
        sender: 'manager@company.com',
        body: 'Please update the project status by EOD',
        category: 'required_personal_action',
        received: new Date().toISOString()
      },
      {
        id: '2',
        subject: 'Team Meeting Notes',
        sender: 'team@company.com',
        body: 'Here are the notes from today meeting',
        category: 'optional_fyi',
        received: new Date().toISOString()
      }
    ];

    await mockEmailAPI(page, testEmails);
    await navigateToEmails(page);

    // Validate exact email count
    await assertEmailData(page, { count: 2 });

    // Validate specific email data is displayed correctly
    await assertEmailData(page, {
      subject: 'Project Update Required',
      sender: 'manager@company.com',
      category: 'required_personal_action'
    });

    // Validate second email
    await assertEmailData(page, {
      subject: 'Team Meeting Notes',
      sender: 'team@company.com',
      category: 'optional_fyi'
    });
  });

  test('should validate API response structure', async ({
    page,
    mockEmailAPI,
    navigateToEmails
  }) => {
    await mockEmailAPI(page, []);
    await navigateToEmails(page);

    // Validate API response has required fields
    const responseData = await assertAPIResponseStructure(
      page,
      '/api/emails',
      {
        requiredFields: ['emails', 'total'],
        optionalFields: ['page', 'limit'],
        statusCode: 200
      }
    );

    // Further validate response data
    expect(responseData.emails).toBeInstanceOf(Array);
    expect(typeof responseData.total).toBe('number');
  });
});

test.describe('Enhanced Assertions: API Payload Validation', () => {
  test('should validate classification API receives correct payload', async ({
    page,
    mockEmailAPI,
    mockAIAPI,
    navigateToEmails
  }) => {
    const testEmail = {
      id: 'email-123',
      subject: 'Important: Review Required',
      sender: 'boss@company.com',
      body: 'Please review this document ASAP',
      received: new Date().toISOString()
    };

    await mockEmailAPI(page, [testEmail]);
    await mockAIAPI(page);
    await navigateToEmails(page);

    const firstEmail = await waitForElement(page, '[data-testid="email-item"]');
    await clickElement(firstEmail);

    const classifyButton = await waitForElement(
      page,
      'button:has-text("Classify"), button:has-text("Process")'
    );
    
    // Click classify and validate payload
    await Promise.all([
      assertAPIPayload(
        page,
        '/api/ai/classify',
        {
          email_id: 'email-123',
          subject: 'Important: Review Required',
          sender: 'boss@company.com'
        },
        { partial: true }
      ),
      clickElement(classifyButton)
    ]);
  });

  test('should validate task creation payload', async ({
    page,
    mockTaskAPI
  }) => {
    await mockTaskAPI(page, []);
    await page.goto('/#tasks');
    await page.waitForLoadState('networkidle');

    const createButton = await waitForElement(page, 'button:has-text("Create"), button:has-text("New Task")');
    await clickElement(createButton);

    // Fill task form
    const titleInput = await waitForElement(page, 'input[name="title"], [data-testid="task-title-input"]');
    await titleInput.fill('Test Task Title');

    const descInput = await waitForElement(page, 'textarea[name="description"], [data-testid="task-description-input"]');
    await descInput.fill('Test task description with details');

    const prioritySelect = await waitForElement(page, 'select[name="priority"], [data-testid="task-priority-select"]');
    await prioritySelect.selectOption('high');

    const submitButton = await waitForElement(page, 'button[type="submit"], [data-testid="task-submit-button"]');

    // Validate payload before submission
    await Promise.all([
      assertAPIPayload(
        page,
        '/api/tasks',
        {
          title: 'Test Task Title',
          description: 'Test task description with details',
          priority: 'high',
          status: 'pending'
        },
        { partial: true }
      ),
      clickElement(submitButton)
    ]);
  });
});

test.describe('Enhanced Assertions: State Persistence', () => {
  test('should persist email filters in localStorage', async ({
    page,
    mockEmailAPI
  }) => {
    await mockEmailAPI(page, []);
    await page.goto('/#emails');

    // Apply filter
    const filterButton = await waitForElement(page, 'button:has-text("Filter"), select[name="category"]');
    await filterButton.selectOption('required_personal_action');
    await page.waitForTimeout(500);

    // Validate state is persisted
    await assertStatePersistence(page, {
      localStorage: {
        'email-filters': {
          category: 'required_personal_action'
        }
      }
    });

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify filter persists
    await assertStatePersistence(page, {
      localStorage: {
        'email-filters': {
          category: 'required_personal_action'
        }
      }
    });
  });

  test('should persist pagination in URL params', async ({
    page,
    mockEmailAPI
  }) => {
    await mockEmailAPI(page, []);
    await page.goto('/#emails?page=2&limit=50');
    await page.waitForLoadState('networkidle');

    // Validate URL parameters
    await assertStatePersistence(page, {
      urlParams: {
        'page': '2',
        'limit': '50'
      }
    });
  });
});

test.describe('Enhanced Assertions: Error Handling', () => {
  test('should validate error message content for failed classification', async ({
    page,
    mockEmailAPI,
    navigateToEmails
  }) => {
    await mockEmailAPI(page, [{
      id: '1',
      subject: 'Test',
      sender: 'test@example.com',
      body: 'Test body',
      received: new Date().toISOString()
    }]);

    // Mock classification failure
    await page.route('**/api/ai/classify*', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'AI service temporarily unavailable. Please try again later.'
        })
      });
    });

    await navigateToEmails(page);
    const firstEmail = await waitForElement(page, '[data-testid="email-item"]');
    await clickElement(firstEmail);

    const classifyButton = await waitForElement(page, 'button:has-text("Classify")');
    await clickElement(classifyButton);

    // Validate error message content
    await assertErrorMessage(
      page,
      {
        message: /AI service.*unavailable/i,
        type: 'error',
        contains: ['service', 'unavailable']
      }
    );
  });

  test('should validate validation errors on task form', async ({
    page,
    mockTaskAPI
  }) => {
    await mockTaskAPI(page, []);
    await page.goto('/#tasks');

    const createButton = await waitForElement(page, 'button:has-text("Create")');
    await clickElement(createButton);

    // Test form validation
    await assertFormValidation(
      page,
      'form, [data-testid="task-form"]',
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
        }
      ]
    );
  });
});

test.describe('Enhanced Assertions: Task Data Validation', () => {
  test('should validate task list displays accurate data', async ({
    page,
    mockTaskAPI
  }) => {
    const testTasks = [
      {
        id: 'task-1',
        title: 'Complete project documentation',
        description: 'Write comprehensive docs',
        status: 'in_progress',
        priority: 'high',
        created: new Date().toISOString()
      },
      {
        id: 'task-2',
        title: 'Review pull requests',
        description: 'Review team PRs',
        status: 'pending',
        priority: 'medium',
        created: new Date().toISOString()
      }
    ];

    await mockTaskAPI(page, testTasks);
    await page.goto('/#tasks');
    await page.waitForLoadState('networkidle');

    // Validate task count
    await assertTaskData(page, { count: 2 });

    // Validate first task data
    await assertTaskData(page, {
      title: 'Complete project documentation',
      status: 'in_progress',
      priority: 'high'
    });

    // Validate second task data
    await assertTaskData(page, {
      title: 'Review pull requests',
      status: 'pending',
      priority: 'medium'
    });
  });
});

test.describe('Enhanced Assertions: Accessibility Validation', () => {
  test('should validate button accessibility attributes', async ({
    page,
    mockEmailAPI
  }) => {
    await mockEmailAPI(page, []);
    await page.goto('/#emails');

    const classifyButton = await waitForElement(
      page,
      'button:has-text("Classify"), button:has-text("Process")'
    );

    // Validate accessibility attributes
    await assertAccessibility(classifyButton, {
      role: 'button',
      ariaLabel: /classify|process/i,
      tabIndex: 0
    });
  });

  test('should validate form input accessibility', async ({
    page,
    mockTaskAPI
  }) => {
    await mockTaskAPI(page, []);
    await page.goto('/#tasks');

    const createButton = await waitForElement(page, 'button:has-text("Create")');
    await clickElement(createButton);

    const titleInput = await waitForElement(page, 'input[name="title"]');

    // Validate input accessibility
    await assertAccessibility(titleInput, {
      ariaLabel: /title|task name/i,
      ariaDescribedBy: true
    });
  });

  test('should validate image alt text', async ({
    page
  }) => {
    await page.goto('/#');
    
    const logo = page.locator('img[src*="logo"], .logo img').first();
    if (await logo.count() > 0) {
      await assertAccessibility(logo, {
        hasAltText: true
      });
    }
  });
});
