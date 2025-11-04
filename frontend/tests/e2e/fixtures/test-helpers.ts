/**
 * Test Helper Utilities
 * 
 * Provides reusable utilities for E2E tests including:
 * - Robust wait strategies
 * - Element existence assertions
 * - Data validation helpers
 */

import { Page, Locator, expect, Request } from '@playwright/test';

/**
 * Wait for an element with retry logic and clear error messages
 * Fails loudly if element is not found
 */
export async function waitForElement(
  page: Page,
  selector: string,
  options: {
    timeout?: number;
    state?: 'attached' | 'visible' | 'hidden';
    errorMessage?: string;
  } = {}
): Promise<Locator> {
  const { timeout = 10000, state = 'visible', errorMessage } = options;
  
  const locator = page.locator(selector);
  
  try {
    await locator.waitFor({ state, timeout });
    return locator;
  } catch (error) {
    const customMessage = errorMessage || `Element not found: ${selector}`;
    throw new Error(`${customMessage}\n\nPage URL: ${page.url()}\nOriginal error: ${error}`);
  }
}

/**
 * Wait for multiple elements to be visible
 * Returns all matching locators
 */
export async function waitForElements(
  page: Page,
  selector: string,
  options: {
    timeout?: number;
    minCount?: number;
  } = {}
): Promise<Locator[]> {
  const { timeout = 10000, minCount = 1 } = options;
  
  const locator = page.locator(selector);
  
  // Wait for first element to appear
  try {
    await locator.first().waitFor({ state: 'attached', timeout });
  } catch (error) {
    const actualCount = await locator.count();
    throw new Error(
      `Expected at least ${minCount} elements matching "${selector}", but found ${actualCount}.\n` +
      `Page URL: ${page.url()}`
    );
  }
  
  // Check we have at least minCount
  const actualCount = await locator.count();
  if (actualCount < minCount) {
    throw new Error(
      `Expected at least ${minCount} elements matching "${selector}", but found ${actualCount}.\n` +
      `Page URL: ${page.url()}`
    );
  }
  
  return locator.all();
}

/**
 * Wait for element with specific text content
 */
export async function waitForElementWithText(
  page: Page,
  selector: string,
  text: string | RegExp,
  options: { timeout?: number } = {}
): Promise<Locator> {
  const { timeout = 10000 } = options;
  
  const locator = page.locator(selector).filter({ hasText: text });
  
  await locator.waitFor({ state: 'visible', timeout }).catch(() => {
    throw new Error(
      `Element matching "${selector}" with text "${text}" not found.\n` +
      `Page URL: ${page.url()}`
    );
  });
  
  return locator;
}

/**
 * Wait for element by data-testid attribute
 */
export async function waitForTestId(
  page: Page,
  testId: string,
  options: { timeout?: number; state?: 'attached' | 'visible' | 'hidden' } = {}
): Promise<Locator> {
  const { timeout = 10000, state = 'visible' } = options;
  
  const locator = page.getByTestId(testId);
  
  try {
    await locator.first().waitFor({ state, timeout });
  } catch (error) {
    throw new Error(
      `Element with data-testid="${testId}" not found.\n` +
      `Page URL: ${page.url()}`
    );
  }
  
  return locator.first();
}

/**
 * Click element with retry logic for transient failures
 */
export async function clickElement(
  locator: Locator,
  options: {
    retries?: number;
    delay?: number;
  } = {}
): Promise<void> {
  const { retries = 3, delay = 500 } = options;
  
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      await locator.click({ timeout: 5000 });
      return;
    } catch (error) {
      if (attempt === retries) {
        throw new Error(`Failed to click element after ${retries} attempts: ${error}`);
      }
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

/**
 * Select option from dropdown with validation
 */
export async function selectOption(
  locator: Locator,
  value: string,
  options: { retries?: number } = {}
): Promise<void> {
  const { retries = 3 } = options;
  
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      await locator.selectOption(value, { timeout: 5000 });
      
      // Verify selection
      const selectedValue = await locator.inputValue();
      if (selectedValue === value) {
        return;
      }
      
      throw new Error(`Selected value "${selectedValue}" does not match expected "${value}"`);
    } catch (error) {
      if (attempt === retries) {
        throw new Error(`Failed to select option "${value}" after ${retries} attempts: ${error}`);
      }
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }
}

/**
 * Assert element exists and is visible
 */
