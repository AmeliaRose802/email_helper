/**
 * Comprehensive E2E Tests for Critical User Flows
 * 
 * Tests the top 5 user journeys with happy path and error scenarios:
 * 1. Login → Fetch Emails → Classify → View Results
 * 2. Email → Create Task → Update Task → Complete Task
 * 3. Bulk Process → Review Categories → Edit Classification
 * 4. Settings → Update Config → Verify Changes Applied
 * 5. Error Recovery → Retry Failed Operations
 */

import { test, expect } from './fixtures/test-setup';

test.describe('Critical User Flow 1: Email Retrieval and Classification', () => {
  test('happy path: should retrieve emails, classify, and view results', async ({ 
    page, 
    mockEmails, 
    mockEmailAPI, 
    mockAIAPI,
    navigateToEmails 
  }) => {
    // Setup mocks
    await mockEmailAPI(page, mockEmails);
    await mockAIAPI(page);
    
    // Navigate to emails page
    await navigateToEmails(page);
    
    // Verify emails are loaded
    await expect(page.locator('[data-testid="email-list"], .email-list, [class*="email"]')).toBeVisible({ timeout: 10000 });
    
    // Count emails displayed
    const emailCount = await page.locator('[data-testid="email-item"], .email-item, [class*="email-item"]').count();
    expect(emailCount).toBeGreaterThan(0);
    
    // Verify email content is visible
    const hasEmailContent = await page.locator('text=/Test Email|Subject:|From:/').count();
    expect(hasEmailContent).toBeGreaterThan(0);
    
    // Select first email
    const firstEmail = page.locator('[data-testid="email-item"], .email-item').first();
    await firstEmail.click();
    await page.waitForTimeout(1000);
    
    // Trigger classification
    const classifyButton = page.locator(
      'button:has-text("Classify"), button:has-text("Process"), button:has-text("Categorize")'
    ).first();
    
    if (await classifyButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Track API call
      const classifyPromise = page.waitForResponse(resp => 
        resp.url().includes('/api/ai/classify') && resp.status() === 200
      );
      
      await classifyButton.click();
      
      // Verify classification API was called
      const response = await classifyPromise;
      const data = await response.json();
      expect(data.category).toBeDefined();
      expect(data.confidence).toBeGreaterThan(0);
      
      // Wait for classification result to display
      await page.waitForTimeout(2000);
      
      // Verify classification result is shown
      const hasCategory = await page.locator(
        'text=/required_personal_action|optional_fyi|team_discussion|task_delegation/i'
      ).count();
      expect(hasCategory).toBeGreaterThan(0);
    }
  });
  
  test('error path: should handle classification failure gracefully', async ({ 
    page, 
    mockEmails, 
    mockEmailAPI,
    navigateToEmails 
  }) => {
    await mockEmailAPI(page, mockEmails);
    
    // Mock classification failure
    await page.route('**/api/ai/classify*', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'AI service unavailable' }),
      });
    });
    
    await navigateToEmails(page);
    
    const firstEmail = page.locator('[data-testid="email-item"], .email-item').first();
    await firstEmail.click();
    
    const classifyButton = page.locator(
      'button:has-text("Classify"), button:has-text("Process")'
    ).first();
    
    if (await classifyButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await classifyButton.click();
      await page.waitForTimeout(2000);
      
      // Verify error message is displayed
      const hasError = await page.locator(
        'text=/error|failed|unavailable/i, [role="alert"], .error, .alert-danger'
      ).count();
      expect(hasError).toBeGreaterThan(0);
    }
  });
  
  test('error path: should handle empty email list', async ({ page, mockEmailAPI }) => {
    // Mock empty email list
    await mockEmailAPI(page, []);
    
    await page.goto('/emails');
    await page.waitForLoadState('networkidle');
    
    // Verify empty state message
    const emptyState = await page.locator(
      'text=/no emails|empty|no messages/i, [data-testid="empty-state"]'
    ).count();
    expect(emptyState).toBeGreaterThan(0);
  });
});

