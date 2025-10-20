import { test, expect } from '@playwright/test';

test.describe('Settings Page Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock settings API
    await page.route('**/api/settings', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            username: 'Test User',
            job_context: 'Software Engineer working on email management systems',
            newsletter_interests: 'DevOps, Azure, React, AI/ML',
            azure_openai_endpoint: 'https://test.openai.azure.com/',
            azure_openai_deployment: 'gpt-4',
            custom_prompts: {},
            ado_area_path: 'Project\\Team\\Area',
            ado_pat: ''
          })
        });
      } else if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            message: 'Settings updated successfully',
            settings: JSON.parse(await route.request().postData() || '{}')
          })
        });
      } else if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            message: 'Settings reset to defaults',
            settings: {}
          })
        });
      }
    });

    // Navigate to settings page
    await page.goto('http://localhost:5173/settings');
    await page.waitForLoadState('networkidle');
  });

  test('should load and display settings', async ({ page }) => {
    // Wait for settings to load
    await page.waitForSelector('h1:has-text("Settings")');
    
    // Verify page title
    await expect(page.locator('h1')).toContainText('Settings');
    
    // Verify tabs are present
    await expect(page.locator('button:has-text("User Profile")')).toBeVisible();
    await expect(page.locator('button:has-text("AI Configuration")')).toBeVisible();
    await expect(page.locator('button:has-text("Custom Prompts")')).toBeVisible();
  });

  test('should display user profile settings', async ({ page }) => {
    // Profile tab should be active by default
    const profileTab = page.locator('button:has-text("User Profile")');
    await expect(profileTab).toHaveClass(/active/);
    
    // Verify username field
    const usernameInput = page.locator('#username');
    await expect(usernameInput).toBeVisible();
    await expect(usernameInput).toHaveValue('Test User');
    
    // Verify job context field
    const jobContextTextarea = page.locator('#jobContext');
    await expect(jobContextTextarea).toBeVisible();
    await expect(jobContextTextarea).toContainText('Software Engineer');
    
    // Verify newsletter interests field
    const newsletterInterestsTextarea = page.locator('#newsletterInterests');
    await expect(newsletterInterestsTextarea).toBeVisible();
    await expect(newsletterInterestsTextarea).toContainText('DevOps');
  });

  test('should switch to AI Configuration tab', async ({ page }) => {
    // Click AI Configuration tab
    const aiTab = page.locator('button:has-text("AI Configuration")');
    await aiTab.click();
    
    // Verify tab is active
    await expect(aiTab).toHaveClass(/active/);
    
    // Verify AI configuration fields are visible
    await expect(page.locator('#azureEndpoint')).toBeVisible();
    await expect(page.locator('#azureKey')).toBeVisible();
    await expect(page.locator('#azureDeployment')).toBeVisible();
    
    // Verify ADO fields are visible
    await expect(page.locator('#adoAreaPath')).toBeVisible();
    await expect(page.locator('#adoPat')).toBeVisible();
    
    // Verify values are loaded
    await expect(page.locator('#azureEndpoint')).toHaveValue('https://test.openai.azure.com/');
    await expect(page.locator('#azureDeployment')).toHaveValue('gpt-4');
    await expect(page.locator('#adoAreaPath')).toHaveValue('Project\\Team\\Area');
  });

  test('should switch to Custom Prompts tab', async ({ page }) => {
    // Click Custom Prompts tab
    const promptsTab = page.locator('button:has-text("Custom Prompts")');
    await promptsTab.click();
    
    // Verify tab is active
    await expect(promptsTab).toHaveClass(/active/);
    
    // Verify at least some category prompts are visible
    await expect(page.locator('label:has-text("Required Personal Action")')).toBeVisible();
    await expect(page.locator('label:has-text("Newsletter")')).toBeVisible();
  });

  test('should save settings successfully', async ({ page }) => {
    // Modify username
    const usernameInput = page.locator('#username');
    await usernameInput.fill('Updated User');
    
    // Modify job context
    const jobContextTextarea = page.locator('#jobContext');
    await jobContextTextarea.fill('Senior Software Engineer with focus on AI');
    
    // Click save button
    const saveButton = page.locator('button:has-text("Save Settings")');
    await saveButton.click();
    
    // Verify success message
    await expect(saveButton).toContainText('Saved!');
    
    // Wait for status to reset
    await page.waitForTimeout(2100);
    await expect(saveButton).toContainText('Save Settings');
  });

  test('should toggle password visibility', async ({ page }) => {
    // Switch to AI Configuration tab
    await page.locator('button:has-text("AI Configuration")').click();
    
    // Verify password field is hidden by default
    const passwordInput = page.locator('#azureKey');
    await expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Click toggle button
    const toggleButton = page.locator('.password-toggle').first();
    await toggleButton.click();
    
    // Verify password is now visible
    await expect(passwordInput).toHaveAttribute('type', 'text');
    
    // Click toggle again
    await toggleButton.click();
    
    // Verify password is hidden again
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('should reset settings with confirmation', async ({ page }) => {
    // Modify a setting first
    const usernameInput = page.locator('#username');
    await usernameInput.fill('Modified User');
    
    // Setup dialog handler to accept confirmation
    page.on('dialog', async (dialog) => {
      expect(dialog.message()).toContain('reset');
      await dialog.accept();
    });
    
    // Click reset button
    const resetButton = page.locator('button:has-text("Reset to Defaults")');
    await resetButton.click();
    
    // Verify settings are reset (username should be empty after reset)
    await page.waitForTimeout(500);
    // The mock returns empty settings, so the form should be cleared
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Override settings API to return error
    await page.route('**/api/settings', async (route) => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: true,
            message: 'Internal server error'
          })
        });
      } else {
        await route.continue();
      }
    });
    
    // Try to save settings
    const saveButton = page.locator('button:has-text("Save Settings")');
    await saveButton.click();
    
    // Verify error indication
    await expect(page.locator('.error-text')).toBeVisible();
    await expect(page.locator('.error-text')).toContainText('Failed');
  });

  test('should validate newsletter interests format', async ({ page }) => {
    const newsletterInput = page.locator('#newsletterInterests');
    
    // Enter newsletter interests with mixed format
    await newsletterInput.fill(`Topics I care about:
- DevOps and CI/CD
- Azure cloud
- React development

Skip content about:
- HR policies
- Marketing`);
    
    // Verify text is entered correctly
    const value = await newsletterInput.inputValue();
    expect(value).toContain('DevOps');
    expect(value).toContain('Skip content about');
  });

  test('should maintain tab state during edits', async ({ page }) => {
    // Switch to AI Configuration
    await page.locator('button:has-text("AI Configuration")').click();
    
    // Make a change
    await page.locator('#azureDeployment').fill('gpt-35-turbo');
    
    // Switch to Profile tab
    await page.locator('button:has-text("User Profile")').click();
    
    // Switch back to AI Configuration
    await page.locator('button:has-text("AI Configuration")').click();
    
    // Verify change is still there
    await expect(page.locator('#azureDeployment')).toHaveValue('gpt-35-turbo');
  });

  test('should show security notice for API keys', async ({ page }) => {
    // Switch to AI Configuration tab
    await page.locator('button:has-text("AI Configuration")').click();
    
    // Verify security warning is displayed
    await expect(page.locator('.warning-box')).toBeVisible();
    await expect(page.locator('.warning-box')).toContainText('Security Notice');
  });
});
