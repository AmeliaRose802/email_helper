# Regression Test Suite

This directory contains the regression test suite for the Email Helper project, designed to catch issues before they reach production.

## Overview

The regression test suite covers critical functionality:
- **Email classification accuracy** - Ensures emails are classified correctly
- **Task deduplication logic** - Prevents duplicate tasks from being created
- **Date parsing edge cases** - Handles various date formats and invalid inputs
- **JSON response handling** - Parses AI responses reliably
- **Action item extraction** - Extracts tasks accurately from emails
- **Workflow integration** - Tests complete end-to-end workflows

## Test Files

### `test_regressions.py`
Comprehensive regression tests organized by functionality:
- `TestEmailClassificationRegression` - Email categorization accuracy
- `TestTaskDeduplicationRegression` - Duplicate detection logic
- `TestDateParsingRegression` - Date parsing edge cases
- `TestJSONResponseHandlingRegression` - JSON parsing robustness
- `TestActionItemExtractionRegression` - Action item extraction
- `TestBatchProcessingRegression` - Batch processing consistency
- `TestSummarizationRegression` - Email summarization quality
- `TestErrorHandlingRegression` - Error handling and recovery
- `TestWorkflowIntegrationRegression` - End-to-end workflows
- `TestGoldenFileRegression` - Golden file testing (future)

### Supporting Test Files
- `test_date_utils.py` - Date utility function tests
- `test_json_utils.py` - JSON utility function tests
- `backend/tests/fixtures/ai_response_fixtures.py` - AI response fixtures

## Running Tests

### Run All Regression Tests
```powershell
python -m pytest test/test_regressions.py -v
```

### Run Specific Test Class
```powershell
python -m pytest test/test_regressions.py::TestEmailClassificationRegression -v
```

### Run with Coverage
```powershell
python -m pytest test/test_regressions.py --cov=src --cov=backend --cov-report=html
```

### Continuous Integration
Regression tests run automatically:
- On every push to `main` and `develop` branches
- On every pull request
- Daily at 2 AM UTC (scheduled)

CI workflow: `.github/workflows/regression-tests.yml`

## Test Data

### Golden Files
Golden files store expected outputs for comparison:
- Location: `test/test_data/regression/`
- Format: JSON files with `.golden.json` extension
- Usage: Compare actual results against known-good outputs

To create/update golden files:
```powershell
python -m pytest test/test_regressions.py --update-golden
```

### Fixtures
AI response fixtures are in `backend/tests/fixtures/ai_response_fixtures.py`:
- Classification responses for all categories
- Action item extraction examples
- Summarization outputs
- Error responses
- Batch processing results

## Adding New Regression Tests

### 1. Identify the Bug or Feature
Document what should NOT regress:
```python
def test_specific_bug_fix(self):
    """Regression: Bug #123 - emails with 'please' but no deadline were misclassified"""
```

### 2. Create a Failing Test First
Write the test that would have caught the bug:
```python
def test_classify_polite_fyi_email(self):
    """Regression: Polite language doesn't mean action required"""
    # This should be FYI, not required_personal_action
    result = classify_email("Please enjoy this newsletter")
    assert result["category"] == "fyi_only"
```

### 3. Use Fixtures for Consistency
Leverage existing fixtures:
```python
from backend.tests.fixtures.ai_response_fixtures import (
    get_classification_response_fyi
)

def test_my_regression(self):
    result = get_classification_response_fyi()
    assert result["category"] == "fyi_only"
```

### 4. Add Test to Appropriate Class
Organize by functionality:
- Classification issues → `TestEmailClassificationRegression`
- Date parsing bugs → `TestDateParsingRegression`
- JSON errors → `TestJSONResponseHandlingRegression`
- Workflow problems → `TestWorkflowIntegrationRegression`

## Test Quality Guidelines

### ✅ DO
- **Test real bugs** - Add regression tests for actual bugs found
- **Use descriptive names** - Name tests after what they prevent
- **Document the regression** - Explain why this test exists
- **Use fixtures** - Leverage shared test data
- **Test edge cases** - Invalid inputs, boundary conditions
- **Keep tests fast** - Each test should run in milliseconds

### ❌ DON'T
- **Test implementation details** - Test behavior, not internals
- **Add flaky tests** - Tests should be deterministic
- **Skip error handling** - Always test graceful failure
- **Ignore test failures** - Fix or document why they fail
- **Write redundant tests** - One test per regression

## CI Integration

### GitHub Actions Workflow
The regression test suite runs in multiple jobs:
1. **regression-tests** - Full suite
2. **classification-accuracy** - Classification tests only
3. **deduplication-tests** - Deduplication tests only
4. **workflow-integration** - End-to-end workflow tests

### On Failure
When regression tests fail in CI:
- ❌ PR comment is added with failure details
- 📊 Test results are uploaded as artifacts
- 🚫 Merge is blocked until tests pass

### Test Results
Results are available in GitHub Actions:
- Detailed test output in job logs
- Test inventory in artifacts
- Coverage reports (if enabled)

## Golden File Testing

Golden file testing compares outputs against known-good results.

### Creating Golden Files
```python
from test_regressions import GoldenFileTester

result = classify_email(test_email)
GoldenFileTester.save_golden("classification_example", result)
```

### Using Golden Files
```python
def test_with_golden_file(self):
    result = classify_email(test_email)
    assert GoldenFileTester.compare_with_golden("classification_example", result)
```

### Updating Golden Files
When behavior intentionally changes:
```powershell
python -m pytest test/test_regressions.py --update-golden
```

## Maintenance

### Regular Review
- **Weekly**: Review new regression tests added
- **Monthly**: Check for redundant tests
- **Quarterly**: Update fixtures with new AI response patterns

### Performance Monitoring
Keep regression tests fast:
- Target: <2 seconds total execution time
- Monitor: CI job duration
- Action: Optimize slow tests or move to integration suite

### Coverage Goals
Regression tests should cover:
- ✅ All critical user workflows
- ✅ All previously found bugs
- ✅ All edge cases in production data
- ✅ All error handling paths

Target: 80%+ coverage of critical paths

## Troubleshooting

### Tests Pass Locally but Fail in CI
- Check Python version differences (local vs CI)
- Verify all dependencies are in `requirements.txt`
- Check for file path issues (Windows vs Linux)
- Review test data directory structure

### Flaky Tests
If a test occasionally fails:
1. Add more specific assertions
2. Remove timing dependencies
3. Use deterministic test data
4. Consider moving to integration suite

### Slow Tests
If regression tests take too long:
1. Profile with `pytest --durations=10`
2. Mock external dependencies
3. Reduce test data size
4. Consider parallelization

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [CI/CD with GitHub Actions](https://docs.github.com/en/actions)

## Contact

For questions about the regression test suite:
- Check existing tests for examples
- Review this README
- Ask in team chat or create an issue
