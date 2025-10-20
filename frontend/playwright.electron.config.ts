import { defineConfig, devices } from '@playwright/test';
import * as path from 'path';

/**
 * Playwright Configuration for Electron App Testing
 * Tests the actual Electron desktop application
 */
export default defineConfig({
  testDir: './tests/e2e/electron',
  timeout: 60000,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 1,
  workers: 1,
  
  reporter: [
    ['html', { outputFolder: 'playwright-report-electron' }],
    ['list'],
  ],
  
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'electron',
      testMatch: '*.electron.spec.ts',
    },
  ],
});
