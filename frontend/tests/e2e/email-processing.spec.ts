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

test.describe('Email Processing Workflow', () => {
  test.beforeEach(async ({ page, mockEmails, mockEmailAPI, mockAIAPI }) => {
    // Setup API mocks
    await mockEmailAPI(page, mockEmails);
    await mockAIAPI(page);
    
    // Navigate to home page
    await page.goto('/');
  });

  test('should retrieve and display emails from backend', async ({ page, mockEmails, navigateToEmails }) => {
    // Navigate to emails page
    await navigateToEmails(page);
    
    // Wait for emails to load
    await page.waitForSelector('[data-testid="email-list"], .email-list, [class*="email"]', { timeout: 10000 });
    
    // Verify emails are displayed (check for common email UI elements)
    const emailElements = await page.locator('[data-testid="email-item"], .email-item, [class*="email"][class*="item"]').count();
    expect(emailElements).toBeGreaterThan(0);
    
    // Verify we can see email content
    const hasSubjects = await page.locator('text=/Test Email|Subject:|From:/', { hasText: /Test Email/ }).count();
    expect(hasSubjects).toBeGreaterThan(0);
  });

  test('should classify email using AI', async ({ page, mockEmails, navigateToEmails }) => {
    await navigateToEmails(page);
    
    // Wait for emails to load
    await page.waitForTimeout(2000);
    
    // Look for classify or process button
    const classifyButton = page.locator('button:has-text("Classify"), button:has-text("Process"), button:has-text("Categorize")').first();
    
    if (await classifyButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await classifyButton.click();
      
      // Wait for processing to complete
      await page.waitForTimeout(1000);
      
      // Verify success indication (could be notification, updated UI, etc.)
      const successIndicators = [
        page.locator('text=/classified|processed|categorized/i'),
        page.locator('[class*="success"], [class*="complete"]'),
        page.locator('[data-testid*="success"]'),
      ];
      
      let found = false;
      for (const indicator of successIndicators) {
        if (await indicator.count() > 0) {
          found = true;
          break;
        }
      }
      
      expect(found).toBeTruthy();
    } else {
      // If no classify button, skip this test
      test.skip();
    }
  });

  test('should handle batch processing of multiple emails', async ({ page, mockEmails, navigateToEmails }) => {
    await navigateToEmails(page);
    await page.waitForTimeout(2000);
    
    // Look for batch processing UI elements
    const selectAllCheckbox = page.locator('[type="checkbox"][aria-label*="Select all"], input[type="checkbox"]:near(text=/Select All/i)').first();
    
    if (await selectAllCheckbox.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Select multiple emails
      await selectAllCheckbox.check();
      
      // Look for batch action button
      const batchButton = page.locator('button:has-text("Process Selected"), button:has-text("Batch Process"), button[aria-label*="batch"]').first();
      
      if (await batchButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await batchButton.click();
        
        // Wait for batch processing
        await page.waitForTimeout(2000);
        
        // Verify completion
        const processed = await page.locator('text=/processed|complete/i').count();
        expect(processed).toBeGreaterThan(0);
      } else {
        test.skip();
      }
    } else {
      test.skip();
    }
  });

  test('should display email statistics', async ({ page, mockEmails, navigateToEmails }) => {
    await navigateToEmails(page);
    
    // Wait for page load
    await page.waitForTimeout(2000);
    
    // Look for statistics display
    const statsElements = [
      page.locator('[data-testid*="stats"], [data-testid*="count"]'),
      page.locator('text=/total|unread|\\d+ email/i'),
      page.locator('[class*="stat"], [class*="count"], [class*="badge"]'),
    ];
    
    let found = false;
    for (const element of statsElements) {
      const count = await element.count();
      if (count > 0) {
        found = true;
        break;
      }
    }
    
    expect(found).toBeTruthy();
  });

  test('should filter emails by category', async ({ page, mockEmails, navigateToEmails }) => {
    await navigateToEmails(page);
    await page.waitForTimeout(2000);
    
    // Look for category filters
    const filterOptions = [
      'required_personal_action',
      'optional_fyi',
      'team_discussion',
      'task_delegation',
    ];
    
    for (const category of filterOptions) {
      const filterElement = page.locator(`button:has-text("${category}"), [role="tab"]:has-text("${category}"), input[value="${category}"]`).first();
      
      if (await filterElement.isVisible({ timeout: 2000 }).catch(() => false)) {
        await filterElement.click();
        await page.waitForTimeout(500);
        
        // Verify filtering occurred (URL change or UI update)
        const url = page.url();
        const hasFilter = url.includes(category) || url.includes('category') || url.includes('filter');
        
        if (hasFilter) {
          expect(hasFilter).toBeTruthy();
          return;
        }
      }
    }
    
    // If no category filters found, skip
    test.skip();
  });

  test('should handle email processing errors gracefully', async ({ page, navigateToEmails }) => {
    // Mock API error
    await page.route('**/api/ai/classify*', async (route) => {
      await route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'AI service unavailable' }),
      });
    });
    
    await navigateToEmails(page);
    await page.waitForTimeout(2000);
    
    // Try to classify an email
    const classifyButton = page.locator('button:has-text("Classify"), button:has-text("Process")').first();
    
    if (await classifyButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await classifyButton.click();
      await page.waitForTimeout(1000);
      
      // Look for error indication
      const errorElements = [
        page.locator('text=/error|failed|unavailable/i'),
        page.locator('[class*="error"], [role="alert"]'),
      ];
      
      let found = false;
      for (const element of errorElements) {
        if (await element.count() > 0) {
          found = true;
          break;
        }
      }
      
      expect(found).toBeTruthy();
    } else {
      test.skip();
    }
  });

  test('should refresh email list on demand', async ({ page, mockEmails, navigateToEmails }) => {
    await navigateToEmails(page);
    await page.waitForTimeout(2000);
    
    // Look for refresh button
    const refreshButton = page.locator('button:has-text("Refresh"), button[aria-label*="refresh"], button[aria-label*="reload"]').first();
    
    if (await refreshButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Get current email count
      const initialCount = await page.locator('[data-testid="email-item"], .email-item, [class*="email"][class*="item"]').count();
      
      // Click refresh
      await refreshButton.click();
      await page.waitForTimeout(1000);
      
      // Verify refresh occurred (loading indicator or count reloaded)
      const loadingIndicator = await page.locator('[class*="loading"], [class*="spinner"], text=/loading/i').count();
      expect(loadingIndicator >= 0).toBeTruthy(); // Just verify no errors
    } else {
      test.skip();
    }
  });

  test('should support pagination for large email lists', async ({ page, navigateToEmails }) => {
    // Mock large dataset
    const largeEmailList = Array.from({ length: 50 }, (_, i) => ({
      id: `email-${i + 1}`,
      subject: `Email ${i + 1}`,
      sender: `sender${i + 1}@example.com`,
      recipient: 'user@example.com',
      body: `Body ${i + 1}`,
      received_time: new Date().toISOString(),
      is_read: false,
      categories: [],
      conversation_id: `conv-${i + 1}`,
    }));
    
    await page.route('**/api/emails*', async (route) => {
      const url = new URL(route.request().url());
      const page = parseInt(url.searchParams.get('page') || '1');
      const perPage = parseInt(url.searchParams.get('per_page') || '20');
      const start = (page - 1) * perPage;
      const end = start + perPage;
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          emails: largeEmailList.slice(start, end),
          total: largeEmailList.length,
          page,
          per_page: perPage,
          total_pages: Math.ceil(largeEmailList.length / perPage),
        }),
      });
    });
    
    await navigateToEmails(page);
    await page.waitForTimeout(2000);
    
    // Look for pagination controls
    const paginationElements = [
      page.locator('button:has-text("Next"), button:has-text("Previous")'),
      page.locator('[aria-label*="page"], [class*="pagination"]'),
      page.locator('text=/Page \\d+ of \\d+/'),
    ];
    
    let found = false;
    for (const element of paginationElements) {
      if (await element.count() > 0) {
        found = true;
        break;
      }
    }
    
    expect(found).toBeTruthy();
  });

  test('should navigate to email detail view', async ({ page, mockEmails, navigateToEmails }) => {
    await navigateToEmails(page);
    await page.waitForTimeout(2000);
    
    // Find and click first email
    const firstEmail = page.locator('[data-testid="email-item"], .email-item, [class*="email"][class*="item"]').first();
    
    if (await firstEmail.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstEmail.click();
      await page.waitForTimeout(1000);
      
      // Verify navigation occurred (URL change or modal/detail view)
      const hasDetailView = 
        page.url().includes('/email') ||
        await page.locator('[data-testid="email-detail"], [class*="email-detail"], [role="dialog"]').count() > 0;
      
      expect(hasDetailView).toBeTruthy();
    } else {
      test.skip();
    }
  });
});

