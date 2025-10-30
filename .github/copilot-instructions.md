# GitHub Copilot Instructions for Email Helper Project

## Project Overview

This is an intelligent email management system that helps users process, categorize, and summarize emails from their Outlook inbox. The system uses AI to analyze emails, extract action items, and provide focused summaries.

## Key Architecture Components

### Core Modules

- `backend/main.py` - FastAPI backend entry point
- `frontend/` - React frontend application
- `electron/` - Electron desktop wrapper
- `src/ai_processor.py` - AI analysis and processing logic (used by backend)
- `src/task_persistence.py` - Task management and persistence (used by backend)
- `src/azure_config.py` - Azure OpenAI configuration

### Data Flow

1. Electron app loads React frontend and starts FastAPI backend
2. Backend connects to Outlook via COM interface
3. Backend analyzes and categorizes emails using AI (src/ai_processor.py)
4. Backend stores results in SQLite database
5. Frontend presents results through React UI
6. Tasks persisted via src/task_persistence.py

## Coding Standards

### CRITICAL: Mock Usage Policy

**MOCKS ARE NEVER ACCEPTABLE IN PRODUCTION CODE**

- ❌ **NEVER** use MockEmailProvider, MockAIProvider, or any mock classes outside of test files
- ❌ **NEVER** create fallback logic that uses mocks when real implementations fail
- ❌ **NEVER** temporarily enable mocks "just for testing" in production code
- ✅ **ALWAYS** throw explicit errors when required services are unavailable
- ✅ **ALWAYS** document setup requirements in README/troubleshooting docs
- ✅ Mocks belong **ONLY** in `test/` or `**/tests/` directories
- ✅ If a service is unavailable, **FAIL FAST** with a clear error message

**Why:** Mocks hide real problems, make debugging impossible, and create false confidence that features work when they don't. Production code must fail visibly when dependencies are missing.

### Python Style

- Follow PEP 8 conventions
- Use type hints where appropriate
- Include comprehensive docstrings for all functions and classes
- Use descriptive variable and function names
- Prefer composition over inheritance
- **NEVER use mock implementations** outside of test code - fail fast with clear errors instead

### Frontend Style (React/TypeScript)

- **NEVER use inline styles** - All styling must be in CSS files
- Use CSS classes from `frontend/src/styles/unified.css` for all component styling
- Follow BEM naming convention for new CSS classes (e.g., `.component-name__element--modifier`)
- Keep component-specific styles grouped together in the CSS file with clear section headers
- Use CSS custom properties (variables) for colors, spacing, and other design tokens
- Only use inline styles for truly dynamic values that cannot be expressed in CSS (e.g., calculated widths based on runtime data)
- When creating new components, add corresponding CSS classes to `unified.css` first, then reference them in the component

### Error Handling

- Use try-catch blocks for external API calls
- Implement graceful degradation for AI service failures
- Log errors appropriately using the existing logging infrastructure
- Provide user-friendly error messages in GUI components

### Testing

- **ACTUALLY RUN YOUR TESTS** - Don't just write tests, execute them to verify they pass
- Write unit tests for new functionality in the `test/` directory
- Follow existing test patterns and naming conventions
- Include both positive and negative test cases
- Mock external dependencies (Outlook, AI services)
- **Run the test suite before submitting code** - Use `python -m pytest test/` or existing test runners
- **Verify edge cases and error conditions** - Test failure scenarios, invalid inputs, and boundary conditions
- **Test with real data when possible** - Use sample emails and realistic data scenarios
- **Integration testing is critical** - Test how components work together, not just in isolation
- **Performance testing for email processing** - Verify the system handles large email volumes efficiently
- **Track test failures with Beads** - Use `bd create` to file issues for failing tests as you discover them

## Dependencies & Integration

### External Services

- **Microsoft Graph API** - For Outlook email access
- **Azure OpenAI** - For AI processing and analysis
- **SQLite Database** - For local data persistence

### Key Libraries

- `win32com.client` - Outlook COM interface
- `sqlite3` - Database operations
- `tkinter` - GUI framework
- `requests` - HTTP API calls
- `json` - Data serialization

## Configuration Management

