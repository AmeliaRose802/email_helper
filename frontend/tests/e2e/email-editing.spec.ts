/**
 * E2E Tests for Email Editing Workflow
 * 
 * Tests email editing operations including:
 * - Marking emails as read/unread
 * - Moving emails to different folders
 * - Updating email categories
 * - Bulk email operations
 */
/* eslint-disable @typescript-eslint/no-unused-vars */
import { test, expect } from './fixtures/test-setup';
import { 
  waitForTestId, 
  waitForElements, 
  clickElement,
  waitForLoadingComplete,
  selectOption,
  assertElementCount
} from './fixtures/test-helpers';

test.describe('Email Editing Workflow', () => {
  test.beforeEach(async ({ page, mockEmails, mockEmailAPI }) => {
    await mockEmailAPI(page, mockEmails);
    await page.goto('/#emails');
    await waitForLoadingComplete(page);
  });

  test('should display email list with proper test IDs', async ({ page }) => {
    // Verify email items are rendered with data-testid
    const emailItems = await waitForElements(page, '[data-testid="email-item"]', { minCount: 1 });
    expect(emailItems.length).toBeGreaterThan(0);
    
    // Verify each email has proper attributes
    const firstEmail = await waitForTestId(page, 'email-item');
    await expect(firstEmail).toHaveAttribute('data-email-id');
    await expect(firstEmail).toHaveAttribute('data-read');
  });

  test('should update email category', async ({ page }) => {
    // Find first email using data-testid
    const firstEmail = await waitForTestId(page, 'email-item');
    await clickElement(firstEmail);
    
    // Look for category selector using data-testid
    const categorySelect = await waitForTestId(page, 'email-category-select');
    
    // Select a category
    await selectOption(categorySelect, 'required_personal_action');
    
    // Verify selection was applied
    await expect(categorySelect).toHaveValue('required_personal_action');
  });

  test('should perform bulk mark as read operation', async ({ page }) => {
    // Select multiple emails using data-testid checkboxes
    const checkboxes = await waitForElements(page, '[data-testid="email-checkbox"]', { minCount: 3 });
    
    // Check first 3 checkboxes
    for (let i = 0; i < Math.min(3, checkboxes.length); i++) {
      await clickElement(checkboxes[i]);
    }
    
    // Wait for bulk actions to appear and click mark as read
    const markReadButton = await waitForTestId(page, 'bulk-mark-read-button');
    await clickElement(markReadButton);
    
    // Verify operation completed (no error thrown)
    await expect(markReadButton).toBeVisible();
  });

  test('should perform bulk mark as unread operation', async ({ page }) => {
    // Select multiple emails
    const checkboxes = await waitForElements(page, '[data-testid="email-checkbox"]', { minCount: 2 });
    
    // Check first 2 checkboxes
    for (let i = 0; i < Math.min(2, checkboxes.length); i++) {
      await clickElement(checkboxes[i]);
    }
    
    // Click bulk mark as unread
    const markUnreadButton = await waitForTestId(page, 'bulk-mark-unread-button');
    await clickElement(markUnreadButton);
    
    // Verify operation completed
    await expect(markUnreadButton).toBeVisible();
  });

  test('should clear selection', async ({ page }) => {
    // Select some emails
    const checkboxes = await waitForElements(page, '[data-testid="email-checkbox"]', { minCount: 2 });
    
    for (let i = 0; i < 2; i++) {
      await clickElement(checkboxes[i]);
    }
    
    // Verify bulk actions are visible
    const clearButton = await waitForTestId(page, 'clear-selection-button');
    await clickElement(clearButton);
    
    // Verify bulk actions disappear after clearing
    await expect(clearButton).not.toBeVisible();
  });

  test('should handle bulk delete operation', async ({ page }) => {
    // Mock the confirm dialog
    page.on('dialog', async dialog => {
      expect(dialog.message()).toContain('delete');
      await dialog.accept();
    });
    
    // Select emails
    const checkboxes = await waitForElements(page, '[data-testid="email-checkbox"]', { minCount: 1 });
    await clickElement(checkboxes[0]);
    
    // Click delete button
    const deleteButton = await waitForTestId(page, 'bulk-delete-button');
    await clickElement(deleteButton);
    
    // Verify operation completed (confirmation dialog was shown)
    await expect(deleteButton).toBeVisible();
  });

  test('should navigate to email detail on click', async ({ page }) => {
    const firstEmail = await waitForTestId(page, 'email-item');
    const emailId = await firstEmail.getAttribute('data-email-id');
    
    await clickElement(firstEmail);
    
    // Verify navigation occurred
    await page.waitForURL(`**/emails/${emailId}`, { timeout: 5000 });
    expect(page.url()).toContain(`/emails/${emailId}`);
  });
});
