# Contributing to Email Helper

Welcome! This guide will help you contribute effectively to the Email Helper project.

## 🚀 Quick Start for New Contributors

### Prerequisites
- **Python 3.9+** with pip
- **Node.js 18+** with npm
- **Windows OS** (for Outlook COM integration)
- **Microsoft Outlook** installed
- **Git** for version control

### Initial Setup (15 minutes)

1. **Clone the repository**
```powershell
git clone https://github.com/AmeliaRose802/email_helper.git
cd email_helper
```

2. **Install Python dependencies**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. **Install frontend dependencies**
```powershell
cd frontend
npm install
```

4. **Install Electron dependencies**
```powershell
cd ../electron
npm install
```

5. **Configure environment**
```powershell
# Copy example env file
cp .env.example .env

# Edit .env with your Azure OpenAI credentials
```

6. **Run tests**
```powershell
# Backend tests
pytest backend/tests/

# Frontend tests  
cd frontend
npm run test
```

---

## 📋 Development Workflow

### Branch Strategy
- `main` - Production-ready code
- `electron` - Current development branch (Electron app)
- `feature/*` - Feature branches
- `fix/*` - Bug fix branches

### Making Changes

1. **Create a feature branch**
```powershell
git checkout -b feature/your-feature-name
```

2. **Make your changes**
   - Follow coding standards (see below)
   - Write tests for new functionality
   - Update documentation

3. **Test your changes**
```powershell
# Run linter
cd frontend
npm run lint

# Run tests
pytest backend/tests/
npm run test
```

4. **Commit with clear messages**
```powershell
git commit -m "feat(emails): add email deduplication logic

- Implement content-based similarity detection
- Add tests for edge cases
- Update documentation

Fixes #123"
```

5. **Push and create PR**
```powershell
git push origin feature/your-feature-name
# Create PR on GitHub
```

---

## 🎨 Coding Standards

### Critical Rules (NEVER VIOLATE)

#### 1. NO MOCK USAGE IN PRODUCTION
```python
# ❌ WRONG - Never use mocks outside tests
from mock import MockEmailProvider

# ✅ CORRECT - Fail fast with clear errors
if not outlook_available():
    raise RuntimeError("Outlook is required but not available")
```

#### 2. NO INLINE STYLES IN REACT
```typescript
// ❌ WRONG - Inline styles
<div style={{ color: 'red', fontSize: '14px' }}>Error</div>

// ✅ CORRECT - CSS classes
<div className="error-message">Error</div>
```

#### 3. NO EMOJIS IN PYTHON LOGGING
```python
# ❌ WRONG - Windows terminals crash on emojis
print("🤖 Starting AI processor...")
logger.warning(f"⚠️ Content filter blocked")

# ✅ CORRECT - Plain text prefixes
print("[AI] Starting AI processor...")
logger.warning("[WARN] Content filter blocked")
```

#### 4. NO @ts-expect-error WITHOUT JUSTIFICATION
```typescript
// ❌ WRONG - Hiding errors
// @ts-expect-error - TODO: fix later
const data: any = fetchData();

// ✅ CORRECT - Fix the actual issue
const data: EmailData = fetchData();
```

### Python Style
- Follow PEP 8
- Use type hints where appropriate
- Comprehensive docstrings for all public functions
- Descriptive variable names
- Use `Stop-Process` not `taskkill` in PowerShell scripts

### TypeScript/React Style
- All styles in CSS files (unified.css)
- Use BEM naming convention for CSS classes
- Prefer functional components with hooks
- Type everything (no `any` types)
- Use RTK Query for API calls

---

## 🧪 Testing Requirements

### Required Before PR
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] ESLint passes with no errors
- [ ] No console warnings in development

### Test Locations
- `backend/tests/` - Backend API tests
- `test/` - Legacy module tests
- `frontend/src/test/` - Frontend unit tests
- `frontend/tests/e2e/` - E2E tests

### Running Tests
```powershell
# Backend unit tests
pytest backend/tests/ -v

# Frontend unit tests
cd frontend
npm run test

# E2E tests (requires app running)
npm run test:e2e

# Linting
npm run lint
```

### Test Coverage
- **Backend:** Aim for 80%+ coverage
- **Frontend:** Aim for 70%+ coverage
- **Critical paths:** 100% coverage required

---

## 📁 File Organization

### Where Things Go
```
backend/          # FastAPI backend services
  api/           # REST API endpoints
  services/      # Business logic
  clients/       # External service clients
  database/      # Data access layer
  tests/         # Backend tests

frontend/         # React frontend
  src/pages/    # Route components
  src/components/ # Reusable UI components
  src/services/  # API clients (RTK Query)
  src/styles/    # CSS files (unified.css)
  tests/e2e/     # E2E tests

electron/         # Electron desktop wrapper
  main.js       # App entry point
  preload.js    # IPC bridge

docs/             # Documentation
  technical/    # Architecture, implementation
  features/     # Feature guides
  setup/        # Installation guides
  troubleshooting/ # Error diagnosis

prompts/          # AI prompt templates (.prompty files)
scripts/          # Reusable utility scripts
src/              # Legacy desktop app (DEPRECATED)
test/             # Legacy module tests
```

