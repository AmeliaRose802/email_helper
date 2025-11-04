# Email Helper - System Architecture

## Overview

Email Helper is an intelligent email management system designed for professionals with ADHD who need focused, actionable email summaries. The system uses AI to analyze, categorize, and extract actionable insights from emails.

**Key Design Principles:**
- **Modular Architecture**: Clear separation between desktop app, web app, and backend services
- **Service-Oriented Design**: Specialized services with single responsibilities
- **Dependency Injection**: Testable, loosely-coupled components
- **Multi-Platform Support**: Desktop (Electron), Web (React), and Native Outlook integration

## System Components

The application consists of four major components:

```
┌──────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                            │
├───────────────┬──────────────────┬───────────────────────────┤
│   Electron    │   React Web      │   Legacy Desktop GUI      │
│   Desktop App │   Application    │   (Tkinter)               │
│   (Port 3000) │   (Port 3000)    │   (Direct Integration)    │
└───────┬───────┴────────┬─────────┴──────────┬────────────────┘
        │                │                     │
        └────────────────┼─────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    BACKEND API LAYER                         │
│              FastAPI REST API (Port 8000)                    │
│   Endpoints: /api/emails, /api/ai, /api/tasks, /health      │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│                   SERVICE LAYER                              │
│  EmailProcessingService, AIService, TaskService,             │
│  EmailProvider, COMEmailProvider, WebSocketManager           │
└────────┬────────────────────────┬────────────────────────────┘
         │                        │
         ▼                        ▼
┌────────────────────┐   ┌────────────────────────────────────┐
│  DATA ACCESS       │   │  BUSINESS LOGIC ENGINES            │
│  - Database        │   │  - AIOrchestrator                  │
│  - Email Sync      │   │  - ClassificationEngine            │
│  - Task Storage    │   │  - ExtractionEngine                │
└────────────────────┘   │  - AnalysisEngine                  │
                         │  - PromptExecutor                  │
                         └─────────────┬──────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────┐
│                  EXTERNAL INTEGRATIONS                       │
│  - Microsoft Outlook (COM/win32)                             │
│  - Azure OpenAI (GPT-4o)                                     │
│  - SQLite Database                                           │
└──────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
email_helper/
├── backend/                    # FastAPI REST API backend
│   ├── api/                   # API endpoint handlers
│   │   ├── emails.py         # Email operations API
│   │   ├── ai.py             # AI processing API
│   │   ├── tasks.py          # Task management API
│   │   ├── processing.py     # Email processing workflows
│   │   └── settings.py       # Application settings API
│   ├── core/                  # Core configuration and business logic
│   │   ├── business/         # Business logic engines
│   │   │   ├── ai_orchestrator.py      # AI coordination facade
│   │   │   ├── classification_engine.py # Email categorization
│   │   │   ├── extraction_engine.py     # Summary/action extraction
│   │   │   ├── analysis_engine.py       # Deduplication/analysis
│   │   │   ├── prompt_executor.py       # Prompty template execution
│   │   │   └── context_manager.py       # User context management
│   │   ├── infrastructure/   # Infrastructure utilities
│   │   │   ├── azure_config.py          # Azure OpenAI config
│   │   │   ├── data_utils.py            # Data processing utilities
│   │   │   ├── json_utils.py            # JSON handling
│   │   │   ├── text_utils.py            # Text processing
│   │   │   └── analytics/               # Analytics tracking
│   │   ├── config.py         # Application settings
│   │   └── dependencies.py   # FastAPI dependency injection
│   ├── services/              # Service layer implementations
│   │   ├── ai_service.py                # AI processing coordination
│   │   ├── email_provider.py            # Email provider interface
│   │   ├── com_email_provider.py        # Outlook COM provider
│   │   ├── email_processing_service.py  # Email workflow coordination
│   │   ├── email_classification_service.py # Classification logic
│   │   ├── email_task_extraction_service.py # Task extraction
│   │   ├── email_sync_service.py        # Database synchronization
│   │   ├── task_service.py              # Task management
│   │   └── websocket_manager.py         # Real-time updates
│   ├── database/              # Database management
│   │   └── connection.py     # SQLite connection handling
│   ├── models/                # Pydantic data models
│   │   ├── email.py          # Email models
│   │   ├── email_requests.py # API request/response models
│   │   └── task.py           # Task models
│   ├── tests/                 # Backend unit/integration tests
│   └── main.py               # FastAPI application entry point
│
├── frontend/                   # React web application
│   ├── src/
│   │   ├── components/       # Reusable React components
│   │   ├── pages/            # Page components (Dashboard, EmailList, etc.)
│   │   ├── services/         # RTK Query API services
│   │   ├── store/            # Redux store and slices
│   │   ├── router/           # React Router configuration
│   │   ├── types/            # TypeScript type definitions
│   │   └── styles/           # CSS stylesheets
│   ├── tests/                # Frontend unit/E2E tests
│   └── vite.config.ts        # Vite build configuration
│
├── electron/                   # Electron desktop wrapper
│   ├── main.js               # Electron main process
│   ├── preload.js            # Security boundary preload script
│   └── start-app.ps1         # Application launcher
│
├── src/                        # Legacy desktop application (Tkinter)
│   ├── unified_gui.py        # Desktop GUI interface
│   ├── ai_processor.py       # Legacy AI integration (being phased out)
│   ├── outlook_manager.py    # Outlook COM operations
│   └── task_persistence.py   # Task storage implementation
│
├── prompts/                    # AI prompt templates (.prompty files)
│   ├── email_classifier_with_explanation.prompty
│   ├── email_one_line_summary.prompty
│   ├── summerize_action_item.prompty
│   └── holistic_inbox_analyzer.prompty
│
├── runtime_data/              # Generated runtime data (not in git)
│   ├── database/             # SQLite databases
│   ├── logs/                 # Application logs
│   ├── tasks/                # Task persistence
│   └── user_feedback/        # AI learning feedback
│
├── user_specific_data/        # User configuration (not in git)
│   ├── job_summery.md        # User job context
│   ├── job_skill_summery.md  # User skills profile
│   └── username.txt          # User identifier
│
└── docs/                       # Documentation
    ├── features/              # Feature-specific guides
    ├── setup/                 # Setup instructions
    ├── technical/             # Technical documentation (this file)
    └── troubleshooting/       # Diagnostic guides
```

