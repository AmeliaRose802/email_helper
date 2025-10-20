const { _electron: electron } = require('@playwright/test');
const path = require('path');

(async () => {
  console.log('Launching Electron...');
  
  const electronPath = path.join(__dirname, '..', 'electron');
  const app = await electron.launch({
    args: [path.join(electronPath, 'main.js')],
    cwd: electronPath,
    timeout: 30000,
  });

  console.log('Electron launched, waiting for window...');
  const page = await app.firstWindow({ timeout: 30000 });
  console.log('Window found!');

  // Listen to console messages
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    console.log(`[Browser ${type.toUpperCase()}] ${text}`);
  });

  // Wait and check
  await page.waitForLoadState('domcontentloaded', { timeout: 30000 });
  console.log('DOM loaded');

  // Get page title and HTML
  const title = await page.title();
  const html = await page.content();
  
  console.log('\n=== PAGE INFO ===');
  console.log('Title:', title);
  console.log('URL:', page.url());
  console.log('HTML length:', html.length);
  console.log('\n=== ROOT DIV ===');
  
  const rootHTML = await page.$eval('#root', el => el.innerHTML).catch(() => 'NOT FOUND');
  console.log(rootHTML.substring(0, 500));

  // Screenshot
  await page.screenshot({ path: 'electron-screenshot.png' });
  console.log('\nScreenshot saved to electron-screenshot.png');

  // Wait a bit
  await page.waitForTimeout(5000);

  await app.close();
  console.log('Test complete');
})();
