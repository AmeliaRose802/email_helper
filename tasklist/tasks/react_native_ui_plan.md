# Web App Conversion Plan - AI Agent Parallel Execution

**Project:** Email Helper Web Application MVP  
**Timeline:** 4-5 weeks (AI-accelerated development)  
**Approach:** Parallel agent execution with conflict-aware task grouping  
**Architecture:** FastAPI backend + React web frontend

## Summary

- **Feature:** Convert Tkinter desktop app to modern web application with cloud backend
- **In scope:** Core email processing, AI classification, task management, responsive web UI
- **Out of scope:** Advanced reporting, multi-user support, desktop app parity

## Repo Forecast

- **Likely components/dirs:** `backend/`, `frontend/`, `shared/`, `deployment/`
- **Predicted file touches (with rationale):**
  - `backend/api/*.py` — FastAPI REST endpoints (already complete)
  - `backend/services/*.py` — Refactored business logic services (already complete)
  - `frontend/src/pages/*.tsx` — React web pages and components
  - `frontend/src/services/*.ts` — API client and state management
  - `shared/types/*.ts` — Shared TypeScript interfaces
- **Related tests:** `backend/tests/`, `frontend/__tests__/`
- **CI jobs:** `lint`, `typecheck`, `test-backend`, `test-frontend`, `build-frontend`
- **CODEOWNERS:** `backend/` → `@backend-agents`, `frontend/` → `@frontend-agents`

## Tasks

- **T1. Backend API Foundation** — _Purpose:_ Create FastAPI server with core services
  - **Acceptance criteria:**
    - FastAPI app with Pydantic models running on port 8000
    - JWT authentication endpoints functional
    - Database connection established (SQLite → PostgreSQL migration)
    - Health check endpoint returns 200 OK
  - **Predicted file touches:** `backend/main.py`, `backend/api/auth.py`, `backend/models/*.py`
  - **Risk:** Low
  - **Surface:** safe-isolated
  - **Owner hints:** backend
  - **GitHub artifacts:**
    - **Branch:** `feat/api-foundation-t1`
    - **PR title:** `[feat] API: FastAPI foundation with auth`
    - **Labels:** `feat`, `backend`, `api`
    - **Issue body:** Setup FastAPI server with authentication, database, and core API structure

- **T2. Email Service Interface** — _Purpose:_ Create REST API endpoints for email operations using Microsoft Graph API
  - **Acceptance criteria:**
    - FastAPI router with email endpoints (`/api/emails/*`) implemented
    - Microsoft Graph API client integration with OAuth authentication
    - GET `/api/emails` endpoint returns paginated email list
    - GET `/api/emails/{id}` endpoint returns detailed email content
    - Email data follows existing Pydantic models in `backend/models/email.py`
    - Integration with existing ServiceFactory pattern for email provider abstraction
  - **Predicted file touches:** `backend/api/emails.py`, `backend/services/graph_email_service.py`, `backend/clients/graph_client.py`
  - **Risk:** Medium
  - **Surface:** safe-isolated
  - **Owner hints:** backend
  - **GitHub artifacts:**
    - **Branch:** `feat/email-service-t2`
    - **PR title:** `[feat] API: Email endpoints with Microsoft Graph integration`
    - **Labels:** `feat`, `backend`, `integration`
    - **Issue body:** Implement email REST API endpoints using Microsoft Graph API and existing email models

- **T3. AI Processing API** — _Purpose:_ Create REST API endpoints for AI email classification using existing AIProcessor
  - **Acceptance criteria:**
    - FastAPI router with AI endpoints (`/api/ai/*`) implemented
    - POST `/api/ai/classify` endpoint accepts email content and returns classification
    - POST `/api/ai/analyze-batch` endpoint for multiple email analysis
    - Integration with existing `AIProcessor` from `src/ai_processor.py` via ServiceFactory
    - Prompty templates from `prompts/` directory properly loaded and functional
    - Azure OpenAI configuration using existing `backend/core/config.py` settings
    - Response follows Pydantic models in `backend/models/email.py` (`EmailClassification`)
    - Error handling for AI service unavailability with fallback responses
  - **Predicted file touches:** `backend/api/ai.py`, `backend/services/ai_service_adapter.py`
  - **Risk:** Low
  - **Surface:** safe-isolated
  - **Owner hints:** backend
  - **GitHub artifacts:**
    - **Branch:** `feat/ai-api-t3`
    - **PR title:** `[feat] API: AI classification endpoints with existing processor integration`
    - **Labels:** `feat`, `backend`, `ai`
    - **Issue body:** Implement AI REST API endpoints leveraging existing AIProcessor and prompty templates