## Data Flow

### Email Classification Workflow

This is the core workflow for processing and classifying emails:

```
1. CLIENT REQUEST
   └─> Frontend/Electron: User requests email list
       │
2. API LAYER
   └─> backend/api/emails.py: get_emails() endpoint
       │
3. EMAIL RETRIEVAL
   ├─> source="outlook": COMEmailProvider.get_emails()
   │   └─> OutlookEmailAdapter → OutlookManager → Outlook COM
   │
   └─> source="database": Query SQLite for classified emails
       │
4. AI CLASSIFICATION (if needed)
   └─> AIService.classify_email()
       └─> AIOrchestrator.classify_email_with_confidence()
           ├─> PromptExecutor.execute_prompty()
           │   └─> Azure OpenAI API (GPT-4o)
           │
           ├─> ClassificationEngine.parse_classification_response()
           │   └─> Validates category and confidence
           │
           └─> Returns: {category, confidence, reasoning}
       │
5. DATABASE PERSISTENCE
   └─> EmailSyncService.sync_email_to_database()
       └─> Stores email + AI metadata in SQLite
       │
6. RESPONSE
   └─> Returns EmailListResponse with classified emails
       └─> Frontend displays categorized emails
```

### Task Extraction Workflow

Extracts actionable tasks from emails:

```
1. EMAIL CLASSIFICATION COMPLETE
   └─> Category: "Action Required" or "Urgent Response"
       │
2. TASK EXTRACTION TRIGGERED
   └─> EmailTaskExtractionService.extract_tasks_from_email()
       │
3. AI EXTRACTION
   └─> AIOrchestrator.extract_action_items()
       ├─> PromptExecutor.execute_prompty("summerize_action_item")
       │   └─> Azure OpenAI extracts tasks with deadlines
       │
       └─> Returns: [{"task": "...", "deadline": "..."}, ...]
       │
4. TASK CREATION
   └─> TaskService.create_task_from_email()
       └─> Stores tasks with email_id linkage
       │
5. NOTIFICATION
   └─> WebSocketManager.broadcast_task_created()
       └─> Real-time frontend update
```

### Deduplication Workflow

Prevents duplicate task/email entries:

