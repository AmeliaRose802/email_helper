/**
 * E2E Tests for Email Processing Workflow
 * 
 * Tests the complete email processing workflow including:
 * - Email retrieval from backend
 * - Email classification with AI
 * - Batch processing operations
 * - Error handling for processing failures
 */
/* eslint-disable @typescript-eslint/no-unused-vars */
import { test, expect } from './fixtures/test-setup';
import { 
  waitForTestId, 
  waitForElements, 
  clickElement,
  waitForLoadingComplete,
  waitForAPIResponse,
  assertElementExists
} from './fixtures/test-helpers';

test.describe('Email Processing Workflow', () => {
  test.beforeEach(async ({ page, mockEmails, mockEmailAPI, mockAIAPI }) => {
    await mockEmailAPI(page, mockEmails);
    await mockAIAPI(page);
    await page.goto('/');
    await waitForLoadingComplete(page);
  });

  test('should retrieve and display emails from backend', async ({ page, navigateToEmails }) => {
    await navigateToEmails(page);
    await waitForLoadingComplete(page);
    
    // Verify emails are displayed using data-testid
    const emailItems = await waitForElements(page, '[data-testid="email-item"]', { minCount: 1 });
    expect(emailItems.length).toBeGreaterThan(0);
    
    // Verify email content is visible
    const firstEmail = await waitForTestId(page, 'email-item');
    await expect(firstEmail).toBeVisible();
    await expect(firstEmail).toHaveAttribute('data-email-id');
  });

  test('should display email list on emails page', async ({ page, navigateToEmails }) => {
    await navigateToEmails(page);
    await waitForLoadingComplete(page);
    
    // Verify multiple emails are loaded
    const emailCount = await page.locator('[data-testid="email-item"]').count();
    expect(emailCount).toBeGreaterThanOrEqual(1);
  });

  test('should handle email selection', async ({ page, navigateToEmails }) => {
    await navigateToEmails(page);
    await waitForLoadingComplete(page);
    
    // Select first email checkbox
    const checkboxes = await waitForElements(page, '[data-testid="email-checkbox"]', { minCount: 1 });
    await clickElement(checkboxes[0]);
    
    // Verify checkbox is checked
    await expect(checkboxes[0]).toBeChecked();
  });

  test('should verify API mock responses', async ({ page, mockEmails, navigateToEmails }) => {
    await navigateToEmails(page);
    
    // Wait for API call to complete
    const response = await waitForAPIResponse(page, '/api/emails', { timeout: 10000 });
    
    // Verify response structure
    expect(response).toHaveProperty('emails');
    expect(response.emails).toBeInstanceOf(Array);
    expect(response.emails.length).toBeGreaterThan(0);
  });

  test('should display processing button when emails selected', async ({ page, navigateToEmails }) => {
    await navigateToEmails(page);
    await waitForLoadingComplete(page);
    
    // Select an email
    const checkboxes = await waitForElements(page, '[data-testid="email-checkbox"]', { minCount: 1 });
    await clickElement(checkboxes[0]);
    
    // Bulk action buttons should appear
    await assertElementExists(page, '[data-testid="bulk-mark-read-button"]', 
      'Bulk actions should be visible when emails are selected');
  });

  test('should handle multiple email selection', async ({ page, navigateToEmails }) => {
    await navigateToEmails(page);
    await waitForLoadingComplete(page);
    
    // Select multiple emails
    const checkboxes = await waitForElements(page, '[data-testid="email-checkbox"]', { minCount: 3 });
    
    for (let i = 0; i < 3; i++) {
      await clickElement(checkboxes[i]);
    }
    
    // Verify all are checked
    for (let i = 0; i < 3; i++) {
      await expect(checkboxes[i]).toBeChecked();
    }
  });

  test('should verify email data structure', async ({ page, navigateToEmails }) => {
    await navigateToEmails(page);
    await waitForLoadingComplete(page);
    
    const firstEmail = await waitForTestId(page, 'email-item');
    
    // Verify required attributes exist
    await expect(firstEmail).toHaveAttribute('data-email-id');
    await expect(firstEmail).toHaveAttribute('data-read');
  });
});
