# React Native Conversion Plan - AI Agent Parallel Execution

**Project:** Email Helper React Native MVP  
**Timeline:** 6 weeks (AI-accelerated development)  
**Approach:** Parallel agent execution with conflict-aware task grouping  
**Architecture:** FastAPI backend + React Native frontend

## Summary

- **Feature:** Convert Tkinter desktop app to React Native mobile app with cloud backend
- **In scope:** Core email processing, AI classification, task management, mobile UI
- **Out of scope:** Advanced reporting, multi-user support, desktop app parity

## Repo Forecast

- **Likely components/dirs:** `backend/`, `mobile/`, `shared/`, `deployment/`
- **Predicted file touches (with rationale):**
  - `backend/api/*.py` — FastAPI REST endpoints
  - `backend/services/*.py` — Refactored business logic services
  - `mobile/src/screens/*.tsx` — React Native UI screens
  - `mobile/src/services/*.ts` — API client and state management
  - `shared/types/*.ts` — Shared TypeScript interfaces
- **Related tests:** `backend/tests/`, `mobile/__tests__/`
- **CI jobs:** `lint`, `typecheck`, `test-backend`, `test-mobile`, `build-mobile`
- **CODEOWNERS:** `backend/` → `@backend-agents`, `mobile/` → `@frontend-agents`

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

- **T5. React Native Project Setup** — _Purpose:_ Initialize mobile app with navigation and state
  - **Acceptance criteria:**
    - React Native app runs on iOS/Android simulators
    - TypeScript configured with strict mode
    - React Navigation with tab/stack navigation
    - Redux Toolkit with RTK Query for API calls
  - **Predicted file touches:** `mobile/package.json`, `mobile/src/navigation/`, `mobile/src/store/`
  - **Risk:** Low
  - **Surface:** safe-isolated
  - **Owner hints:** frontend
  - **GitHub artifacts:**
    - **Branch:** `feat/rn-setup-t5`
    - **PR title:** `[feat] Mobile: React Native project initialization`
    - **Labels:** `feat`, `mobile`, `setup`
    - **Issue body:** Set up React Native project with TypeScript, navigation, and state management

- **T6. Authentication Flow** — _Purpose:_ Login/logout with secure token storage
  - **Acceptance criteria:**
    - Login screen with email/password fields
    - JWT tokens stored securely in Keychain/Keystore
    - Auth state persists across app restarts
    - Logout clears all stored credentials
  - **Predicted file touches:** `mobile/src/screens/AuthScreen.tsx`, `mobile/src/services/auth.ts`
  - **Risk:** Medium
  - **Surface:** safe-isolated
  - **Owner hints:** frontend
  - **GitHub artifacts:**
    - **Branch:** `feat/auth-flow-t6`
    - **PR title:** `[feat] Mobile: Authentication flow with secure storage`
    - **Labels:** `feat`, `mobile`, `auth`
    - **Issue body:** Implement secure authentication flow with token storage

- **T7. Email List Interface** — _Purpose:_ Display and manage emails in mobile UI
  - **Acceptance criteria:**
    - FlatList shows emails with infinite scroll
    - Swipe gestures for quick actions (archive, delete)
    - Pull-to-refresh triggers email sync
    - Search and category filtering functional
  - **Predicted file touches:** `mobile/src/screens/EmailListScreen.tsx`, `mobile/src/components/EmailItem.tsx`
  - **Risk:** Medium
  - **Surface:** safe-isolated
  - **Owner hints:** frontend
  - **GitHub artifacts:**
    - **Branch:** `feat/email-list-t7`
    - **PR title:** `[feat] Mobile: Email list with gestures and filtering`
    - **Labels:** `feat`, `mobile`, `ui`
    - **Issue body:** Create email list interface with touch gestures and filtering

- **T8. Task Management Interface** — _Purpose:_ Mobile task management with touch interactions
  - **Acceptance criteria:**
    - Task list with swipe-to-complete gestures
    - Task creation modal from email actions
    - Due date picker and priority selection
    - Task filtering by status and category
  - **Predicted file touches:** `mobile/src/screens/TaskScreen.tsx`, `mobile/src/components/TaskItem.tsx`
  - **Risk:** Medium
  - **Surface:** safe-isolated
  - **Owner hints:** frontend
  - **GitHub artifacts:**
    - **Branch:** `feat/task-ui-t8`
    - **PR title:** `[feat] Mobile: Task management interface`
    - **Labels:** `feat`, `mobile`, `tasks`
    - **Issue body:** Build mobile task management with touch-optimized interactions

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