- **T4. Task Management API** — _Purpose:_ Create REST API endpoints for task CRUD operations using existing task persistence
  - **Acceptance criteria:**
    - FastAPI router with task endpoints (`/api/tasks/*`) implemented
    - GET `/api/tasks` endpoint with pagination, filtering by status/priority/category
    - GET `/api/tasks/{id}` endpoint for individual task details
    - POST `/api/tasks` endpoint for creating new tasks
    - PUT `/api/tasks/{id}` endpoint for updating existing tasks
    - DELETE `/api/tasks/{id}` endpoint for task deletion
    - Integration with existing `TaskPersistence` from `src/task_persistence.py` via ServiceFactory
    - Task data follows existing Pydantic models in `backend/models/task.py`
    - Tasks properly linked to source emails via `email_id` field
    - Support for task status transitions (pending → in_progress → completed)
    - Database operations use existing SQLite schema from `backend/database/connection.py`
  - **Predicted file touches:** `backend/api/tasks.py`, `backend/services/task_service_adapter.py`
  - **Risk:** Low
  - **Surface:** safe-isolated
  - **Owner hints:** backend
  - **GitHub artifacts:**
    - **Branch:** `feat/task-api-t4`
    - **PR title:** `[feat] API: Task management CRUD endpoints with persistence integration`
    - **Labels:** `feat`, `backend`, `tasks`
    - **Issue body:** Implement complete task management REST API using existing TaskPersistence and database schema

- **T5. React Web App Setup** — _Purpose:_ Initialize modern web application with routing and state management
  - **Acceptance criteria:**
    - React web app runs in browser with hot reload
    - TypeScript configured with strict mode
    - React Router for client-side navigation
    - Redux Toolkit with RTK Query for API calls
    - Responsive design with Tailwind CSS or Material-UI
    - Vite for fast development and building
  - **Predicted file touches:** `frontend/package.json`, `frontend/src/router/`, `frontend/src/store/`
  - **Risk:** Low
  - **Surface:** safe-isolated
  - **Owner hints:** frontend
  - **GitHub artifacts:**
    - **Branch:** `feat/web-setup-t5`
    - **PR title:** `[feat] Web: React web application initialization`
    - **Labels:** `feat`, `frontend`, `setup`
    - **Issue body:** Set up React web app with TypeScript, routing, and state management

- **T6. Authentication Flow** — _Purpose:_ Login/logout with secure token storage for web
  - **Acceptance criteria:**
    - Login page with email/password fields and validation
    - JWT tokens stored securely in localStorage/sessionStorage
    - Auth state persists across browser sessions
    - Logout clears all stored credentials and redirects to login
    - Protected routes redirect to login when unauthenticated
  - **Predicted file touches:** `frontend/src/pages/LoginPage.tsx`, `frontend/src/services/auth.ts`
  - **Risk:** Medium
  - **Surface:** safe-isolated
  - **Owner hints:** frontend
  - **GitHub artifacts:**
    - **Branch:** `feat/auth-flow-t6`
    - **PR title:** `[feat] Web: Authentication flow with secure storage`
    - **Labels:** `feat`, `frontend`, `auth`
    - **Issue body:** Implement secure web authentication flow with token storage

- **T7. Email List Interface** — _Purpose:_ Display and manage emails in responsive web UI
  - **Acceptance criteria:**
    - Email list with virtual scrolling for performance
    - Hover actions and context menus for quick actions (archive, delete)
    - Refresh button and auto-refresh triggers email sync
    - Search bar and category filtering functional
    - Responsive design works on desktop and tablet
  - **Predicted file touches:** `frontend/src/pages/EmailListPage.tsx`, `frontend/src/components/EmailItem.tsx`
  - **Risk:** Medium
  - **Surface:** safe-isolated
  - **Owner hints:** frontend
  - **GitHub artifacts:**
    - **Branch:** `feat/email-list-t7`
    - **PR title:** `[feat] Web: Email list with actions and filtering`
    - **Labels:** `feat`, `frontend`, `ui`
    - **Issue body:** Create responsive email list interface with web-optimized interactions

- **T8. Task Management Interface** — _Purpose:_ Web-based task management with rich interactions
  - **Acceptance criteria:**
    - Task list with drag-and-drop reordering and bulk actions
    - Task creation modal/form from email actions and standalone
    - Date picker component and priority selection dropdown
    - Advanced filtering by status, category, due date, and priority
    - Keyboard shortcuts for power users
  - **Predicted file touches:** `frontend/src/pages/TaskPage.tsx`, `frontend/src/components/TaskItem.tsx`
  - **Risk:** Medium
  - **Surface:** safe-isolated
  - **Owner hints:** frontend
  - **GitHub artifacts:**
    - **Branch:** `feat/task-ui-t8`
    - **PR title:** `[feat] Web: Task management interface`
    - **Labels:** `feat`, `frontend`, `tasks`
    - **Issue body:** Build comprehensive web task management with rich interactions