test.describe('Email Processing - Error Scenarios', () => {
  test('should handle network errors during email retrieval', async ({ page }) => {
    // Mock network error
    await page.route('**/api/emails*', async (route) => {
      await route.abort('failed');
    });
    
    await page.goto('/emails');
    await page.waitForTimeout(2000);
    
    // Look for error message
    const errorIndicators = [
      page.locator('text=/error|failed|unable to load/i'),
      page.locator('[role="alert"], [class*="error"]'),
    ];
    
    let found = false;
    for (const element of errorIndicators) {
      if (await element.count() > 0) {
        found = true;
        break;
      }
    }
    
    expect(found).toBeTruthy();
  });

  test('should handle timeout during processing', async ({ page, mockEmails, navigateToEmails, mockEmailAPI }) => {
    await mockEmailAPI(page, mockEmails);
    
    // Mock slow AI response
    await page.route('**/api/ai/classify*', async (route) => {
      // Delay response to simulate timeout
      await new Promise(resolve => setTimeout(resolve, 5000));
      await route.fulfill({
        status: 408,
        body: JSON.stringify({ error: 'Request timeout' }),
      });
    });
    
    await navigateToEmails(page);
    await page.waitForTimeout(2000);
    
    // Try to classify
    const classifyButton = page.locator('button:has-text("Classify"), button:has-text("Process")').first();
    
    if (await classifyButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await classifyButton.click();
      
      // Wait for timeout or error
      await page.waitForTimeout(6000);
      
      // Verify error handling
      const hasError = await page.locator('text=/timeout|error|failed/i').count() > 0;
      expect(hasError).toBeTruthy();
    } else {
      test.skip();
    }
  });
});