export async function assertElementExists(
  page: Page,
  selector: string,
  errorMessage?: string
): Promise<void> {
  const locator = page.locator(selector);
  const count = await locator.count();
  
  if (count === 0) {
    const message = errorMessage || `Expected element "${selector}" to exist, but it was not found.`;
    throw new Error(`${message}\nPage URL: ${page.url()}`);
  }
  
  await expect(locator.first()).toBeVisible();
}

/**
 * Assert specific count of elements
 */
export async function assertElementCount(
  page: Page,
  selector: string,
  expectedCount: number,
  errorMessage?: string
): Promise<void> {
  const locator = page.locator(selector);
  const actualCount = await locator.count();
  
  if (actualCount !== expectedCount) {
    const message = errorMessage || 
      `Expected ${expectedCount} elements matching "${selector}", but found ${actualCount}.`;
    throw new Error(`${message}\nPage URL: ${page.url()}`);
  }
}

/**
 * Wait for API response with specific criteria
 */
export async function waitForAPIResponse(
  page: Page,
  urlPattern: string | RegExp,
  options: {
    timeout?: number;
    status?: number;
  } = {}
): Promise<unknown> {
  const { timeout = 10000, status = 200 } = options;
  
  const response = await page.waitForResponse(
    (resp) => {
      const url = resp.url();
      const matchesPattern = typeof urlPattern === 'string' 
        ? url.includes(urlPattern)
        : urlPattern.test(url);
      return matchesPattern && resp.status() === status;
    },
    { timeout }
  ).catch(() => {
    throw new Error(
      `API response matching "${urlPattern}" with status ${status} not received within ${timeout}ms.\n` +
      `Page URL: ${page.url()}`
    );
  });
  
  return response.json();
}

/**
 * Wait for element to have specific attribute value
 */
export async function waitForAttribute(
  locator: Locator,
  attribute: string,
  expectedValue: string | RegExp,
  options: { timeout?: number } = {}
): Promise<void> {
  const { timeout = 10000 } = options;
  
  await expect(locator).toHaveAttribute(attribute, expectedValue, { timeout });
}

/**
 * Check if element exists without failing
 * Returns true if element exists and is visible
 */
export async function elementExists(
  page: Page,
  selector: string,
  timeout: number = 2000
): Promise<boolean> {
  try {
    const locator = page.locator(selector);
    await locator.waitFor({ state: 'visible', timeout });
    return true;
  } catch {
    return false;
  }
}

/**
 * Verify localStorage contains expected data
 */
export async function assertLocalStorage(
  page: Page,
  key: string,
  expectedValue?: unknown
): Promise<void> {
  const value = await page.evaluate((k) => localStorage.getItem(k), key);
  
  if (value === null) {
    throw new Error(`localStorage key "${key}" not found`);
  }
  
  if (expectedValue !== undefined) {
    const parsedValue = JSON.parse(value);
    expect(parsedValue).toEqual(expectedValue);
  }
}

/**
 * Verify sessionStorage contains expected data
 */
export async function assertSessionStorage(
  page: Page,
  key: string,
  expectedValue?: unknown
): Promise<void> {
  const value = await page.evaluate((k) => sessionStorage.getItem(k), key);
  
  if (value === null) {
    throw new Error(`sessionStorage key "${key}" not found`);
  }
  
  if (expectedValue !== undefined) {
    const parsedValue = JSON.parse(value);
    expect(parsedValue).toEqual(expectedValue);
  }
}

/**
 * Wait for loading state to complete
 */
export async function waitForLoadingComplete(
  page: Page,
  options: {
    timeout?: number;
    loadingSelector?: string;
  } = {}
): Promise<void> {
  const { timeout = 10000, loadingSelector = '[data-testid="loading"], .loading, .spinner' } = options;
  
  // Wait for loading indicator to appear and then disappear
  const locator = page.locator(loadingSelector);
  const isVisible = await locator.isVisible().catch(() => false);
  
  if (isVisible) {
    await locator.waitFor({ state: 'hidden', timeout }).catch(() => {
      throw new Error(`Loading indicator did not disappear within ${timeout}ms`);
    });
  }
  
  // Also wait for network to be idle
  await page.waitForLoadState('networkidle', { timeout });
}

/**
 * Fill form field with validation
 */
export async function fillField(
  locator: Locator,
  value: string,
  options: { pressEnter?: boolean } = {}
): Promise<void> {
  const { pressEnter = false } = options;
  
  await locator.clear();
  await locator.fill(value);
  
  // Verify the value was set correctly
  const actualValue = await locator.inputValue();
  if (actualValue !== value) {
    throw new Error(`Field value "${actualValue}" does not match expected "${value}"`);
  }
  
  if (pressEnter) {
    await locator.press('Enter');
  }
}

