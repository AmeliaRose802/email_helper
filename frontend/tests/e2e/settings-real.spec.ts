/**
 * REAL Settings Tests - NO MOCKS, REAL DATABASE OPERATIONS
 * These tests interact with the actual backend API and database
 */

import { test, expect } from '@playwright/test';

test.describe('Real Settings E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/settings');
    await page.waitForSelector('h1, h2', { timeout: 15000 });
  });

  test('should load and save username to real database', async ({ page }) => {
    const testUsername = `E2E_${Date.now()}`;
    
    await page.waitForTimeout(2000);
    const field = page.locator('input').first();
    await field.clear();
    await field.fill(testUsername);
    
    await page.locator('button').first().click();
    await page.waitForTimeout(3000);
    
    await page.reload();
    await page.waitForTimeout(2000);
    
    const saved = await page.locator('input').first().inputValue();
    expect(saved).toBe(testUsername);
    console.log('✅ Real database save verified:', testUsername);
  });
});