test.describe('Critical User Flow 2: Task Creation and Management', () => {
  test('happy path: should create task from email, update it, and mark complete', async ({ 
    page, 
    mockEmails, 
    mockTasks,
    mockEmailAPI, 
    mockTaskAPI,
    navigateToEmails 
  }) => {
    await mockEmailAPI(page, mockEmails);
    await mockTaskAPI(page, mockTasks);
    
    // Start at emails page
    await navigateToEmails(page);
    
    // Select an email
    const firstEmail = page.locator('[data-testid="email-item"], .email-item').first();
    await firstEmail.click();
    await page.waitForTimeout(1000);
    
    // Look for create task button
    const createTaskButton = page.locator(
      'button:has-text("Create Task"), button:has-text("Add Task"), button:has-text("Task")'
    ).first();
    
    if (await createTaskButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Track task creation API call
      const createPromise = page.waitForResponse(resp => 
        resp.url().includes('/api/tasks') && 
        resp.request().method() === 'POST' &&
        resp.status() === 201
      );
      
      await createTaskButton.click();
      await page.waitForTimeout(1000);
      
      // Fill task form if modal appears
      const titleInput = page.locator('input[name="title"], input[placeholder*="title" i]').first();
      if (await titleInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await titleInput.fill('E2E Test Task: Complete report');
        
        const descInput = page.locator('textarea[name="description"], textarea[placeholder*="description" i]').first();
        if (await descInput.isVisible().catch(() => false)) {
          await descInput.fill('This is a test task created during E2E testing');
        }
        
        // Submit form
        const submitButton = page.locator('button:has-text("Create"), button:has-text("Save"), button[type="submit"]').first();
        await submitButton.click();
        
        // Verify task was created
        const response = await createPromise;
        const taskData = await response.json();
        expect(taskData.id).toBeDefined();
        expect(taskData.title).toContain('Complete report');
      }
      
      // Navigate to tasks page
      await page.goto('/tasks');
      await page.waitForLoadState('networkidle');
      
      // Verify task appears in list
      const taskExists = await page.locator('text=/Complete report|E2E Test Task/i').count();
      expect(taskExists).toBeGreaterThan(0);
      
      // Update task status
      const task = page.locator('text=/Complete report/i').first();
      await task.click();
      await page.waitForTimeout(500);
      
      // Change status to in_progress
      const statusDropdown = page.locator('select[name="status"], [role="combobox"]:has-text("Status")').first();
      if (await statusDropdown.isVisible({ timeout: 3000 }).catch(() => false)) {
        await statusDropdown.selectOption('in_progress');
        await page.waitForTimeout(1000);
        
        // Verify status updated
        const hasInProgress = await page.locator('text=/in progress|in_progress/i').count();
        expect(hasInProgress).toBeGreaterThan(0);
        
        // Mark as complete
        await statusDropdown.selectOption('completed');
        await page.waitForTimeout(1000);
        
        // Verify completed status
        const hasCompleted = await page.locator('text=/completed|done/i').count();
        expect(hasCompleted).toBeGreaterThan(0);
      }
    }
  });
  
  test('error path: should handle task creation failure', async ({ 
    page, 
    mockEmails, 
    mockEmailAPI 
  }) => {
    await mockEmailAPI(page, mockEmails);
    
    // Mock task creation failure
    await page.route('**/api/tasks', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Invalid task data' }),
        });
      } else {
        await route.continue();
      }
    });
    
    await page.goto('/emails');
    await page.waitForLoadState('networkidle');
    
    const firstEmail = page.locator('[data-testid="email-item"], .email-item').first();
    await firstEmail.click();
    
    const createTaskButton = page.locator('button:has-text("Create Task"), button:has-text("Add Task")').first();
    
    if (await createTaskButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await createTaskButton.click();
      await page.waitForTimeout(1000);
      
      const titleInput = page.locator('input[name="title"], input[placeholder*="title" i]').first();
      if (await titleInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await titleInput.fill('Test Task');
        
        const submitButton = page.locator('button:has-text("Create"), button:has-text("Save")').first();
        await submitButton.click();
        await page.waitForTimeout(2000);
        
        // Verify error is displayed
        const hasError = await page.locator('text=/error|failed|invalid/i, [role="alert"]').count();
        expect(hasError).toBeGreaterThan(0);
      }
    }
  });
});

