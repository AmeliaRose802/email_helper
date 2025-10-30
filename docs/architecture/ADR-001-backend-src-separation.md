# ADR-001: Backend/Src Separation

## Status
**Accepted** (October 2025)

## Context

The Email Helper project evolved from a desktop application into a multi-platform system supporting:
1. **Desktop GUI** - Original Tkinter-based application for Windows
2. **Web Application** - React frontend with FastAPI backend for browser access
3. **Mobile Application** - React Native app connecting to REST API

This evolution created a challenge: how to structure the codebase to support both the legacy desktop application and the modern web/mobile architecture without creating maintenance burden or code duplication.

The key concerns were:
- **Code Reuse**: Core logic (AI processing, Outlook integration, task persistence) should be shared
- **Backward Compatibility**: Existing desktop users should continue to work without disruption
- **Clean Architecture**: New backend should follow modern web API patterns
- **Development Velocity**: Teams should be able to work independently on desktop vs. web/mobile
- **Deployment Flexibility**: Desktop and web/mobile have different deployment models

## Decision

We maintain **two separate top-level directories** with shared code:

```
email_helper/
├── backend/              # FastAPI REST API for web/mobile
│   ├── api/             # API endpoints
│   ├── core/            # Backend-specific config & DI
│   ├── models/          # Pydantic models for API
│   └── services/        # Service adapters
├── src/                 # Core application logic (SHARED)
│   ├── ai_processor.py  # AI classification & processing
│   ├── outlook_manager.py # Outlook COM integration
│   ├── task_persistence.py # Database operations
│   └── core/            # Shared configuration
└── email_manager_main.py # Desktop GUI entry point
```

**Backend imports from src** using path manipulation:
```python
# backend/main.py
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from ai_processor import AIProcessor
from outlook_manager import OutlookManager
```

This creates a **layered architecture**:
- **src/**: Core business logic (platform-agnostic)
- **backend/**: Web API layer (FastAPI-specific)
- **Desktop**: Direct imports from src/ for GUI application

## Consequences

### Positive

✅ **Clear Separation of Concerns**: Web API logic stays separate from desktop GUI logic
✅ **Code Reuse**: Both platforms share core AI processing, Outlook integration, and database logic
✅ **Independent Development**: Backend and desktop teams can work without conflicts
✅ **Backward Compatibility**: Desktop application continues to work exactly as before
✅ **Migration Path**: Easy to migrate desktop features to API gradually
✅ **Testing Isolation**: Can test backend API independently from desktop GUI
✅ **Deployment Flexibility**: Can deploy backend to cloud while desktop stays local

### Negative

❌ **Path Manipulation**: Backend needs `sys.path.insert()` which is non-standard
❌ **Import Complexity**: Need to understand which code lives where
❌ **Duplication Risk**: Some configuration exists in both backend/core and src/core
❌ **Refactoring Burden**: Changes to shared code affect both platforms

### Neutral

⚠️ **Documentation Requirement**: Must clearly document which code is shared vs. platform-specific
⚠️ **Testing Strategy**: Need tests for both direct usage (desktop) and API usage (backend)

## Alternatives Considered

### Alternative 1: Single Unified Structure
```
email_helper/
├── core/               # Shared business logic
├── desktop/           # Desktop-specific code
└── api/               # API-specific code
```

**Rejected because:**
- Would require major refactoring of working desktop application
- Higher risk of breaking existing functionality
- More complex migration path
- Existing imports would all break

### Alternative 2: Backend as Package
```
email_helper/
├── email_helper/      # Installable package
│   ├── ai_processor.py
│   └── outlook_manager.py
├── desktop/
│   └── gui.py
└── backend/
    └── api/
```

**Rejected because:**
- Requires package installation for development
- Complicates local development workflow
- Added build/distribution complexity
- Not justified for current project scale

### Alternative 3: Separate Repositories
- `email_helper-core`: Shared logic as library
- `email_helper-desktop`: Desktop application
- `email_helper-api`: Backend API

**Rejected because:**
- Too much overhead for current team size
- Complicates version management
- Slower iteration on shared code
- Requires package registry setup

## Implementation Notes

### Import Pattern
Backend modules use this pattern:
```python
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Now can import shared modules
from ai_processor import AIProcessor
from outlook_manager import OutlookManager
```

### Configuration Management
- **Shared config**: `src/core/config.py` (business logic configuration)
- **Backend config**: `backend/core/config.py` (API-specific settings like CORS, JWT)

### Testing Strategy
- **Shared code tests**: `test/` directory tests src/ modules directly
- **Backend tests**: `backend/tests/` tests API endpoints and integrations
- **Desktop tests**: Tests in `test/` for GUI functionality

### Documentation
- Backend README explains the separation and import pattern
- Project README describes both deployment modes
- This ADR provides architectural rationale

## Related Decisions

- [ADR-002: Dependency Injection Pattern](ADR-002-dependency-injection-pattern.md) - Explains how backend adapts shared services
- [ADR-003: Testing Strategy](ADR-003-testing-strategy.md) - Testing approach for both platforms

## Future Considerations

As the project evolves, consider:

1. **Gradual Migration**: Move more desktop code into shared src/ as web/mobile features expand
2. **Package Extraction**: If codebase grows significantly, revisit Alternative 2 (backend as package)
3. **Microservices**: For very large scale, separate services (email, AI, tasks) into independent APIs
4. **Shared Models**: Create shared Pydantic models to ensure type safety across platforms

## References

- Initial implementation: October 2025
- Backend README: `backend/README.md`
- Project structure discussion in Sprint Planning (October 2025)

## Authors

- Architecture: Development Team
- Documentation: GitHub Copilot
- Review: Project Maintainers