/**
 * Assert toast/notification message appears
 */
export async function assertNotification(
  page: Page,
  message: string | RegExp,
  options: { timeout?: number } = {}
): Promise<void> {
  const { timeout = 5000 } = options;
  
  const notificationSelectors = [
    '[role="alert"]',
    '.toast',
    '.notification',
    '[data-testid="notification"]',
  ];
  
  let found = false;
  for (const selector of notificationSelectors) {
    const locator = page.locator(selector).filter({ hasText: message });
    const count = await locator.count();
    
    if (count > 0) {
      await expect(locator.first()).toBeVisible({ timeout });
      found = true;
      break;
    }
  }
  
  if (!found) {
    throw new Error(
      `Notification with message "${message}" not found.\n` +
      `Tried selectors: ${notificationSelectors.join(', ')}\n` +
      `Page URL: ${page.url()}`
    );
  }
}

/**
 * Validate API request payload contains expected data
 */
export async function assertAPIPayload(
  page: Page,
  urlPattern: string | RegExp,
  expectedPayload: Record<string, unknown>,
  options: {
    timeout?: number;
    method?: string;
    partial?: boolean;
  } = {}
): Promise<void> {
  const { timeout = 10000, method = 'POST', partial = false } = options;

  let capturedPayload: unknown = null;
  let payloadFound = false;

  const requestPromise = page.waitForRequest(
    (request) => {
      const url = request.url();
      const matchesPattern = typeof urlPattern === 'string'
        ? url.includes(urlPattern)
        : urlPattern.test(url);
      
      if (matchesPattern && request.method() === method) {
        try {
          capturedPayload = request.postDataJSON();
          payloadFound = true;
          return true;
        } catch {
          return false;
        }
      }
      return false;
    },
    { timeout }
  );

  await requestPromise.catch(() => {
    throw new Error(
      `API request to "${urlPattern}" with method ${method} not captured within ${timeout}ms.\n` +
      `Page URL: ${page.url()}`
    );
  });

  if (!payloadFound || !capturedPayload) {
    throw new Error(`No payload captured for API request to "${urlPattern}"`);
  }

  if (partial) {
    for (const [key, value] of Object.entries(expectedPayload)) {
      expect(capturedPayload).toHaveProperty(key, value);
    }
  } else {
    expect(capturedPayload).toMatchObject(expectedPayload);
  }
}

/**
 * Validate email data accuracy in UI
 */
export async function assertEmailData(
  page: Page,
  emailData: {
    subject?: string | RegExp;
    sender?: string | RegExp;
    body?: string | RegExp;
    category?: string;
    count?: number;
  }
): Promise<void> {
  const { subject, sender, body, category, count } = emailData;

  if (count !== undefined) {
    const emailItems = page.locator('[data-testid="email-item"], .email-item');
    const actualCount = await emailItems.count();
    if (actualCount !== count) {
      throw new Error(
        `Expected ${count} emails, but found ${actualCount}.\n` +
        `Page URL: ${page.url()}`
      );
    }
  }

  if (subject) {
    const subjectLocator = page.locator('[data-testid="email-subject"], .email-subject, .subject')
      .filter({ hasText: subject });
    await expect(subjectLocator.first()).toBeVisible({ timeout: 5000 });
  }

  if (sender) {
    const senderLocator = page.locator('[data-testid="email-sender"], .email-sender, .sender, .from')
      .filter({ hasText: sender });
    await expect(senderLocator.first()).toBeVisible({ timeout: 5000 });
  }

  if (body) {
    const bodyLocator = page.locator('[data-testid="email-body"], .email-body, .body, .content')
      .filter({ hasText: body });
    await expect(bodyLocator.first()).toBeVisible({ timeout: 5000 });
  }

  if (category) {
    const categoryLocator = page.locator(
      `[data-testid="email-category"], .category, [data-category="${category}"]`
    ).filter({ hasText: new RegExp(category, 'i') });
    await expect(categoryLocator.first()).toBeVisible({ timeout: 5000 });
  }
}

/**
 * Validate task data accuracy in UI
 */