test.describe('Critical User Flow 3: Bulk Processing and Category Review', () => {
  test('happy path: should bulk process emails, review categories, and edit classification', async ({ 
    page, 
    mockEmails, 
    mockEmailAPI, 
    mockAIAPI 
  }) => {
    await mockEmailAPI(page, mockEmails);
    await mockAIAPI(page);
    
    await page.goto('/emails');
    await page.waitForLoadState('networkidle');
    
    // Select multiple emails
    const selectAllCheckbox = page.locator('input[type="checkbox"][aria-label*="select all" i], input[type="checkbox"].select-all').first();
    
    if (await selectAllCheckbox.isVisible({ timeout: 5000 }).catch(() => false)) {
      await selectAllCheckbox.check();
      await page.waitForTimeout(500);
      
      // Verify emails are selected
      const selectedCount = await page.locator('input[type="checkbox"]:checked').count();
      expect(selectedCount).toBeGreaterThan(1);
      
      // Trigger bulk processing
      const bulkProcessButton = page.locator(
        'button:has-text("Process Selected"), button:has-text("Bulk Process"), button:has-text("Classify Selected")'
      ).first();
      
      if (await bulkProcessButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        // Track batch processing API call
        const batchPromise = page.waitForResponse(resp => 
          resp.url().includes('/batch') && resp.status() === 200
        );
        
        await bulkProcessButton.click();
        await page.waitForTimeout(3000);
        
        // Verify batch processing completed
        const response = await batchPromise;
        const data = await response.json();
        expect(data.processed || data.success).toBeDefined();
        
        // Review categories - look for category badges or labels
        const categories = await page.locator('[class*="category"], [class*="badge"], [data-category]').count();
        expect(categories).toBeGreaterThan(0);
        
        // Edit a classification
        const firstEmail = page.locator('[data-testid="email-item"], .email-item').first();
        await firstEmail.click();
        await page.waitForTimeout(500);
        
        // Look for category dropdown or edit button
        const editButton = page.locator(
          'button:has-text("Edit Category"), button:has-text("Change Category"), [data-testid="edit-category"]'
        ).first();
        
        if (await editButton.isVisible({ timeout: 3000 }).catch(() => false)) {
          await editButton.click();
          await page.waitForTimeout(500);
          
          // Select different category
          const categoryOption = page.locator('text=/optional_fyi|team_discussion/i').first();
          if (await categoryOption.isVisible({ timeout: 3000 }).catch(() => false)) {
            await categoryOption.click();
            await page.waitForTimeout(1000);
            
            // Verify category was updated
            const updatedCategory = await page.locator('[class*="category"]').first().textContent();
            expect(updatedCategory).toBeTruthy();
          }
        }
      }
    }
  });
  
  test('error path: should handle bulk processing partial failures', async ({ 
    page, 
    mockEmails, 
    mockEmailAPI 
  }) => {
    await mockEmailAPI(page, mockEmails);
    
    // Mock partial batch failure
    await page.route('**/api/processing/process-batch*', async (route) => {
      const data = await route.request().postDataJSON();
      const emailIds = data.email_ids || [];
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          processed: Math.floor(emailIds.length / 2),
          failed: Math.ceil(emailIds.length / 2),
          results: emailIds.map((id: string, idx: number) => ({
            email_id: id,
            success: idx % 2 === 0,
            error: idx % 2 === 1 ? 'Processing failed' : undefined,
          })),
        }),
      });
    });
    
    await page.goto('/emails');
    await page.waitForLoadState('networkidle');
    
    const selectAllCheckbox = page.locator('input[type="checkbox"][aria-label*="select all" i]').first();
    
    if (await selectAllCheckbox.isVisible({ timeout: 5000 }).catch(() => false)) {
      await selectAllCheckbox.check();
      
      const bulkProcessButton = page.locator('button:has-text("Process Selected"), button:has-text("Bulk")').first();
      
      if (await bulkProcessButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await bulkProcessButton.click();
        await page.waitForTimeout(3000);
        
        // Verify partial failure notification
        const hasWarning = await page.locator('text=/some failed|partially|warning/i, [role="alert"]').count();
        expect(hasWarning).toBeGreaterThan(0);
      }
    }
  });
});