- **T9. Email Processing Pipeline** — _Purpose:_ Background email processing with real-time updates
  - **Acceptance criteria:**
    - Background job queue processes emails
    - WebSocket updates for processing status
    - Job cancellation and retry logic
    - Processing history and error handling
  - **Predicted file touches:** `backend/workers/email_processor.py`, `backend/websockets/status.py`
  - **Risk:** High
  - **Surface:** shared-surface
  - **Owner hints:** backend
  - **GitHub artifacts:**
    - **Branch:** `feat/email-processing-t9`
    - **PR title:** `[feat] API: Background email processing pipeline`
    - **Labels:** `feat`, `backend`, `processing`
    - **Issue body:** Implement background processing with WebSocket status updates

- **T10. Deployment Configuration** — _Purpose:_ Docker and cloud deployment setup
  - **Acceptance criteria:**
    - Docker containers for backend and database
    - Docker Compose for local development
    - Cloud deployment configuration (Railway/Render)
    - Environment variable management
  - **Predicted file touches:** `Dockerfile`, `docker-compose.yml`, `deployment/`
  - **Risk:** Medium
  - **Surface:** safe-isolated
  - **Owner hints:** devops
  - **GitHub artifacts:**
    - **Branch:** `feat/deployment-t10`
    - **PR title:** `[feat] Deploy: Docker containerization and cloud setup`
    - **Labels:** `feat`, `deployment`, `docker`
    - **Issue body:** Set up containerization and cloud deployment infrastructure

## Dependencies (DAG)

- ✅ `T1 → T2` — Email service needs API foundation (COMPLETE)
- ✅ `T1 → T3` — AI service needs API foundation (COMPLETE)  
- ✅ `T1 → T4` — Task API needs API foundation (COMPLETE)
- `T2 → T9` — Email processing needs email service
- `T3 → T9` — Email processing needs AI service
- `T5 → T6` — Auth flow needs web app setup
- `T5 → T7` — Email UI needs web app setup  
- `T5 → T8` — Task UI needs web app setup

## Parallel Blocks

- **Block A - Backend Foundation** _(COMPLETE ✅)_
  - **Rationale:** Core API services with minimal shared dependencies
  - **Tasks:** ✅ `T1`, `T2`, `T3`, `T4` (T1 completed first, then T2-T4 completed in parallel)
  - **Notes:** All backend APIs are now functional and ready for web frontend

- **Block B - Web App Foundation** _(ready to start)_
  - **Rationale:** Web app setup independent of backend details
  - **Tasks:** `T5`, `T6`, `T7`, `T8` (T5 must complete first, then T6-T8 in parallel)
  - **Notes:** T5 creates React web foundation, then web components can be built simultaneously

- **Block C - Integration Layer** _(depends on Blocks A+B; conflict risk: Medium)_
  - **Rationale:** Requires both backend and frontend to be functional
  - **Tasks:** `T9` (background processing with WebSocket integration)
  - **Notes:** Needs API and mobile app basics complete

- **Block D - Deployment** _(run in parallel with Block C; conflict risk: Low)_
  - **Rationale:** Infrastructure setup independent of application logic
  - **Tasks:** `T10` (Docker and cloud deployment configuration)
  - **Notes:** Can be prepared while integration work happens

## Scheduling Plan

- **Completed:** ✅ `T1` (API Foundation), ✅ `T2`, ✅ `T3`, ✅ `T4` (Backend complete)
- **Ready to start:** `T5` (Web App Setup), `T10` (Deployment Config)
- **Gated tasks:** 
  - `T6`, `T7`, `T8` (depends on `T5`, gate: Web app foundation)
  - `T9` (depends on `T2`, `T3`, gate: email and AI services - ready to start)
- **Agent allocation:** 
  - Block A (COMPLETE ✅): T1-T4 backend APIs functional
  - Block B (ready): 2 agents for T5 setup, then split T6-T8 components
  - Block C (ready): 1 agent for T9 integration work (backend ready)
  - Block D (ready): 1 agent for T10 deployment

## Risks & Mitigations