export async function assertTaskData(
  page: Page,
  taskData: {
    title?: string | RegExp;
    description?: string | RegExp;
    status?: string;
    priority?: string;
    count?: number;
  }
): Promise<void> {
  const { title, description, status, priority, count } = taskData;

  if (count !== undefined) {
    const taskCards = page.locator('[data-testid="task-card"], .task-card');
    const actualCount = await taskCards.count();
    if (actualCount !== count) {
      throw new Error(
        `Expected ${count} tasks, but found ${actualCount}.\n` +
        `Page URL: ${page.url()}`
      );
    }
  }

  if (title) {
    const titleLocator = page.locator('[data-testid="task-title"], .task-title')
      .filter({ hasText: title });
    await expect(titleLocator.first()).toBeVisible({ timeout: 5000 });
  }

  if (description) {
    const descLocator = page.locator('[data-testid="task-description"], .task-description')
      .filter({ hasText: description });
    await expect(descLocator.first()).toBeVisible({ timeout: 5000 });
  }

  if (status) {
    const statusLocator = page.locator(`[data-task-status="${status}"], [data-testid="task-status"]`)
      .filter({ hasText: new RegExp(status, 'i') });
    await expect(statusLocator.first()).toBeVisible({ timeout: 5000 });
  }

  if (priority) {
    const priorityLocator = page.locator(`[data-task-priority="${priority}"], [data-testid="task-priority"]`)
      .filter({ hasText: new RegExp(priority, 'i') });
    await expect(priorityLocator.first()).toBeVisible({ timeout: 5000 });
  }
}

/**
 * Validate error message content and type
 */
export async function assertErrorMessage(
  page: Page,
  expectedError: {
    message: string | RegExp;
    type?: 'error' | 'warning' | 'info';
    contains?: string[];
  },
  options: { timeout?: number } = {}
): Promise<void> {
  const { timeout = 5000 } = options;
  const { message, type, contains } = expectedError;

  const errorSelectors = [
    '[role="alert"]',
    '.error',
    '.error-message',
    '.alert-danger',
    '[data-testid="error-message"]',
  ];

  if (type === 'warning') {
    errorSelectors.push('.warning', '.alert-warning', '[data-testid="warning"]');
  } else if (type === 'info') {
    errorSelectors.push('.info', '.alert-info', '[data-testid="info"]');
  }

  let errorElement: Locator | null = null;
  for (const selector of errorSelectors) {
    const locator = page.locator(selector).filter({ hasText: message });
    const count = await locator.count();
    if (count > 0) {
      errorElement = locator.first();
      break;
    }
  }

  if (!errorElement) {
    throw new Error(
      `Error message matching "${message}" not found.\n` +
      `Tried selectors: ${errorSelectors.join(', ')}\n` +
      `Page URL: ${page.url()}`
    );
  }

  await expect(errorElement).toBeVisible({ timeout });

  if (contains && contains.length > 0) {
    const errorText = await errorElement.textContent();
    for (const keyword of contains) {
      if (!errorText?.toLowerCase().includes(keyword.toLowerCase())) {
        throw new Error(
          `Error message does not contain expected keyword "${keyword}".\n` +
          `Actual message: "${errorText}"\n` +
          `Page URL: ${page.url()}`
        );
      }
    }
  }
}

/**
 * Validate API response data structure
 */
export async function assertAPIResponseStructure(
  page: Page,
  urlPattern: string | RegExp,
  expectedStructure: {
    requiredFields: string[];
    optionalFields?: string[];
    statusCode?: number;
  },
  options: { timeout?: number } = {}
): Promise<unknown> {
  const { timeout = 10000 } = options;
  const { requiredFields, optionalFields, statusCode = 200 } = expectedStructure;

  const response = await page.waitForResponse(
    (resp) => {
      const url = resp.url();
      const matchesPattern = typeof urlPattern === 'string'
        ? url.includes(urlPattern)
        : urlPattern.test(url);
      return matchesPattern && resp.status() === statusCode;
    },
    { timeout }
  ).catch(() => {
    throw new Error(
      `API response matching "${urlPattern}" with status ${statusCode} not received within ${timeout}ms.\n` +
      `Page URL: ${page.url()}`
    );
  });

  const data = await response.json();

  for (const field of requiredFields) {
    if (!(field in data)) {
      throw new Error(
        `Required field "${field}" missing from API response.\n` +
        `Response data: ${JSON.stringify(data, null, 2)}\n` +
        `API URL: ${response.url()}`
      );
    }
  }

  return data;
}

/**
 * Validate state persistence across page reloads
 */