```
1. NEW EMAIL CLASSIFIED
   └─> Check if email already processed
       │
2. CONTENT DEDUPLICATION
   └─> AnalysisEngine.detect_duplicates()
       ├─> Compares subject, sender, date
       ├─> AI-powered content similarity check
       └─> Returns duplicate_ids[]
       │
3. ACTION ITEM DEDUPLICATION
   └─> AnalysisEngine.deduplicate_action_items()
       ├─> Compares task descriptions
       ├─> AI semantic similarity matching
       └─> Merges or flags duplicates
       │
4. SKIP OR MERGE
   └─> If duplicate: Update existing entry
   └─> If unique: Create new entry
```

## Component Details

### Backend API Layer

**Purpose**: RESTful API for all client applications

**Technology**: FastAPI with async/await support

**Key Endpoints**:
- `/api/emails` - Email operations (list, get, move, mark read)
- `/api/ai` - AI processing (classify, summarize, extract tasks)
- `/api/tasks` - Task management (CRUD operations)
- `/api/processing` - Batch processing workflows
- `/api/settings` - Application configuration
- `/health` - Health check and diagnostics

**Features**:
- JWT authentication (optional, disabled for localhost)
- CORS support for web/Electron clients
- WebSocket support for real-time updates
- Comprehensive error handling with HTTP status codes
- Request validation with Pydantic models

**Configuration**: `backend/core/config.py` with `.env` overrides

### Service Layer

**Purpose**: Business logic implementation with dependency injection

**Key Services**:

#### EmailProcessingService
- **Responsibility**: Coordinates email processing workflows
- **Dependencies**: AIService, EmailProvider, TaskService
- **Delegates to**:
  - `EmailSyncService` - Database operations
  - `EmailClassificationService` - AI classification
  - `EmailTaskExtractionService` - Task extraction
  - `EmailAccuracyService` - Accuracy tracking

#### AIService
- **Responsibility**: AI processing coordination for FastAPI
- **Dependencies**: AIOrchestrator (business logic)
- **Methods**:
  - `classify_email()` - Categorizes emails
  - `extract_action_items()` - Extracts tasks
  - `generate_summary()` - Creates summaries
  - `analyze_inbox()` - Holistic inbox analysis

#### COMEmailProvider
- **Responsibility**: Outlook COM integration
- **Implements**: EmailProvider interface
- **Thread Safety**: Uses dedicated COM thread with queue-based operations
- **Methods**:
  - `get_emails()` - Retrieves emails from Outlook
  - `get_email_content()` - Full email content
  - `move_email()` - Folder operations
  - `mark_as_read()` - Update read status

#### TaskService
- **Responsibility**: Task management and persistence
- **Dependencies**: TaskPersistence, DatabaseManager
- **Methods**:
  - `create_task()` - Creates new tasks
  - `get_tasks()` - Retrieves tasks with filtering
  - `update_task()` - Updates task status/details
  - `delete_task()` - Removes tasks

### Business Logic Engines

**Purpose**: Pure business logic without framework dependencies

**Location**: `backend/core/business/`

**Key Engines**:

#### AIOrchestrator
- **Responsibility**: Coordinates all AI operations
- **Pure Python**: No async, no FastAPI dependencies
- **Delegates to**:
  - `PromptExecutor` - Executes .prompty templates
  - `ClassificationEngine` - Email categorization
  - `ExtractionEngine` - Summary/task extraction
  - `AnalysisEngine` - Deduplication and analysis
  - `UserContextManager` - User context management

#### ClassificationEngine
- **Responsibility**: Email categorization with confidence scoring
- **Categories**: Action Required, Urgent Response, FYI, Newsletter, etc.
- **Confidence Thresholds**:
  - HIGH: ≥ 0.85
  - MEDIUM: 0.60 - 0.84
  - LOW: < 0.60

#### ExtractionEngine
- **Responsibility**: Extracts summaries and action items
- **Methods**:
  - `generate_one_line_summary()` - Brief email summary
  - `extract_action_items()` - Actionable tasks with deadlines
  - `summarize_fyi()` - FYI email summaries

#### AnalysisEngine
- **Responsibility**: Advanced email analysis
- **Methods**:
  - `detect_duplicates()` - Content-based duplicate detection
  - `deduplicate_action_items()` - Task deduplication
  - `analyze_inbox_holistic()` - Comprehensive inbox analysis

### Frontend Applications

#### React Web Application

**Technology**: React 19 + TypeScript + Vite

