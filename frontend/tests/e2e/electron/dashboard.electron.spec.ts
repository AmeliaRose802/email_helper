/**
 * Electron Dashboard Tests
 * Tests button clicks, navigation, and core functionality in the Electron app
 */
import { test, expect, _electron as electron, ElectronApplication, Page } from '@playwright/test';
import * as path from 'path';
import { existsSync } from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let electronApp: ElectronApplication;
let page: Page;

test.beforeAll(async () => {
  // Kill any existing processes
  try {
    await import('child_process').then(cp => {
      cp.execSync('Get-Process -Name electron,python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue', { shell: 'pwsh.exe', stdio: 'ignore' });
    });
  } catch (e) {
    // Ignore errors
  }

  // Wait for cleanup
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Launch Electron
  const electronPath = path.join(__dirname, '../../../..', 'electron');
  const electronExecutable = path.join(
    electronPath,
    'node_modules',
    '.bin',
    process.platform === 'win32' ? 'electron.cmd' : 'electron',
  );

  if (!existsSync(electronExecutable)) {
    throw new Error(`Electron executable not found at ${electronExecutable}`);
  }

  electronApp = await electron.launch({
    executablePath: electronExecutable,
    args: [path.join(electronPath, 'main.js')],
    cwd: electronPath,
    timeout: 45000,
  });

  // Wait for window
  page = await electronApp.firstWindow({ timeout: 30000 });
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  
  // Give extra time for backend to start
  await page.waitForTimeout(5000);
});

test.afterAll(async () => {
  if (electronApp) {
    await electronApp.close();
  }
  
  // Cleanup processes
  try {
    await import('child_process').then(cp => {
      cp.execSync('Get-Process -Name electron,python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue', { shell: 'pwsh.exe', stdio: 'ignore' });
    });
  } catch (e) {
    // Ignore errors
  }
});

test.describe('Dashboard Functionality', () => {
  test('should load dashboard page', async () => {
    await expect(page.locator('h1')).toContainText('Dashboard', { timeout: 10000 });
  });

  test('should display stat cards', async () => {
    const statCards = page.locator('.stat-card');
    await expect(statCards).toHaveCount(2, { timeout: 10000 });
  });

  test('should display quick action buttons', async () => {
    const quickActions = page.locator('.quick-actions');
    await expect(quickActions).toBeVisible({ timeout: 10000 });
    
    const buttons = page.locator('.quick-actions button');
    await expect(buttons).toHaveCount(3);
  });

  test('Process Emails button should be clickable', async () => {
    const processButton = page.locator('button:has-text(\"Process New Emails\")');
    
    // Check visibility and enabled state
    await expect(processButton).toBeVisible({ timeout: 10000 });
    await expect(processButton).toBeEnabled();
    
    // Get computed style to verify clickability
    const computedStyle = await processButton.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return {
        pointerEvents: style.pointerEvents,
        cursor: style.cursor,
        zIndex: style.zIndex,
      };
    });
    
    console.log('Process button style:', computedStyle);
    expect(computedStyle.cursor).toContain('pointer');
    
    // Try to click
    let dialogShown = false;
    page.once('dialog', async dialog => {
      dialogShown = true;
      console.log('Dialog message:', dialog.message());
      expect(dialog.message()).toContain('Processing emails');
      await dialog.accept();
    });
    
    await processButton.click({ timeout: 5000 });
    
    // Wait a bit for dialog
    await page.waitForTimeout(1000);
    expect(dialogShown).toBe(true);
  });

  test('View Tasks button should navigate', async () => {
    const viewTasksButton = page.locator('button:has-text(\"View Pending Tasks\")');
    
    await expect(viewTasksButton).toBeVisible({ timeout: 10000 });
    await expect(viewTasksButton).toBeEnabled();
    
    await viewTasksButton.click({ timeout: 5000 });
    
    // Should navigate to tasks page
    await expect(page).toHaveURL(/.*tasks/, { timeout: 10000 });
    
    // Navigate back
    await page.goBack();
    await page.waitForLoadState('domcontentloaded');
  });

  test('Generate Summary button should be clickable', async () => {
    const summaryButton = page.locator('button:has-text(\"Generate Summary\")');
    
    await expect(summaryButton).toBeVisible({ timeout: 10000 });
    await expect(summaryButton).toBeEnabled();
    
    let dialogShown = false;
    page.once('dialog', async dialog => {
      dialogShown = true;
      console.log('Dialog message:', dialog.message());
      expect(dialog.message()).toContain('Generating summary');
      await dialog.accept();
    });
    
    await summaryButton.click({ timeout: 5000 });
    
    await page.waitForTimeout(1000);
    expect(dialogShown).toBe(true);
  });

  test('Backend API should be accessible', async () => {
    // Test if backend is responding
    const response = await page.evaluate(async () => {
      try {
        const res = await fetch('http://localhost:8000/health');
        return {
          ok: res.ok,
          status: res.status,
          data: await res.json(),
        };
      } catch (error) {
        return {
          ok: false,
          error: String(error),
        };
      }
    });
    
    console.log('Backend health check:', response);
    expect(response.ok).toBe(true);
  });
});