- Configuration is managed through `src/azure_config.py`
- User-specific data is stored in `user_specific_data/`
- Sensitive credentials should use environment variables
- Follow existing patterns for configuration loading

## Database Schema

- Email data is stored with unique identifiers and metadata
- Task persistence uses structured JSON storage
- Maintain backward compatibility when modifying schemas
- Use migrations for database structure changes

## AI Integration Patterns

### Prompt Engineering

- Prompts are stored in the `prompts/` directory as `.prompty` files
- Follow existing prompt structure and formatting
- Include clear instructions and examples in prompts
- Test prompts thoroughly before deployment

### Response Processing

- Parse AI responses defensively with error handling
- Validate JSON structures before processing
- Implement fallback behaviors for malformed responses
- Cache responses when appropriate to reduce API calls

## GUI Development

### Tkinter Patterns

- Use the existing widget patterns from `unified_gui.py`
- Implement responsive layouts that work across screen sizes
- Follow consistent styling and color schemes
- Provide user feedback for long-running operations

### User Experience

- Minimize clicks required for common operations
- Provide clear status indicators and progress feedback
- Implement keyboard shortcuts for power users
- Ensure accessibility considerations

## File Organization

### Directory Structure

- `src/` - Core application code
- `backend/` - FastAPI backend services
- `frontend/` - React frontend application
- `electron/` - Electron desktop wrapper
- `test/` - Unit and integration tests for src/
- `backend/tests/` - Backend API tests
- `prompts/` - AI prompt templates
- `docs/` - Documentation and guides (organized by category)
- `scripts/` - Reusable setup and utility scripts
- `runtime_data/` - Generated data and temporary files
- `user_specific_data/` - User configuration and personalization
- `todo/` - Development task tracking (DO NOT MODIFY)

### Documentation Organization

**CRITICAL: All documentation must go in the `docs/` folder in the correct subfolder:**