**State Management**: Redux Toolkit + RTK Query

**Key Features**:
- Dashboard with email/task statistics
- Paginated email list with filtering
- Task management with Kanban board
- Real-time updates via WebSocket
- Responsive design for mobile/desktop

**API Integration**: RTK Query services in `frontend/src/services/`

#### Electron Desktop Application

**Technology**: Electron with React frontend

**Features**:
- Native desktop window
- Automatic backend/frontend startup
- System tray integration
- Keyboard shortcuts

**Startup**: `electron/start-app.ps1` launches all components

#### Legacy Tkinter Desktop Application

**Status**: Being phased out in favor of web/Electron

**Location**: `src/unified_gui.py`

**Still Used For**: Direct Outlook integration in some workflows

### Database Layer

**Technology**: SQLite with connection pooling

**Location**: `runtime_data/database/email_helper_history.db`

**Key Tables**:
- `emails` - Classified emails with AI metadata
- `tasks` - Extracted action items
- `user_feedback` - AI learning data
- `accuracy_metrics` - Classification accuracy tracking

**Connection Management**: `backend/database/connection.py`

**Thread Safety**: Connection pooling with context managers

### External Integrations

#### Microsoft Outlook (COM Interface)

**Technology**: `win32com.client` (pywin32)

**Adapter**: `src/adapters/outlook_email_adapter.py`

**Thread Safety**: Dedicated COM thread to avoid apartment issues

**Limitations**: Windows-only, requires Outlook installed

**Alternative**: Microsoft Graph API (future implementation)

#### Azure OpenAI

**Model**: GPT-4o

**Configuration**: `backend/core/infrastructure/azure_config.py`

**Authentication**:
1. Azure CLI (`az login`) - preferred
2. Environment variables - fallback

**Prompt Templates**: `.prompty` files in `prompts/` directory

**Rate Limiting**: Built-in retry logic with exponential backoff

## Design Patterns

### Dependency Injection

**Purpose**: Testability and loose coupling

**Pattern**: Constructor injection with interface-based design

**Example**:
```python
class EmailProcessingService:
    def __init__(
        self,
        ai_service: AIService,
        email_provider: EmailProvider,
        task_service: TaskService
    ):
        self.ai_service = ai_service
        self.email_provider = email_provider
        self.task_service = task_service
```

**Benefits**:
- Easy to mock for testing
- Swappable implementations
- Clear dependency graph

**See**: `docs/technical/DEPENDENCY_INJECTION.md`

### Service Layer Pattern

**Purpose**: Separation of concerns between API and business logic

**Structure**:
```
API Layer → Service Layer → Business Logic → Data Access
```

**Example**:
- `backend/api/emails.py` (API)
  → `EmailProcessingService` (Service)
    → `AIOrchestrator` (Business Logic)
      → `database/connection.py` (Data Access)

### Facade Pattern

**Purpose**: Simplified interface to complex subsystems

**Example**: `AIOrchestrator` provides unified API for multiple engines

```python
# Simple facade call
orchestrator.classify_email_with_confidence(email_text)

# Internally coordinates:
# - PromptExecutor
# - ClassificationEngine  
# - UserContextManager
# - Accuracy tracking
```

### Repository Pattern

**Purpose**: Abstract data access logic

**Implementation**:
- `EmailSyncService` - Email data access
- `TaskService` - Task data access
- `DatabaseManager` - Connection management

### Factory Pattern

**Purpose**: Service instance creation

**Implementation**: `ServiceFactory` in `src/core/service_factory.py`

**Usage**:
```python
factory = ServiceFactory()
outlook_manager = factory.get_outlook_manager()
task_persistence = factory.get_task_persistence()
```

## Configuration Management

### Environment Variables

**Files**:
- `.env` - Backend configuration (not in git)
- `.env.localhost.example` - Backend template
- `frontend/.env.local` - Frontend configuration (not in git)
- `frontend/.env.local.example` - Frontend template

**Key Settings**:

**Backend**:
```bash
USE_COM_BACKEND=true              # Use Outlook COM
EMAIL_PROVIDER=com                # COM provider
DEBUG=true                        # Enable debug logging
REQUIRE_AUTHENTICATION=false      # Skip auth for development
DATABASE_URL=sqlite:///./runtime_data/email_helper_history.db
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

**Frontend**:
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_DEBUG_LOGGING=true
```

