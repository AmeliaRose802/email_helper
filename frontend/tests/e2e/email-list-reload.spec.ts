import { test, expect } from '@playwright/test';

/**
 * Email List Page Reload Tests
 * 
 * These tests verify that the email list page handles page reloads correctly,
 * including:
 * - Classification state persistence
 * - Page navigation state
 * - No crashes or errors on reload
 */

test.describe('Email List Page Reload', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to email list page
    await page.goto('http://localhost:5173/#/emails');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('should not crash on page reload', async ({ page }) => {
    // Wait for initial load
    await page.waitForSelector('.email-list-container', { timeout: 10000 });
    
    // Reload the page
    await page.reload();
    
    // Verify page loads without errors
    await page.waitForSelector('.email-list-container', { timeout: 10000 });
    
    // Check that no error overlays are shown
    const errorOverlay = page.locator('.email-list-error-overlay');
    await expect(errorOverlay).not.toBeVisible();
    
    // Verify email list is functional
    const emailListTitle = page.locator('.email-list-title');
    await expect(emailListTitle).toContainText('Inbox');
  });

  test('should preserve classification state after reload', async ({ page }) => {
    // Wait for initial load and classification to start
    await page.waitForSelector('.email-list-container', { timeout: 10000 });
    
    // Wait a bit for some classifications to happen
    await page.waitForTimeout(5000);
    
    // Check sessionStorage for classified emails
    const classifiedEmailsBefore = await page.evaluate(() => {
      const stored = sessionStorage.getItem('classifiedEmails');
      return stored ? JSON.parse(stored) : {};
    });
    
    // Reload the page
    await page.reload();
    await page.waitForSelector('.email-list-container', { timeout: 10000 });
    
    // Check that sessionStorage is restored
    const classifiedEmailsAfter = await page.evaluate(() => {
      const stored = sessionStorage.getItem('classifiedEmails');
      return stored ? JSON.parse(stored) : {};
    });
    
    // If classifications happened before reload, they should be preserved
    if (Object.keys(classifiedEmailsBefore).length > 0) {
      expect(Object.keys(classifiedEmailsAfter).length).toBeGreaterThan(0);
    }
  });

  test('should handle multiple reloads gracefully', async ({ page }) => {
    // Perform multiple reloads
    for (let i = 0; i < 3; i++) {
      await page.reload();
      await page.waitForSelector('.email-list-container', { timeout: 10000 });
      
      // Check no error state
      const errorOverlay = page.locator('.email-list-error-overlay');
      await expect(errorOverlay).not.toBeVisible();
      
      // Small delay between reloads
      await page.waitForTimeout(1000);
    }
    
    // Verify page is still functional
    const emailListTitle = page.locator('.email-list-title');
    await expect(emailListTitle).toBeVisible();
  });

  test('should clear sessionStorage when explicitly requested', async ({ page }) => {
    // Wait for initial load
    await page.waitForSelector('.email-list-container', { timeout: 10000 });
    
    // Wait for some classifications
    await page.waitForTimeout(3000);
    
    // Clear sessionStorage
    await page.evaluate(() => {
      sessionStorage.removeItem('classifiedEmails');
      sessionStorage.removeItem('classifiedPages');
    });
    
    // Reload the page
    await page.reload();
    await page.waitForSelector('.email-list-container', { timeout: 10000 });
    
    // Verify sessionStorage is empty initially
    const classifiedEmails = await page.evaluate(() => {
      return sessionStorage.getItem('classifiedEmails');
    });
    
    // It should be null or empty after clearing
    expect(classifiedEmails).toBeFalsy();
  });

  test('should handle navigation between pages and reload', async ({ page }) => {
    // Wait for initial load
    await page.waitForSelector('.email-list-container', { timeout: 10000 });
    
    // Try to find and click next page button if it exists
    const nextButton = page.locator('.email-pagination-button').filter({ hasText: 'Next' });
    const isEnabled = await nextButton.isEnabled().catch(() => false);
    
    if (isEnabled) {
      await nextButton.click();
      await page.waitForTimeout(2000);
    }
    
    // Reload the page
    await page.reload();
    await page.waitForSelector('.email-list-container', { timeout: 10000 });
    
    // Verify no errors
    const errorOverlay = page.locator('.email-list-error-overlay');
    await expect(errorOverlay).not.toBeVisible();
  });
});

test.describe('Email List Error Handling', () => {
  test('should show error state when backend is unreachable', async ({ page }) => {
    // Block all API requests to simulate backend failure
    await page.route('**/api/**', route => route.abort());
    
    // Navigate to email list
    await page.goto('http://localhost:5173/#/emails');
    
    // Wait for error state to appear
    await page.waitForSelector('.email-list-error-overlay', { timeout: 10000 });
    
    // Verify error message is shown
    const errorTitle = page.locator('.email-list-error-overlay__title');
    await expect(errorTitle).toContainText('Error');
    
    // Verify retry button exists
    const retryButton = page.locator('.email-list-error-overlay__retry-btn');
    await expect(retryButton).toBeVisible();
  });
});
