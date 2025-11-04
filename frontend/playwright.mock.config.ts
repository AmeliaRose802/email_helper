import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Test Configuration - Mock API Mode
 * This configuration runs tests with mocked APIs (no real backend server)
 * 
 * Use this for fast, isolated component testing without backend dependencies
 */
export default defineConfig({
  // Test directory
  testDir: './tests/e2e',
  
  // Maximum time one test can run
  timeout: 30 * 1000, // Shorter timeout since no real backend
  
  // Test execution settings
  fullyParallel: true, // Can run in parallel since no real COM backend
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0, // No retries for mock tests
  workers: process.env.CI ? 2 : 4, // More workers for mock tests
  
  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report-mock' }],
    ['list'],
    ['json', { outputFile: 'playwright-report-mock/results.json' }],
  ],
  
  // Shared settings for all projects
  use: {
    // Base URL for navigation - Vite dev server runs on port 3001
    baseURL: 'http://localhost:3001',
    
    // Collect trace on failure for debugging
    trace: 'on-first-retry',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
    
    // Timeouts
    actionTimeout: 10000,
    navigationTimeout: 15000,
    
    // Locale
    locale: 'en-US',
    timezoneId: 'America/New_York',
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
      },
    },
  ],

  // Web server configuration - ONLY frontend, NO backend
  webServer: {
    // Frontend dev server only (Vite on port 3001)
    command: 'npm run dev',
    url: 'http://localhost:3001',
    reuseExistingServer: !process.env.CI,
    timeout: 60 * 1000,
    stdout: 'ignore',
    stderr: 'pipe',
  },
});