### User Configuration

**Location**: `user_specific_data/` (not in git)

**Files**:
- `job_summery.md` - Job role and responsibilities
- `job_skill_summery.md` - Technical skills
- `username.txt` - User identifier
- `custom_interests.md` - Personal interests for classification

**Purpose**: Personalizes AI classification based on user context

## Security Considerations

### Authentication

**Current**: Optional JWT-based authentication

**Development**: `REQUIRE_AUTHENTICATION=false` for localhost

**Production**: JWT tokens with access/refresh token flow

### Data Privacy

**Sensitive Data**:
- Email content stored locally (SQLite)
- User configuration excluded from git (`.gitignore`)
- Azure credentials via CLI or environment variables

**No External Storage**: All data kept local except Azure OpenAI API calls

### COM Security

**Thread Safety**: Dedicated COM thread prevents apartment violations

**Error Handling**: Graceful fallback on COM failures

### CORS

**Development**: Allow all origins (`["*"]`)

**Production**: Restrict to specific frontend domains

## Testing Strategy

### Test Organization

```
backend/tests/          # Backend API/service tests
frontend/tests/         # Frontend unit/E2E tests
  ├── unit/            # Component/reducer tests (Vitest)
  └── e2e/             # End-to-end tests (Playwright)
```

### Test Execution

**All Tests**:
```bash
npm test
# OR
.\run-all-tests.ps1
```

**Individual Suites**:
```bash
npm run test:backend      # Backend Python tests
npm run test:frontend     # Frontend unit tests
npm run test:e2e          # Frontend E2E tests
npm run test:coverage     # All tests with coverage
```

### Mock Services

**Location**: `src/core/mock_services.py`

**Purpose**: Testing without real Outlook/Azure dependencies

**Critical Rule**: ❌ **NEVER use mocks in production code**

Mocks are ONLY for test files. Production code must fail fast with clear errors when dependencies are unavailable.

### Integration Testing

**Backend**: Tests with real database, mock Outlook/Azure

**Frontend**: Tests with mock backend API responses

**E2E**: Playwright tests with real backend + mock email data

## Performance Considerations

### Email Retrieval

- **Pagination**: 50 emails per request (configurable up to 50,000)
- **Caching**: SQLite stores classified emails
- **Lazy Loading**: Frontend loads emails on-demand

### AI Processing

- **Rate Limiting**: Built-in retry with exponential backoff
- **Batch Processing**: Process multiple emails in background
- **Confidence Caching**: Skip re-classification of high-confidence emails

### Database Optimization

- **Connection Pooling**: Reuse connections efficiently
- **Indexes**: On frequently queried fields (email_id, category, date)
- **Batch Inserts**: Bulk operations for multiple emails

### Frontend Optimization

- **Code Splitting**: Lazy load routes
- **RTK Query Caching**: Automatic caching of API responses
- **WebSocket**: Real-time updates without polling

## Deployment Architecture

### Development (Localhost)

```
┌─────────────────────┐
│  Electron App       │
│  http://localhost   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐     ┌─────────────────┐
│  React Frontend     │────▶│  FastAPI        │
│  Port 3000          │     │  Backend        │
└─────────────────────┘     │  Port 8000      │
                            └────────┬─────────┘
                                     │
                          ┌──────────┼──────────┐
                          ▼          ▼          ▼
                    ┌─────────┐ ┌────────┐ ┌─────────┐
                    │ Outlook │ │ SQLite │ │ Azure   │
                    │ (COM)   │ │   DB   │ │ OpenAI  │
                    └─────────┘ └────────┘ └─────────┘
```

### Production (Future)

```
┌─────────────────────┐
│  Electron App       │
│  (Installed)        │
└──────────┬──────────┘
           │
┌──────────▼──────────┐     ┌─────────────────┐
│  React Frontend     │────▶│  FastAPI        │
│  (Built Bundle)     │     │  Backend        │
└─────────────────────┘     │  (Local Service)│
                            └────────┬─────────┘
                                     │
                          ┌──────────┼──────────┐
                          ▼          ▼          ▼
                    ┌─────────┐ ┌────────┐ ┌─────────┐
                    │ Outlook │ │ SQLite │ │ Azure   │
                    │ (COM)   │ │   DB   │ │ OpenAI  │
                    └─────────┘ └────────┘ └─────────┘
```