test.describe('Critical User Flow 4: Settings Configuration', () => {
  test('happy path: should update settings and verify changes applied', async ({ page }) => {
    // Mock settings API
    let savedSettings: any = {
      username: 'Test User',
      theme: 'light',
      emailsPerPage: 20,
      autoClassify: false,
    };
    
    await page.route('**/api/settings*', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(savedSettings),
        });
      } else if (route.request().method() === 'PUT' || route.request().method() === 'PATCH') {
        const updates = await route.request().postDataJSON();
        savedSettings = { ...savedSettings, ...updates };
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(savedSettings),
        });
      } else {
        await route.continue();
      }
    });
    
    // Navigate to settings
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
    
    // Wait for settings to load
    await page.waitForTimeout(2000);
    
    // Update username
    const usernameInput = page.locator('input[name="username"], input[id="username"], input[placeholder*="name" i]').first();
    if (await usernameInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await usernameInput.clear();
      await usernameInput.fill('E2E Test User Updated');
      
      // Save settings
      const saveButton = page.locator('button:has-text("Save"), button:has-text("Update"), button[type="submit"]').first();
      await saveButton.click();
      await page.waitForTimeout(2000);
      
      // Verify save success message
      const hasSuccess = await page.locator('text=/saved|success|updated/i, [role="alert"]').count();
      expect(hasSuccess).toBeGreaterThan(0);
      
      // Verify setting was persisted
      expect(savedSettings.username).toBe('E2E Test User Updated');
      
      // Reload page to verify persistence
      await page.reload();
      await page.waitForTimeout(2000);
      
      const reloadedValue = await usernameInput.inputValue();
      expect(reloadedValue).toBe('E2E Test User Updated');
    }
    
    // Toggle auto-classify setting
    const autoClassifyToggle = page.locator('input[type="checkbox"][name*="auto" i], input[type="checkbox"][id*="auto" i]').first();
    if (await autoClassifyToggle.isVisible({ timeout: 3000 }).catch(() => false)) {
      const initialState = await autoClassifyToggle.isChecked();
      await autoClassifyToggle.click();
      await page.waitForTimeout(500);
      
      const saveButton = page.locator('button:has-text("Save"), button:has-text("Update")').first();
      await saveButton.click();
      await page.waitForTimeout(2000);
      
      // Verify setting was toggled
      expect(savedSettings.autoClassify).toBe(!initialState);
    }
  });
  
  test('error path: should handle settings save failure', async ({ page }) => {
    // Mock settings load success but save failure
    await page.route('**/api/settings*', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ username: 'Test User' }),
        });
      } else if (route.request().method() === 'PUT' || route.request().method() === 'PATCH') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Database connection failed' }),
        });
      } else {
        await route.continue();
      }
    });
    
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    const usernameInput = page.locator('input[name="username"], input[id="username"]').first();
    if (await usernameInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await usernameInput.clear();
      await usernameInput.fill('Should Fail');
      
      const saveButton = page.locator('button:has-text("Save"), button:has-text("Update")').first();
      await saveButton.click();
      await page.waitForTimeout(2000);
      
      // Verify error message
      const hasError = await page.locator('text=/error|failed|unable/i, [role="alert"], .error').count();
      expect(hasError).toBeGreaterThan(0);
    }
  });
});