- `T1 → T2` — Email service needs API foundation
- `T1 → T3` — AI service needs API foundation  
- `T1 → T4` — Task API needs API foundation
- `T2 → T9` — Email processing needs email service
- `T3 → T9` — Email processing needs AI service
- `T5 → T6` — Auth flow needs RN project setup
- `T5 → T7` — Email UI needs RN project setup
- `T5 → T8` — Task UI needs RN project setup

## Parallel Blocks

- **Block A - Backend Foundation** _(run in parallel with other Blocks; conflict risk: Low)_
  - **Rationale:** Core API services with minimal shared dependencies
  - **Tasks:** `T1`, `T2`, `T3`, `T4` (T1 must complete first, then T2-T4 in parallel)
  - **Notes:** T1 creates foundation, then T2-T4 can run simultaneously

- **Block B - React Native Foundation** _(run in parallel with Block A; conflict risk: Low)_
  - **Rationale:** Mobile app setup independent of backend details
  - **Tasks:** `T5`, `T6`, `T7`, `T8` (T5 must complete first, then T6-T8 in parallel)
  - **Notes:** T5 creates RN foundation, then mobile screens can be built simultaneously

- **Block C - Integration Layer** _(depends on Blocks A+B; conflict risk: Medium)_
  - **Rationale:** Requires both backend and frontend to be functional
  - **Tasks:** `T9` (background processing with WebSocket integration)
  - **Notes:** Needs API and mobile app basics complete

- **Block D - Deployment** _(run in parallel with Block C; conflict risk: Low)_
  - **Rationale:** Infrastructure setup independent of application logic
  - **Tasks:** `T10` (Docker and cloud deployment configuration)
  - **Notes:** Can be prepared while integration work happens

## Scheduling Plan

- **Day-0 startables:** `T1` (API Foundation), `T5` (RN Setup), `T10` (Deployment Config)
- **Gated tasks:** 
  - `T2`, `T3`, `T4` (depends on `T1`, gate: API foundation)
  - `T6`, `T7`, `T8` (depends on `T5`, gate: RN foundation)
  - `T9` (depends on `T2`, `T3`, gate: email and AI services)
- **Agent allocation:** 
  - Block A (2 agents: 1 for T1, then split T2-T4)
  - Block B (2 agents: 1 for T5, then split T6-T8)
  - Block C (1 agent: T9 integration work)
  - Block D (1 agent: T10 deployment)

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
- **React Native** with **TypeScript**
- **Redux Toolkit + RTK Query** - State and API management
- **React Navigation** - Mobile navigation
- **Native UI components** - Platform-specific look/feel

### Deployment
- **Docker** containers for backend
- **Railway/Render** for quick cloud deployment
- **Expo** for mobile app distribution (faster than app stores)

## Timeline Summary

| Week | Block A (Backend) | Block B (Mobile) | Block C (Integration) | Block D (Deploy) |
|------|------------------|------------------|---------------------|------------------|
| **1** | T1: API Foundation | T5: RN Setup | - | T10: Docker Config |
| **2** | T2,T3,T4: Services | T6,T7,T8: UI Screens | - | Continue T10 |
| **3** | Continue T2-T4 | Continue T6-T8 | - | Deploy staging |
| **4** | Testing & Polish | Testing & Polish | T9: Integration | Deploy production |
| **5** | Bug fixes | Bug fixes | Testing | User migration |
| **6** | **MVP COMPLETE** | **MVP COMPLETE** | **MVP COMPLETE** | **MVP COMPLETE** |

**Total Duration: 6 weeks for fully functional MVP**

## Success Metrics

- **Week 2:** Backend API serves email data, Mobile app displays emails
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
- **Week 1:** API foundation serving health checks, RN app building successfully
- **Week 2:** Email data flowing through API, Mobile screens displaying sample data  
- **Week 3:** Full email processing pipeline, Task management UI functional
- **Week 4:** End-to-end integration, WebSocket real-time updates working
- **Week 5:** Production deployment, performance optimization
- **Week 6:** User migration tools, first production users

---

**READY FOR IMMEDIATE EXECUTION**
**Agents can start T1, T5, T10 in parallel NOW** 
**Expected MVP delivery: 6 weeks from start**