## Key Architectural Decisions

### Why FastAPI?

- Async support for concurrent requests
- Automatic OpenAPI documentation
- Pydantic validation
- Easy WebSocket integration
- Modern Python 3.12+ features

### Why React + Redux Toolkit?

- Component reusability
- Type safety with TypeScript
- RTK Query eliminates manual API state management
- Large ecosystem and tooling

### Why Electron?

- Cross-platform desktop deployment
- Native system integration
- Reuses web frontend (DRY principle)
- Auto-update capabilities

### Why SQLite?

- No server setup required
- File-based (easy backups)
- Sufficient performance for single-user app
- Built-in Python support

### Why Azure OpenAI?

- Enterprise-grade reliability
- Better privacy than OpenAI API
- Integration with Azure ecosystem
- Cost control features

### Why COM Instead of Graph API?

**Current**: COM for simplicity and immediate access

**Future**: Will add Graph API support for:
- Cloud email access
- Cross-platform support
- Modern API design

## Migration Path

### Legacy → Modern Architecture

**Phase 1** (Current):
- ✅ FastAPI backend operational
- ✅ React frontend with full features
- ✅ Electron desktop app
- ⚠️ Legacy Tkinter GUI still present

**Phase 2** (In Progress):
- 🚧 Deprecate Tkinter GUI
- 🚧 Move all AI logic to `backend/core/business/`
- 🚧 Complete test coverage

**Phase 3** (Future):
- 📋 Add Microsoft Graph API support
- 📋 Cloud deployment option
- 📋 Mobile app development
- 📋 Multi-user support

## Common Workflows

### Adding a New API Endpoint

1. **Define Pydantic models**: `backend/models/`
2. **Implement endpoint**: `backend/api/`
3. **Add service logic**: `backend/services/`
4. **Add business logic**: `backend/core/business/` (if needed)
5. **Write tests**: `backend/tests/`
6. **Add frontend integration**: `frontend/src/services/`
7. **Update documentation**

### Adding a New AI Prompt

1. **Create .prompty file**: `prompts/new_prompt.prompty`
2. **Add to AIOrchestrator**: Add method to appropriate engine
3. **Add API endpoint**: Expose via `backend/api/ai.py`
4. **Add service method**: `backend/services/ai_service.py`
5. **Write tests**: `backend/tests/test_ai_service.py`
6. **Document**: Update this file and feature docs

### Adding a New Service

1. **Define interface**: (optional) in `src/core/interfaces.py`
2. **Implement service**: `backend/services/new_service.py`
3. **Add dependency injection**: Update `backend/core/dependencies.py`
4. **Write unit tests**: `backend/tests/test_new_service.py`
5. **Integrate with API**: Use in endpoint handlers
6. **Document dependencies**: Update this file

## Troubleshooting

### Backend Won't Start

- Check `.env` configuration
- Verify port 8000 is free
- Check Outlook is installed (if using COM)
- Review logs in `runtime_data/logs/`

### COM Connection Errors

- Ensure Outlook is installed and configured
- Try opening Outlook manually first
- Run with administrator privileges
- Check Windows Event Viewer for COM errors

### Frontend Can't Connect

- Verify backend running at http://localhost:8000
- Check `.env.local` has correct `VITE_API_BASE_URL`
- Verify CORS origins in backend config
- Check browser console for errors

### AI Processing Errors

- Verify Azure OpenAI credentials
- Check API quota and rate limits
- Review prompt template syntax
- Check content filter violations

## Related Documentation

- **[COM Integration](./COM_EMAIL_PROVIDER.md)** - Outlook COM details
- **[Dependency Injection](./DEPENDENCY_INJECTION.md)** - DI patterns
- **[Error Handling](./ERROR_HANDLING.md)** - Error handling strategies
- **[Testing Guide](./TESTING.md)** - Testing strategies
- **[Troubleshooting](../TROUBLESHOOTING.md)** - Common issues

## Contributing

When modifying architecture:

1. **Update this document** - Keep architecture docs current
2. **Follow existing patterns** - Maintain consistency
3. **Write tests** - Ensure coverage for new components
4. **Document decisions** - Explain why, not just what
5. **Consider migration** - Don't break existing functionality

---

**Last Updated**: October 31, 2025  
**Version**: 1.0.0  
**Maintainer**: Email Helper Development Team
