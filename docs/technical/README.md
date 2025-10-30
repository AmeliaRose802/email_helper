# Technical Documentation Index

## 🚨 Start Here

**New to this codebase?** Read these in order:
1. **[IMMEDIATE_ACTION_PLAN.md](./IMMEDIATE_ACTION_PLAN.md)** - Critical fixes to stop breakage
2. **[TECHNICAL_DEBT_CLEANUP_PLAN.md](./TECHNICAL_DEBT_CLEANUP_PLAN.md)** - Long-term cleanup strategy  
3. [technical_summary.md](./technical_summary.md) - Overall technical overview

## 📋 Quick Reference

### Architecture & Design
- [COM_EMAIL_PROVIDER.md](./COM_EMAIL_PROVIDER.md) - Outlook COM integration
- [COM_AI_SERVICE_ADAPTER.md](./COM_AI_SERVICE_ADAPTER.md) - AI service adapter pattern

### Implementation Guides
- [PAGE_RELOAD_FIX.md](./PAGE_RELOAD_FIX.md) - Handling page reloads
- [OUTLOOK_COM_FIX.md](./OUTLOOK_COM_FIX.md) - Outlook COM troubleshooting
- [email_analysis_summary.md](./email_analysis_summary.md) - Email analysis features

## 📚 Documentation Organization

### Where Things Go
- **docs/technical/** - Architecture, implementation details (YOU ARE HERE)
- **docs/features/** - User-facing feature documentation
- **docs/setup/** - Installation and configuration guides
- **docs/troubleshooting/** - Error diagnosis and fixes

### What Doesn't Belong Here
- Summary documents (use git history)
- Completion reports (use git commits)
- Progress tracking (use GitHub issues)
- One-off scripts (delete them)

## 🤖 For AI Agents

**Context gathering strategy:**
1. Read this index first
2. Check IMMEDIATE_ACTION_PLAN for known issues
3. Review relevant technical docs for the feature area
4. Check .github/copilot-instructions.md for coding standards

**Making changes safely:**
1. Understand the integration points (see technical_summary.md)
2. Check existing tests before editing
3. Follow coding standards (no mocks, no inline styles, etc.)
4. Update documentation in the correct docs/ subfolder

## 🎯 Common Tasks → Relevant Docs

| Task | Primary Doc | Related Docs |
|------|-------------|--------------|
| Fix Outlook integration | COM_EMAIL_PROVIDER.md | OUTLOOK_COM_FIX.md |
| Understand AI classification | COM_AI_SERVICE_ADAPTER.md | email_analysis_summary.md |
| Fix UI state issues | PAGE_RELOAD_FIX.md | - |
| Set up development | ../setup/*.md | - |
| Troubleshoot errors | ../troubleshooting/*.md | - |

## 📝 Contributing to Docs

**Adding new documentation:**
1. Choose correct docs/ subfolder (technical/features/setup/troubleshooting)
2. Follow existing naming conventions
3. Add entry to appropriate index (this file or docs/README.md)
4. Link from related documents

**Never create:**
- *_SUMMARY.md files
- *_COMPLETE.md files
- COMMIT_MESSAGE.txt
- Progress reports

Use git commits and code comments instead!

---

Last updated: 2025-01-15
