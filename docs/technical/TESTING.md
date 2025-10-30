# Testing Guide

## Quick Start

Run all tests with a single command:

```bash
npm test
```

Or use the PowerShell script directly:

```powershell
.\run-all-tests.ps1
```

## Test Suites

This project has 4 test suites that run in sequence:

1. **Backend Tests** (`backend/tests/`) - FastAPI backend, API endpoints, services
2. **Src Tests** (`test/`) - Legacy desktop app modules, core functionality
3. **Frontend Unit Tests** (`frontend/tests/`) - React component tests with Vitest
4. **Frontend E2E Tests** (`frontend/tests/e2e/`) - End-to-end workflows with Playwright

## NPM Scripts

```bash
# Run all tests
npm test

# Run all tests with coverage
npm run test:coverage

# Run individual test suites
npm run test:backend          # Backend Python tests (pytest)
npm run test:src              # Src Python tests (pytest)
npm run test:frontend         # Frontend unit tests (vitest)
npm run test:e2e              # Frontend E2E tests (Playwright)
```

## PowerShell Test Runner Options

```powershell
# Run all tests
.\run-all-tests.ps1

# Run with coverage reports
.\run-all-tests.ps1 -Coverage

# Run with verbose output
.\run-all-tests.ps1 -Verbose

# Skip specific test suites (for faster development)
.\run-all-tests.ps1 -SkipE2E
.\run-all-tests.ps1 -SkipBackend
.\run-all-tests.ps1 -SkipFrontend
.\run-all-tests.ps1 -SkipSrc

# Combine options
.\run-all-tests.ps1 -Coverage -SkipE2E -Verbose
```

## Coverage Reports

When running with `-Coverage` flag, HTML reports are generated at:

- **Backend coverage:** `runtime_data/coverage/backend/index.html`
- **Src coverage:** `runtime_data/coverage/src/index.html`
- **Frontend coverage:** `frontend/coverage/index.html`

Open these files in a browser to view detailed coverage information.

## Exit Codes

- **0** - All tests passed ✅
- **1** - One or more test suites failed ❌

This makes the test runner suitable for CI/CD pipelines and automated workflows.

## Prerequisites

### Install Dependencies

```bash
# Install all dependencies
npm run setup

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (for E2E tests)
cd frontend && npx playwright install
```

### Verify Installation

```bash
# Check pytest is available
python -m pytest --version

# Check Node.js tools are available
npm --version
cd frontend && npm --version
```

## Development Workflow

### Before Starting Work

```bash
# Run tests to ensure everything works
npm test
```

### During Development

```bash
# Run specific test suite you're working on
npm run test:backend    # If working on backend
npm run test:frontend   # If working on frontend
npm run test:src        # If working on src modules

# Skip slow E2E tests during rapid development
.\run-all-tests.ps1 -SkipE2E
```

### Before Committing

```bash
# ALWAYS run full test suite
npm test

# Fix any failing tests immediately
# File bugs with Beads if tests reveal issues:
# bd create "Bug: <description>" -t bug -p 1
```

## Troubleshooting

### Tests Won't Run

**Check dependencies are installed:**
```bash
npm run setup
pip install -r requirements.txt
```

**Verify pytest is available:**
```bash
python -m pytest --version
```

**Check Node.js and npm are in PATH:**
```bash
node --version
npm --version
```

### E2E Tests Fail

**Install Playwright browsers:**
```bash
cd frontend
npx playwright install
```

**Ensure backend server is not already running:**
- E2E tests start their own backend instance
- Stop any running instances of the app before running E2E tests

### Coverage Reports Not Generated

**Ensure coverage tools are installed:**
```bash
pip install pytest-cov
cd frontend && npm install
```

**Check directory permissions:**
- Ensure `runtime_data/coverage/` directory is writable

### PowerShell Script Won't Run

**Check execution policy:**
```powershell
Get-ExecutionPolicy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Run from project root:**
```powershell
cd c:\Users\ameliapayne\email_helper
.\run-all-tests.ps1
```

## CI/CD Integration

The test runner is designed for both local development and CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run all tests
  run: npm test

- name: Run tests with coverage
  run: npm run test:coverage

- name: Upload coverage reports
  uses: actions/upload-artifact@v3
  with:
    name: coverage-reports
    path: |
      runtime_data/coverage/
      frontend/coverage/
```

## Output Format

The test runner provides:

- **Color-coded output** (Green = Pass, Red = Fail, Yellow = Info)
- **Summary table** showing pass/fail status for each suite
- **Total test execution duration**
- **Individual test suite output** for debugging failures
- **Clear exit codes** for automation

Example output:

```
========================================
Running Backend Tests (pytest backend/tests/)
========================================

[pytest output...]

========================================
Running Src Tests (pytest test/)
========================================

[pytest output...]

========================================
Running Frontend Unit Tests (vitest)
========================================

[vitest output...]

========================================
Running Frontend E2E Tests (Playwright)
========================================

[playwright output...]

========================================
Test Results Summary
========================================

✓ BackendTests : PASSED
✓ SrcTests : PASSED
✓ FrontendUnitTests : PASSED
✓ FrontendE2ETests : PASSED

Total Duration: 05:23

All test suites passed! ✨
```

## More Information

For detailed documentation, see:
- `TEST_RUNNER_README.md` - Comprehensive test runner documentation
- `backend/tests/README.md` - Backend testing guide
- `frontend/tests/e2e/README.md` - E2E testing guide
- `test/README_REGRESSION_TESTS.md` - Regression testing guide

## Quick Reference

| Command | Description |
|---------|-------------|
| `npm test` | Run all tests |
| `npm run test:backend` | Backend tests only |
| `npm run test:src` | Src tests only |
| `npm run test:frontend` | Frontend unit tests only |
| `npm run test:e2e` | E2E tests only |
| `npm run test:coverage` | All tests with coverage |
| `.\run-all-tests.ps1 -SkipE2E` | Skip E2E tests |
| `.\run-all-tests.ps1 -Coverage` | Generate coverage reports |
| `.\run-all-tests.ps1 -Verbose` | Verbose output |
