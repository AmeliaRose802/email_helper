# GitHub Actions Workflows

This directory contains CI/CD workflows for the Email Helper project.

## Workflows

### 🔍 Merge Validation (`merge-validation.yml`)

**Triggers:**
- Pull requests to `master`, `main`, or `develop`
- Direct pushes to main branches
- Manual workflow dispatch

**What it does:**
1. **Test Suite** - Runs comprehensive tests across Python 3.10 and 3.11
   - Essential tests (must pass)
   - Core test suite
   - Backend API tests
   - Generates coverage reports

2. **Code Quality** - Checks code standards
   - Black formatting validation
   - Flake8 linting
   - Syntax error detection

3. **Security Scan** - Checks for vulnerabilities
   - Dependency vulnerability scanning with Safety

4. **Validation Summary** - Final status check
   - Fails merge if essential tests fail
   - Warns on quality/security issues

**Duration:** ~15-30 minutes

**Artifacts:**
- Test results (XML)
- Coverage reports (HTML)
- Retained for 30 days

### ⚡ Quick Check (`quick-check.yml`)

**Triggers:**
- Pull request creation/updates
- Manual workflow dispatch

**What it does:**
- Fast syntax validation
- Import checks
- Essential tests only (fast subset)

**Duration:** ~5-10 minutes

**Use case:** Rapid feedback for developers during active development

## Running Workflows

### Automatic Triggers

Workflows run automatically on:
```bash
# Create or update a PR
git push origin feature-branch

# Merge to main branch
git checkout master
git merge feature-branch
git push origin master
```

### Manual Triggers

From GitHub web interface:
1. Go to "Actions" tab
2. Select workflow
3. Click "Run workflow"
4. Choose branch and run

From GitHub CLI:
```bash
# Run merge validation
gh workflow run merge-validation.yml

# Run quick check
gh workflow run quick-check.yml
```

## Configuration

### Required Secrets

None required for basic testing. Optional secrets for enhanced features:

- `AZURE_OPENAI_ENDPOINT` - For real AI integration tests
- `AZURE_OPENAI_API_KEY` - For real AI integration tests

Set secrets in: Repository Settings → Secrets and variables → Actions

### Customization

#### Adjust Python Versions

Edit `merge-validation.yml`:
```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']  # Add versions
```

#### Adjust Test Timeouts

```yaml
timeout-minutes: 30  # Increase if tests take longer
```

#### Change Branch Protection

Edit workflow triggers:
```yaml
on:
  pull_request:
    branches:
      - master
      - main
      - release/*  # Add patterns
```

## Branch Protection Rules

Recommended GitHub branch protection settings for `master`:

1. **Require pull request reviews before merging** ✅
   - Required approvals: 1

2. **Require status checks to pass before merging** ✅
   - Required checks:
     - `Run Tests (3.10)`
     - `Run Tests (3.11)`
     - `Code Quality Checks`
     - `Validation Summary`

3. **Require branches to be up to date** ✅

4. **Do not allow bypassing** ✅

## Test Results

### Viewing Results

1. **In Pull Request:**
   - Check marks/crosses appear on PR
   - Click "Details" for full logs

2. **In Actions Tab:**
   - See all workflow runs
   - Download artifacts (test results, coverage)

3. **Coverage Reports:**
   - Download from artifacts
   - Open `htmlcov/index.html` locally

### Understanding Status

| Status | Meaning | Action |
|--------|---------|--------|
| ✅ Success | All essential tests passed | Safe to merge |
| ⚠️ Warning | Non-critical issues found | Review warnings |
| ❌ Failure | Essential tests failed | Fix before merge |
| ⏭️ Skipped | Job was skipped | Check dependencies |

## Troubleshooting

### Common Issues

**1. Tests fail on CI but pass locally**
- Ensure all dependencies in `requirements.txt`
- Check for OS-specific code
- Verify environment variables

**2. Windows runner issues**
- pywin32 requires Windows runner
- Can't run Outlook COM tests in containers

**3. Timeout errors**
- Increase `timeout-minutes`
- Optimize slow tests
- Split into separate jobs

**4. Cache issues**
- Clear pip cache in workflow settings
- Update cache key version

### Debug Commands

Add debug step to workflow:
```yaml
- name: Debug environment
  run: |
    python --version
    pip list
    Get-ChildItem Env:
  shell: pwsh
```

## Performance Optimization

### Current Optimization

- ✅ Pip dependency caching
- ✅ Parallel test execution across Python versions
- ✅ Quick check workflow for fast feedback
- ✅ Artifact retention limits (30 days)

### Future Improvements

- [ ] Docker layer caching
- [ ] Test result caching
- [ ] Selective test execution based on changed files
- [ ] Matrix strategy for OS testing (when applicable)

## Maintenance

### Regular Tasks

- **Weekly:** Review test execution times
- **Monthly:** Update action versions
- **Quarterly:** Review and update Python versions
- **As needed:** Adjust timeouts and resource limits

### Updating Actions

Keep actions up to date:
```yaml
# Check for updates
uses: actions/checkout@v4  # Update version number
uses: actions/setup-python@v5
```

## Links

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python setup action](https://github.com/actions/setup-python)
- [Upload artifact action](https://github.com/actions/upload-artifact)
- [Test result publisher](https://github.com/EnricoMi/publish-unit-test-result-action)

## Support

For issues with workflows:
1. Check Actions tab for detailed logs
2. Review this documentation
3. Check GitHub Actions status page
4. Consult project maintainers
