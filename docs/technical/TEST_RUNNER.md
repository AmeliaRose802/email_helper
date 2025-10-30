# Test Runner Documentation

## Running All Tests

This project includes a comprehensive test runner that executes all test suites across the entire codebase.

### Quick Start

**Run all tests:**
```powershell
npm test
# OR
.\run-all-tests.ps1
```

### Test Suites Included

The test runner executes four test suites in sequence:

1. **Backend Tests** - Python tests for `backend/` using pytest
2. **Src Tests** - Python tests for `test/` (legacy desktop app) using pytest
3. **Frontend Unit Tests** - React component tests using vitest
4. **Frontend E2E Tests** - End-to-end tests using Playwright

### Command Options

```powershell
# Run all tests
.\run-all-tests.ps1

# Run with coverage reports
.\run-all-tests.ps1 -Coverage

# Run with verbose output
.\run-all-tests.ps1 -Verbose

# Skip specific test suites
.\run-all-tests.ps1 -SkipBackend
.\run-all-tests.ps1 -SkipSrc
.\run-all-tests.ps1 -SkipFrontend
.\run-all-tests.ps1 -SkipE2E

# Combine options
.\run-all-tests.ps1 -Coverage -SkipE2E -Verbose
```

### NPM Scripts

You can also use npm scripts to run specific test suites:

```bash
# Run all tests
npm test

# Run all tests with coverage
npm run test:coverage

# Run individual test suites
npm run test:backend          # Backend Python tests
npm run test:src              # Src Python tests
npm run test:frontend         # Frontend unit tests
npm run test:e2e              # Frontend E2E tests
```

### Coverage Reports

When running with `-Coverage` flag:
- Backend coverage: `runtime_data/coverage/backend/index.html`
- Src coverage: `runtime_data/coverage/src/index.html`
- Frontend coverage: `frontend/coverage/index.html`

### Exit Codes

- `0` - All tests passed
- `1` - One or more test suites failed

### Output Format

The test runner provides:
- Color-coded output (Green = Pass, Red = Fail, Yellow = Info)
- Summary table showing pass/fail status for each suite
- Total test execution duration
- Individual test suite output for debugging

### Prerequisites

Ensure you have installed all dependencies:
```bash
npm run setup           # Install all dependencies
pip install -r requirements.txt
```

### Troubleshooting

**Tests fail to run:**
- Ensure all dependencies are installed
- Check that Python and Node.js are in your PATH
- Verify pytest is installed: `python -m pytest --version`

**E2E tests fail:**
- Install Playwright browsers: `cd frontend && npx playwright install`
- Ensure the backend server is not running (tests will start their own instance)

**Coverage reports not generated:**
- Ensure coverage tools are installed: `pip install pytest-cov`
- Check `runtime_data/coverage/` directory permissions

### CI/CD Integration

This test runner is designed for both local development and CI/CD pipelines. The exit code makes it suitable for automated testing workflows.

Example GitHub Actions usage:
```yaml
- name: Run all tests
  run: npm test
```
