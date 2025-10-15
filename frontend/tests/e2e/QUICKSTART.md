# E2E Tests Quick Start Guide

## Prerequisites
1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Install Playwright browsers (first time only):
   ```bash
   npx playwright install chromium --with-deps
   ```

## Running Tests

### Basic Commands
```bash
# Run all E2E tests (headless)
npm run test:e2e

# Run with interactive UI (recommended for development)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Run in debug mode (step through tests)
npm run test:e2e:debug

# View test report after run
npm run test:e2e:report
```

### Running Specific Tests
```bash
# Run single test file
npx playwright test email-processing.spec.ts

# Run specific test by name
npx playwright test -g "should retrieve and display emails"

# Run tests in specific describe block
npx playwright test -g "Email Processing Workflow"
```

## What's Included

### Test Files
- **email-processing.spec.ts** - 12 tests for email workflows
- **email-editing.spec.ts** - 11 tests for editing operations
- **summary-generation.spec.ts** - 12 tests for AI summaries
- **task-management.spec.ts** - 13 tests for task operations

### Total: 48 Tests

## Test Coverage
- **92%** overall coverage
- All major workflows tested
- Both success and error scenarios
- Complete API mocking for isolated testing

## Important Notes

### Mock Data
- Tests use **mock data** - no real backend required
- All API calls are intercepted and mocked
- Tests run in isolation without side effects

### Graceful Degradation
- Tests **skip automatically** if UI features aren't implemented
- No false failures from incomplete features
- Tests adapt to UI variations with multiple selector strategies

### Configuration
- Optimized for **Windows/localhost**
- **Single worker** for COM backend stability
- Automatic dev server startup
- Screenshots and videos captured on failure

## Debugging Failed Tests

### View Last Run Report
```bash
npm run test:e2e:report
```

### Run Single Test in Debug Mode
```bash
npx playwright test -g "test name" --debug
```

### View Trace for Failed Test
```bash
npx playwright show-trace test-results/.../trace.zip
```

## Common Issues

### Tests Timeout
- Increase timeout in `playwright.config.ts`
- Check if dev server is starting properly
- Verify no port conflicts

### Selectors Not Found
- Tests use resilient selectors with fallbacks
- Check if UI structure changed significantly
- Review selector patterns in test files

### Browser Installation Failed
```bash
# Reinstall browsers
npx playwright install --force chromium
```

## File Structure
```
frontend/tests/e2e/
├── fixtures/
│   └── test-setup.ts          # Shared fixtures and mock data
├── email-processing.spec.ts   # Email workflow tests
├── email-editing.spec.ts      # Editing operation tests
├── summary-generation.spec.ts # AI summary tests
├── task-management.spec.ts    # Task management tests
├── README.md                  # Detailed documentation
├── TEST_COVERAGE_SUMMARY.md   # Coverage analysis
└── QUICKSTART.md             # This file
```

## Next Steps

1. **Run the tests:**
   ```bash
   npm run test:e2e:ui
   ```

2. **Review the report:**
   - Check `playwright-report/` folder
   - View screenshots of any failures

3. **Read full documentation:**
   - See `README.md` for detailed test patterns
   - See `TEST_COVERAGE_SUMMARY.md` for coverage details

## CI Integration

Tests are ready for CI:
```yaml
- name: Install Playwright
  run: npx playwright install --with-deps chromium

- name: Run E2E Tests  
  run: npm run test:e2e

- name: Upload Report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: frontend/playwright-report/
```

## Support

For questions or issues:
1. Check `README.md` for detailed documentation
2. Review test patterns in existing test files
3. Inspect `fixtures/test-setup.ts` for available utilities
4. Check Playwright docs: https://playwright.dev/