export async function assertStatePersistence(
  page: Page,
  stateChecks: {
    localStorage?: Record<string, unknown>;
    sessionStorage?: Record<string, unknown>;
    urlParams?: Record<string, string>;
  }
): Promise<void> {
  const { localStorage: localStorageChecks, sessionStorage: sessionStorageChecks, urlParams } = stateChecks;

  if (localStorageChecks) {
    for (const [key, expectedValue] of Object.entries(localStorageChecks)) {
      await assertLocalStorage(page, key, expectedValue);
    }
  }

  if (sessionStorageChecks) {
    for (const [key, expectedValue] of Object.entries(sessionStorageChecks)) {
      await assertSessionStorage(page, key, expectedValue);
    }
  }

  if (urlParams) {
    const currentUrl = new URL(page.url());
    for (const [param, expectedValue] of Object.entries(urlParams)) {
      const actualValue = currentUrl.searchParams.get(param);
      if (actualValue !== expectedValue) {
        throw new Error(
          `URL parameter "${param}" has value "${actualValue}", expected "${expectedValue}".\n` +
          `Page URL: ${page.url()}`
        );
      }
    }
  }
}

/**
 * Validate accessibility attributes
 */
export async function assertAccessibility(
  locator: Locator,
  checks: {
    role?: string;
    ariaLabel?: string | RegExp;
    ariaDescribedBy?: boolean;
    tabIndex?: number;
    hasAltText?: boolean;
  }
): Promise<void> {
  const { role, ariaLabel, ariaDescribedBy, tabIndex, hasAltText } = checks;

  if (role) {
    await expect(locator).toHaveAttribute('role', role);
  }

  if (ariaLabel) {
    await expect(locator).toHaveAttribute('aria-label', ariaLabel);
  }

  if (ariaDescribedBy) {
    const describedBy = await locator.getAttribute('aria-describedby');
    if (!describedBy) {
      throw new Error('Element missing aria-describedby attribute');
    }
  }

  if (tabIndex !== undefined) {
    await expect(locator).toHaveAttribute('tabindex', String(tabIndex));
  }

  if (hasAltText) {
    const tagName = await locator.evaluate((el) => el.tagName.toLowerCase());
    if (tagName === 'img') {
      const alt = await locator.getAttribute('alt');
      if (!alt || alt.trim() === '') {
        throw new Error('Image element missing alt text');
      }
    }
  }
}

/**
 * Capture and validate API call sequence
 */
export async function assertAPICallSequence(
  page: Page,
  expectedSequence: Array<{
    urlPattern: string | RegExp;
    method: string;
    order: number;
  }>,
  options: { timeout?: number } = {}
): Promise<void> {
  const { timeout = 15000 } = options;
  const capturedCalls: Array<{ url: string; method: string; timestamp: number }> = [];

  const requestHandler = (request: Request) => {
    for (const expected of expectedSequence) {
      const url = request.url();
      const matchesPattern = typeof expected.urlPattern === 'string'
        ? url.includes(expected.urlPattern)
        : expected.urlPattern.test(url);
      
      if (matchesPattern && request.method() === expected.method) {
        capturedCalls.push({
          url,
          method: request.method(),
          timestamp: Date.now(),
        });
      }
    }
  };

  page.on('request', requestHandler);

  await page.waitForTimeout(timeout);

  page.off('request', requestHandler);

  if (capturedCalls.length < expectedSequence.length) {
    throw new Error(
      `Expected ${expectedSequence.length} API calls, but captured only ${capturedCalls.length}.\n` +
      `Captured: ${JSON.stringify(capturedCalls, null, 2)}\n` +
      `Expected: ${JSON.stringify(expectedSequence, null, 2)}`
    );
  }

  for (let i = 0; i < expectedSequence.length - 1; i++) {
    if (capturedCalls[i].timestamp > capturedCalls[i + 1].timestamp) {
      throw new Error(
        `API calls not in expected order.\n` +
        `Call ${i} (${capturedCalls[i].method} ${capturedCalls[i].url}) ` +
        `happened after Call ${i + 1} (${capturedCalls[i + 1].method} ${capturedCalls[i + 1].url})`
      );
    }
  }
}

/**
 * Validate form validation behavior
 */
export async function assertFormValidation(
  page: Page,
  formSelector: string,
  validationTests: Array<{
    field: string;
    invalidValue: string;
    expectedError: string | RegExp;
  }>
): Promise<void> {
  const form = page.locator(formSelector);
  await expect(form).toBeVisible();

  for (const test of validationTests) {
    const fieldLocator = form.locator(`[name="${test.field}"], #${test.field}`);
    await fieldLocator.clear();
    await fieldLocator.fill(test.invalidValue);
    await fieldLocator.blur();

    await page.waitForTimeout(500);

    const errorLocator = page.locator(
      `[id="${test.field}-error"], [data-error-for="${test.field}"], .error, .invalid-feedback`
    ).filter({ hasText: test.expectedError });

    await expect(errorLocator).toBeVisible({ timeout: 3000 });
  }
}