- **docs/features/** - Feature-specific guides (UI features, deduplication, analysis, etc.)
- **docs/setup/** - Setup and configuration guides (OAuth, Graph API, Electron, etc.)
- **docs/technical/** - Technical documentation (architecture, COM integration, APIs)
- **docs/troubleshooting/** - Diagnostic and troubleshooting guides

**Root-level docs:** Only `README.md`, `QUICK_START.md`, and `LICENSE` should be in root.

**NEVER create these files:**
- Implementation summaries (e.g., `*_IMPLEMENTATION_SUMMARY.md`, `FIXES_COMPLETED.md`, `*_SUMMARY.md`)
- Completion reports (e.g., `*_COMPLETE.md`, `*_DONE.md`)
- Temporary notes (e.g., `COMMIT_MESSAGE.txt`, `AI_SERVICE_FIX_SUMMARY.md`)
- Progress reports or task completion logs
- Status documents (e.g., `FIXES_COMPLETED.md`, `PROGRESS.md`)

**CRITICAL:** NEVER EVER create summary files, completion reports, or progress documents. This includes files in `runtime_data/` or any other directory. Implementation details belong in git commits and code comments ONLY.

**Why:** Implementation details belong in code comments and git history, not as separate summary documents. If documentation is needed, add it to the appropriate feature or technical doc.

### Script Organization

**Reusable scripts go in `scripts/`:**
- Setup scripts (Azure OAuth, OpenAI, user templates)
- Utility scripts (accuracy reports, diagnostics)
- Deployment scripts (localhost startup, prerequisite checks)

**One-off scripts belong NOWHERE - delete them:**
- Database migration scripts (run once, then delete)
- Manual test scripts (use proper test framework instead)
- Diagnostic scripts (convert to proper troubleshooting docs)
- Fix scripts (apply fix, commit, delete script)

### Test Organization

**Proper test locations:**
- `test/` - Tests for `src/` modules (legacy desktop app)
- `backend/tests/` - Tests for `backend/` API and services
- `frontend/tests/` - Tests for React frontend components

**NEVER create these in root:**
- `test_*.py` files outside test directories
- `check_*.py` diagnostic scripts
- `fix_*.py` one-off fix scripts
- `manual_*.py` manual testing scripts

**If you need to test something:**
1. Write a proper test in the appropriate test directory
2. Use existing test frameworks and patterns
3. Follow test naming conventions
4. Run tests with `pytest` or existing test runners

### Naming Conventions

- Use snake_case for Python files and functions
- Use descriptive names that indicate purpose
- Group related functionality in appropriately named modules
- Keep file names concise but clear
- Avoid prefixes like `test_`, `fix_`, `check_` in root directory

## Common Patterns

### Email Processing

```python
# Follow this pattern for email analysis
def process_email(email_data):
    try:
        # Validate input
        # Call AI service
        # Process response
        # Store results
        # Return structured data
    except Exception as e:
        logger.error(f"Error processing email: {e}")
        return default_response
```

### Database Operations

```python
# Use connection context managers
def store_data(data):
    with get_database_connection() as conn:
        cursor = conn.cursor()
        # Perform operations
        conn.commit()
```

### AI Service Calls

```python
# Follow existing patterns for AI integration
def call_ai_service(prompt, data):
    try:
        response = ai_client.process(prompt, data)
        return parse_ai_response(response)
    except Exception as e:
        logger.warning(f"AI service unavailable: {e}")
        return fallback_response()
```

## Performance Considerations

- Cache frequently accessed data
- Implement pagination for large email lists
- Use background processing for time-consuming operations
- Optimize database queries and use appropriate indexes
- Monitor memory usage when processing large datasets

## Security Guidelines

- Never log sensitive email content or credentials
- Validate all user inputs
- Use secure methods for credential storage
- Implement appropriate access controls
- Follow principle of least privilege

## Development Workflow

1. Create feature branches for new functionality
2. Write tests before implementing features (TDD when appropriate)
3. **RUN AND VERIFY ALL TESTS PASS** - Execute the test suite frequently during development
4. **IF TESTS FAIL** - Use the `bd` CLI tool to track the problem:
   - Run `bd create "Test failure: <test_name>" -t bug -p 1 -d "Error: <error_message>"`
   - Add relevant labels: `-l testing,backend` or `-l testing,frontend`
   - Link to parent work if applicable: `bd dep add <new-issue-id> <parent-id> --type discovered-from`
   - Check ready work with: `bd ready --json`
5. Test integration with existing components
6. **Run full test suite before commits** - Ensure nothing is broken

### Documentation Guidelines During Development

**When adding new features:**
- Update existing docs in `docs/features/` if the feature already has documentation
- Create new docs in `docs/features/` only for major user-facing features
- Add technical details to `docs/technical/` if architecture changes

**NEVER create:**
- Summary files about what you just did (use git commit messages instead)
- Implementation reports (document in code comments and technical docs)
- Temporary notes or completion checklists (use todo/ or issue tracker)

**Version control tells the story:**
- Git commits explain what changed and why
- Git history shows implementation progress
- Code comments explain how it works
- Official docs explain how to use it

## Debugging Tips

- Use the existing logging infrastructure
- Check `runtime_data/` for generated files and debugging info
- Test with various email types and content
- Verify AI service responses and error handling
- Use the test framework for isolated component testing

## Beads Task Tracking

This project uses [Beads](https://github.com/steveyegge/beads) (`bd` CLI tool) for issue tracking and task management. AI agents should use Beads instead of markdown TODO lists for all task tracking.

### Core Beads Workflow for Agents

**Finding Work:**
```bash
# Check what's ready to work on (no blockers)
bd ready --json

# View specific issue details
bd show <issue-id> --json

# List all open issues
bd list --status open --json
```

**Creating Issues:**
```bash
# File a new bug you discovered
bd create "Bug: <description>" -t bug -p 1 -d "<detailed description>" --json

# Create a feature request
bd create "Feature: <description>" -t feature -p 2 -d "<details>" --json

# Create a task with labels
bd create "Task: <description>" -t task -p 2 -l backend,testing --json
```

**Tracking Dependencies:**
```bash
# Link discovered work back to parent issue
bd dep add <new-issue-id> <parent-issue-id> --type discovered-from

# Mark an issue as blocking another
bd dep add <blocked-issue> <blocking-issue> --type blocks

# Show dependency tree
bd dep tree <issue-id> --json
```

**Updating Status:**
```bash
# Mark issue as in-progress when starting work
bd update <issue-id> --status in_progress --json

# Close issue when complete
bd close <issue-id> --reason "Implemented feature X" --json

# Add notes to an issue
bd update <issue-id> --notes "Additional context..." --json
```

**Filtering and Searching:**
```bash
# Find high-priority work
bd ready --priority 1 --json

# Find backend-related issues
bd list --label backend --json

# Find bugs
bd list --type bug --status open --json
```

### Beads Best Practices for Agents

1. **File issues automatically** - When you discover bugs, missing features, or technical debt during work, immediately file them with `bd create`
2. **Link related work** - Always link new issues back to the parent issue you were working on using `--type discovered-from`
3. **Update status immediately** - Mark issues `in_progress` when starting, `closed` when done
4. **Use proper issue types** - `bug`, `feature`, `task`, `epic`, `chore`
5. **Set accurate priorities** - P0 (critical), P1 (high), P2 (medium), P3 (low), P4 (backlog)
6. **Add meaningful labels** - Use labels like `backend`, `frontend`, `testing`, `documentation`, `performance`
7. **Check ready work first** - Always run `bd ready` to see what's unblocked before starting new work
8. **Avoid markdown TODOs** - Use Beads instead of creating TODO lists in markdown files

### Why Beads?

- **Long-term memory** - Track work across multiple sessions without forgetting
- **Dependency tracking** - Understand what's blocked and what's ready
- **Automatic sync** - Issues are stored in git and sync across machines
- **Agent-friendly** - JSON output for programmatic integration
- **No context loss** - Never lose track of discovered work due to context limits

### Beads vs Manual Tracking

❌ **Don't do this:**
```markdown
## TODO
- [ ] Fix bug in email processor
- [ ] Add tests for AI service
- [ ] Update documentation
```

✅ **Do this instead:**
```bash
bd create "Fix bug in email processor" -t bug -p 1 -l backend
bd create "Add tests for AI service" -t task -p 2 -l testing
bd create "Update documentation" -t chore -p 3 -l documentation
```

### Beads Integration

The Beads database is located in `.beads/` directory (gitignored). The source of truth is `.beads/issues.jsonl` (committed to git). Beads automatically syncs between the SQLite cache and JSONL file.

**Never manually edit `.beads/issues.jsonl`** - Always use the `bd` CLI tool.

## PowerShell and Process Management

### CRITICAL: Never Use taskkill in PowerShell Scripts

**ALWAYS use PowerShell's native `Stop-Process` cmdlet instead of `taskkill`**

❌ **WRONG - Will prompt for confirmation and block:**
```powershell
taskkill /IM electron.exe /F
taskkill /IM python.exe /F
```

✅ **CORRECT - No prompts, never blocks:**
```powershell
Get-Process -Name electron -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
```

### Why This Matters

- `taskkill` is a Windows command-line tool that may prompt for confirmation when multiple processes match
- Even with `/F` flag, `taskkill` can block waiting for user input with "Terminate batch job (Y/N)?"
- `Stop-Process -Force` is PowerShell-native and **NEVER prompts for confirmation**
- `-ErrorAction SilentlyContinue` prevents errors when no matching processes exist

### Proper Process Cleanup Pattern

```powershell
# Kill processes without prompts
Get-Process -Name electron -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Free specific ports if needed
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    $port8000 | Select-Object -ExpandProperty OwningProcess | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
}

# Wait for cleanup
Start-Sleep -Seconds 2
```

### Electron App Startup

Use the provided `electron/start-app.ps1` script for clean app startup:
```powershell
cd c:\Users\ameliapayne\email_helper\electron
& ".\start-app.ps1"
```

This script handles:
- Killing existing Electron and Python processes (without prompts!)
- Freeing port 8000
- Starting the app cleanly

### Terminal Command Best Practices

When running terminal commands:
1. **Always use `Stop-Process`** instead of `taskkill` in PowerShell
2. Include `-ErrorAction SilentlyContinue` to handle cases where processes don't exist
3. Use `Start-Sleep` after killing processes to ensure cleanup completes
4. Check for port conflicts with `Get-NetTCPConnection` before starting servers

Remember: This project handles sensitive user data (emails). Always prioritize security, privacy, and reliability in your implementations.
