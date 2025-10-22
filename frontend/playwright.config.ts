import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Test Configuration
 * Optimized for Windows localhost development environment
 * 
 * See https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // Test directory
  testDir: './tests/e2e',
  
  // Maximum time one test can run
  timeout: 60 * 1000,
  
  // Test execution settings
  fullyParallel: false, // Run tests sequentially for COM backend stability
  forbidOnly: !!process.env.CI, // Fail on test.only in CI
  retries: process.env.CI ? 2 : 1, // Retry on CI, once locally
  workers: 1, // Single worker for COM backend (not thread-safe)
  
  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
    ['json', { outputFile: 'playwright-report/results.json' }],
  ],
  
  // Shared settings for all projects
  use: {
    // Base URL for navigation - Vite dev server runs on port 5173
    baseURL: 'http://localhost:5173',
    
    // Collect trace on failure for debugging
    trace: 'on-first-retry',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
    
    // Timeouts
    actionTimeout: 15000,
    navigationTimeout: 30000,
    
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
        // Viewport for typical Windows desktop
        viewport: { width: 1920, height: 1080 },
      },
    },
    
    // Optional: Firefox for cross-browser testing
    // Uncomment if needed for full coverage
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },

    // Optional: Microsoft Edge
    // {
    //   name: 'Microsoft Edge',
    //   use: { ...devices['Desktop Edge'], channel: 'msedge' },
    // },
  ],

  // Web server configuration - DISABLED since dev server is already running
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:5173',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120 * 1000, // 2 minutes to start
  //   stdout: 'ignore',
  //   stderr: 'pipe',
  // },

  // Global setup/teardown
  // globalSetup: require.resolve('./tests/e2e/global-setup.ts'),
  // globalTeardown: require.resolve('./tests/e2e/global-teardown.ts'),
});