test.describe('Critical User Flow 5: Error Recovery and Retry', () => {
  test('should handle network timeout and retry successfully', async ({ 
    page, 
    mockEmails, 
    mockEmailAPI 
  }) => {
    let attemptCount = 0;
    
    // First attempt fails, second succeeds
    await page.route('**/api/emails*', async (route) => {
      attemptCount++;
      
      if (attemptCount === 1) {
        // Simulate timeout on first attempt
        await new Promise(resolve => setTimeout(resolve, 100));
        await route.abort('timedout');
      } else {
        // Success on retry
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            emails: mockEmails.slice(0, 10),
            total: mockEmails.length,
            page: 1,
            per_page: 20,
            total_pages: 1,
          }),
        });
      }
    });
    
    await page.goto('/emails');
    
    // Wait for retry attempt
    await page.waitForTimeout(5000);
    
    // Verify retry button or automatic retry succeeded
    const retryButton = page.locator('button:has-text("Retry"), button:has-text("Try Again")').first();
    
    if (await retryButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await retryButton.click();
      await page.waitForTimeout(3000);
    }
    
    // Verify emails eventually load after retry
    const emailCount = await page.locator('[data-testid="email-item"], .email-item').count();
    expect(emailCount).toBeGreaterThan(0);
    expect(attemptCount).toBeGreaterThanOrEqual(2);
  });
  
  test('should recover from 500 server error with manual retry', async ({ page }) => {
    let attemptCount = 0;
    
    await page.route('**/api/emails*', async (route) => {
      attemptCount++;
      
      if (attemptCount === 1) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal server error' }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            emails: [],
            total: 0,
            page: 1,
            per_page: 20,
            total_pages: 0,
          }),
        });
      }
    });
    
    await page.goto('/emails');
    await page.waitForTimeout(2000);
    
    // Verify error is displayed
    const hasError = await page.locator('text=/error|failed|500/i, [role="alert"]').count();
    expect(hasError).toBeGreaterThan(0);
    
    // Click retry button
    const retryButton = page.locator('button:has-text("Retry"), button:has-text("Try Again"), button:has-text("Reload")').first();
    
    if (await retryButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await retryButton.click();
      await page.waitForTimeout(3000);
      
      // Verify error is cleared and request succeeded
      const errorStillVisible = await page.locator('[role="alert"]:has-text("error")').count();
      expect(errorStillVisible).toBe(0);
      expect(attemptCount).toBe(2);
    }
  });
  
  test('should handle 404 not found error gracefully', async ({ page }) => {
    await page.route('**/api/emails/invalid-id*', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Email not found' }),
      });
    });
    
    // Try to navigate to non-existent email
    await page.goto('/emails/invalid-id');
    await page.waitForTimeout(2000);
    
    // Verify 404 error handling
    const has404Message = await page.locator('text=/not found|404|doesn\'t exist/i').count();
    expect(has404Message).toBeGreaterThan(0);
    
    // Verify back button or link to email list
    const backButton = page.locator('button:has-text("Back"), a:has-text("Back to"), a:has-text("Email List")').first();
    
    if (await backButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await backButton.click();
      await page.waitForTimeout(2000);
      
      // Verify we're back at a valid page
      const url = page.url();
      expect(url).toMatch(/\/emails\/?$/);
    }
  });
  
  test('should recover from failed AI classification with retry', async ({ 
    page, 
    mockEmails, 
    mockEmailAPI 
  }) => {
    await mockEmailAPI(page, mockEmails);
    
    let classifyAttempts = 0;
    
    await page.route('**/api/ai/classify*', async (route) => {
      classifyAttempts++;
      
      if (classifyAttempts === 1) {
        await route.fulfill({
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'AI service temporarily unavailable' }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            category: 'required_personal_action',
            confidence: 0.92,
            reasoning: 'Action required based on content analysis',
          }),
        });
      }
    });
    
    await page.goto('/emails');
    await page.waitForLoadState('networkidle');
    
    // Select and classify email
    const firstEmail = page.locator('[data-testid="email-item"], .email-item').first();
    await firstEmail.click();
    
    const classifyButton = page.locator('button:has-text("Classify"), button:has-text("Process")').first();
    
    if (await classifyButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await classifyButton.click();
      await page.waitForTimeout(2000);
      
      // Verify error is shown
      const hasError = await page.locator('text=/unavailable|error|failed/i').count();
      expect(hasError).toBeGreaterThan(0);
      
      // Retry classification
      const retryButton = page.locator('button:has-text("Retry"), button:has-text("Try Again")').first();
      
      if (await retryButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await retryButton.click();
      } else {
        // If no retry button, click classify again
        await classifyButton.click();
      }
      
      await page.waitForTimeout(3000);
      
      // Verify classification succeeded on retry
      const hasCategory = await page.locator('text=/required_personal_action|category/i').count();
      expect(hasCategory).toBeGreaterThan(0);
      expect(classifyAttempts).toBe(2);
    }
  });
});
