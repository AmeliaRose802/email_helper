/**
 * Diagnostic test to investigate data-testid attributes in DOM
 */
import { test, expect } from './fixtures/test-setup';

test.describe('Diagnostic: data-testid attributes', () => {
  test.beforeEach(async ({ page, mockTasks, mockTaskAPI, mockEmails, mockEmailAPI }) => {
    await mockTaskAPI(page, mockTasks);
    await mockEmailAPI(page, mockEmails);
    await page.goto('/#/tasks');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Give React time to render
  });

  test('should check if data-testid exists in HTML', async ({ page }) => {
    // Get the HTML of the entire page
    const html = await page.content();
    
    // Check if data-testid="task-card" appears in the HTML
    const hasTestId = html.includes('data-testid="task-card"');
    console.log('[Diagnostic] data-testid="task-card" in HTML:', hasTestId);
    
    // Print a snippet of HTML around task elements
    const taskSection = html.match(/class="simple-task-item[^>]*>[\s\S]{0,500}/g);
    if (taskSection) {
      console.log('[Diagnostic] Task item HTML sample:', taskSection[0]);
    }
    
    // Try different selectors
    const byTestId = await page.locator('[data-testid="task-card"]').count();
    const byClass = await page.locator('.simple-task-item').count();
    const byCheckbox = await page.locator('input[type="checkbox"]').count();
    
    console.log('[Diagnostic] Selector counts:');
    console.log('  - [data-testid="task-card"]:', byTestId);
    console.log('  - .simple-task-item:', byClass);
    console.log('  - input[type="checkbox"]:', byCheckbox);
    
    // Get all elements with data-testid
    const allTestIds = await page.locator('[data-testid]').all();
    console.log('[Diagnostic] Total elements with data-testid:', allTestIds.length);
    
    for (const el of allTestIds) {
      const testId = await el.getAttribute('data-testid');
      console.log('[Diagnostic]   - Found data-testid:', testId);
    }
    
    // This test always passes - it's just for diagnostic output
    expect(true).toBe(true);
  });
});