### What NOT to Create
- ❌ `*_SUMMARY.md` files (use git commits)
- ❌ `*_COMPLETE.md` files (use git history)
- ❌ `COMMIT_MESSAGE.txt` (commit directly)
- ❌ Root-level test scripts (use test/ directories)
- ❌ Manual diagnostic scripts (convert to troubleshooting docs)

---

## 🔄 Common Development Tasks

### Adding a New Feature

1. **Understand the architecture**
   - Read `docs/technical/ARCHITECTURE.md`
   - Identify affected components
   - Check integration points

2. **Plan the change**
   - Write tests first (TDD)
   - Consider backward compatibility
   - Document API changes

3. **Implement**
   - Follow coding standards
   - Add inline comments for complex logic
   - Keep functions small and focused

4. **Test thoroughly**
   - Unit tests for isolated logic
   - Integration tests for component interaction
   - E2E tests for user workflows

5. **Document**
   - Update relevant docs in `docs/` subdirectories
   - Add JSDoc/docstrings
   - Update README if needed

### Fixing a Bug

1. **Reproduce the bug**
   - Create a failing test case
   - Document steps to reproduce
   - Identify root cause

2. **Fix the issue**
   - Minimal change to fix bug
   - Don't refactor unnecessarily
   - Keep changes focused

3. **Verify the fix**
   - Ensure test passes
   - Check for regression
   - Manual testing

4. **Document**
   - Add comment explaining the fix
   - Update troubleshooting docs if applicable

### Modifying AI Prompts

1. **Location:** `prompts/*.prompty` files
2. **Test changes:** Run classification on sample emails
3. **Document:** Add examples in prompt comments
4. **Version:** Include version info in prompt metadata

---

## 🐛 Troubleshooting Development Issues

### Port Already in Use
```powershell
# Kill process using port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | `
  Select-Object -ExpandProperty OwningProcess | `
  ForEach-Object { Stop-Process -Id $_ -Force }
```

### Python Import Errors
```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Outlook COM Errors
- Ensure Outlook is installed
- Check Outlook is not in "Safe Mode"
- Restart Outlook
- See `docs/troubleshooting/OUTLOOK_COM_FIX.md`

### Frontend Build Errors
```powershell
# Clear cache and reinstall
cd frontend
Remove-Item node_modules -Recurse -Force
Remove-Item package-lock.json
npm install
```

---

## 📝 Commit Message Format

Use conventional commits:

```
type(scope): brief description

Detailed explanation of changes made.
Can span multiple lines.

- Bullet points for specific changes
- Reference issues when applicable

Fixes #123
```

### Types
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Code style (formatting, not CSS)
- `refactor` - Code refactoring
- `perf` - Performance improvement
- `test` - Adding/updating tests
- `chore` - Build process, tooling

### Scopes
- `emails` - Email processing
- `ai` - AI classification
- `tasks` - Task management
- `ui` - Frontend UI
- `api` - Backend API
- `docs` - Documentation
- `electron` - Electron app

### Examples
```
feat(ai): add few-shot learning for classification

Implement similarity-based example selection to improve
classification accuracy. Uses keyword overlap scoring.

- Add get_few_shot_examples() method
- Update prompts to include examples
- Add tests for example selection

Closes #45
```

```
fix(emails): resolve duplicate email detection issue

Fixed bug where emails with similar subjects were incorrectly
marked as duplicates. Now uses content similarity threshold.

- Update similarity calculation algorithm
- Add unit tests for edge cases
- Improve performance by 30%

Fixes #67
```

---

## 🎯 Pull Request Process

### Before Submitting
- [ ] All tests pass locally
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No merge conflicts with target branch
- [ ] Commit messages are clear and descriptive

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] E2E tests added/updated
- [ ] Manual testing performed

## Documentation
- [ ] Code comments added
- [ ] README updated (if needed)
- [ ] Technical docs updated

## Screenshots (if applicable)
Add screenshots here

## Related Issues
Fixes #123
```

### Review Process
1. Automated checks run (linting, tests)
2. Code review by maintainer
3. Address feedback
4. Approval and merge

---

## 🔍 Code Review Guidelines

### Reviewing Code
- Check for coding standard violations
- Verify test coverage
- Look for potential bugs
- Consider performance implications
- Ensure documentation is clear

### Receiving Feedback
- Be receptive to suggestions
- Ask questions if unclear
- Make requested changes promptly
- Keep discussions focused on code

---

## 📚 Additional Resources

### Documentation
- [Architecture Overview](docs/technical/ARCHITECTURE.md)
- [Coding Standards](docs/CODE_QUALITY_STANDARDS.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [Setup Guides](docs/setup/)

### Key Files
- `.github/copilot-instructions.md` - AI agent guidelines
- `docs/technical/README.md` - Technical docs index
- `README.md` - Project overview

---

## 💬 Getting Help

### Questions?
1. Check existing documentation
2. Search closed issues on GitHub
3. Ask in PR comments
4. Open a new issue with `question` label

### Found a Bug?
1. Search existing issues
2. If new, open an issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details

---

## 🎉 Thank You!

Your contributions make this project better. Thank you for taking the time to contribute!

Remember: **Quality over speed.** Take time to write clean, well-tested code that follows our standards.
