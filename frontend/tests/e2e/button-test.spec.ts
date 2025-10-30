import { test, expect } from "@playwright/test";

test.describe("Email Helper Button Tests", () => {
  test("should have clickable buttons", async ({ page }) => {
    await page.goto("http://localhost:5173");
    await page.waitForSelector("[data-testid=\"process-emails-button\"]");
    
    const processButton = page.getByTestId("process-emails-button");
    await expect(processButton).toBeVisible();
    await expect(processButton).toBeEnabled();
    
    page.on("dialog", dialog => dialog.accept());
    await processButton.click();
  });
});
