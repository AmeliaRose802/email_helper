/**
 * Test Helper Utilities
 * 
 * Provides reusable utilities for E2E tests including:
 * - Robust wait strategies
 * - Element existence assertions
 * - Data validation helpers
 */

import { Page, Locator, expect } from '@playwright/test';

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
  
  await expect(locator).toHaveCount(minCount, { timeout }).catch(() => {
    throw new Error(
      `Expected at least ${minCount} elements matching "${selector}", but found none.\n` +
      `Page URL: ${page.url()}`
    );
  });
  
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
  
  await locator.waitFor({ state, timeout }).catch(() => {
    throw new Error(
      `Element with data-testid="${testId}" not found.\n` +
      `Page URL: ${page.url()}`
    );
  });
  
  return locator;
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
): Promise<any> {
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
  expectedValue?: any
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
  expectedValue?: any
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