- **Risk:** Microsoft Graph API integration complexity → **Mitigation:** Start with read-only access, test early with sample data
- **Risk:** Real-time WebSocket updates performance → **Mitigation:** Implement polling fallback, optimize message frequency
- **Risk:** Mobile app store approval delays → **Mitigation:** Submit early beta versions, prepare for review feedback
- **Risk:** Data migration from desktop app → **Mitigation:** Create export tools early, test with sample user data

## Technology Stack (MVP-Focused)

### Backend
- **FastAPI** (Python) - Leverages existing codebase
- **SQLite → PostgreSQL** - Simple migration path
- **Redis** - Background jobs and caching
- **Microsoft Graph API** - Replace Outlook COM

### Frontend  
- **React** with **TypeScript** - Modern web framework
- **Vite** - Fast build tool and dev server
- **Redux Toolkit + RTK Query** - State and API management
- **React Router** - Web app navigation
- **Tailwind CSS** or **Material-UI** - Responsive styling

### Deployment
- **Docker** containers for backend
- **Railway/Render** for quick cloud deployment
- **Vercel/Netlify** for web app deployment (static hosting)

## Timeline Summary

| Week | Block A (Backend) | Block B (Web App) | Block C (Integration) | Block D (Deploy) |
|------|------------------|------------------|---------------------|------------------|
| **1** | ✅ T1: API Foundation | T5: Web App Setup | - | T10: Docker Config |
| **2** | ✅ T2,T3,T4: Services | T6,T7,T8: Web Components | T9: Integration | Continue T10 |
| **3** | ✅ COMPLETE | Continue T6-T8 | Continue T9 | Deploy staging |
| **4** | ✅ COMPLETE | Testing & Polish | Testing | Deploy production |
| **5** | ✅ COMPLETE | Bug fixes | Bug fixes | User migration |
| **6** | ✅ **COMPLETE** | **MVP COMPLETE** | **MVP COMPLETE** | **MVP COMPLETE** |

**Total Duration: 6 weeks for fully functional MVP**

## Success Metrics

- **Week 1:** ✅ Backend API serves email data (COMPLETE)
- **Week 2:** Web app displays emails, Authentication working
- **Week 4:** End-to-end email processing working, Task management functional  
- **Week 6:** Production deployment, first users migrated from desktop app

**Next Steps:** Begin T1, T5, T10 in parallel with 3 different agents immediately

## GitHub Artifacts

### Issues Created for Each Task

**T1 - Backend API Foundation**
```markdown
**Goal:** Create FastAPI server with authentication and database setup
**Acceptance:** FastAPI app running on port 8000, JWT auth working, database connected
**Implementation:** Use existing ServiceFactory pattern, convert to FastAPI dependencies
**Test Plan:** Health check endpoint, auth token generation/validation, database queries
**Risks/Rollback:** Minimal - isolated foundation work, easy to revert
```

**T2 - Email Service Interface**  
```markdown
**Goal:** Replace Outlook COM with Microsoft Graph API integration
**Acceptance:** Can authenticate and fetch 10 emails from test inbox via Graph API
**Implementation:** Abstract EmailProvider interface, Graph API client implementation
**Test Plan:** Auth flow, email fetching, data normalization tests
**Risks/Rollback:** Medium - Graph API complexity, fallback to original COM if needed
```

*[Similar detailed issue bodies for T3-T10...]*

## Execution Instructions for AI Agents

### Agent Assignment Strategy
- **Backend Agent 1:** Takes T1 (foundation), then leads T2-T4 coordination
- **Frontend Agent 1:** Takes T5 (RN setup), then leads T6-T8 coordination  
- **Integration Agent:** Takes T9 (requires backend+frontend completion)
- **DevOps Agent:** Takes T10 (can run parallel with all other work)

### Daily Standups (Async)
- **Day 1:** T1, T5, T10 kickoff status updates
- **Day 3:** T1 completion confirmation, T2-T4 parallel start
- **Day 5:** T5 completion confirmation, T6-T8 parallel start
- **Week 2:** Integration readiness assessment for T9
- **Week 4:** MVP feature complete, deployment readiness check

### Success Gates
- **Week 1:** ✅ API foundation serving health checks, Web app building successfully
- **Week 2:** Email data flowing through API, Mobile screens displaying sample data  
- **Week 3:** Full email processing pipeline, Task management UI functional
- **Week 4:** End-to-end integration, WebSocket real-time updates working
- **Week 5:** Production deployment, performance optimization
- **Week 6:** User migration tools, first production users

---

**READY FOR IMMEDIATE EXECUTION**
**Agents can start T1, T5, T10 in parallel NOW** 
**Expected MVP delivery: 6 weeks from start**
