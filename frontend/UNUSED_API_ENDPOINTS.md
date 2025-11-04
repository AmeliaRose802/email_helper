# Unused API Endpoints Analysis

This document lists all API endpoints defined in `api-spec.yml` that are **NOT** currently used by the frontend application.

**Analysis Date:** October 31, 2025

---

## Summary

- **Total Endpoints in API Spec:** 25 paths (some with multiple HTTP methods)
- **Used by Frontend:** 21
- **Unused by Frontend:** 11

---

## Unused Endpoints

### Health & Info Endpoints

#### 1. `GET /` - API Root Information
- **Description:** Returns API information including version, docs links, and health endpoint
- **Spec Location:** Line 32
- **Reason Unused:** Frontend uses `/health` directly instead
- **Recommendation:** Keep for API documentation/discovery purposes

---

### AI Endpoints

#### 2. `POST /api/ai/action-items` - Extract Action Items
- **Description:** Extract action items from email content
- **Spec Location:** Line 111
- **Frontend Implementation:** `aiApi` has `getActionItems` using `builder.query` which defaults to GET HTTP method, but spec defines POST
- **Issue:** Method mismatch - RTK Query `builder.query` defaults to GET, but spec defines POST with request body
- **Recommendation:** Either change frontend to use `builder.mutation` with POST, or update spec to GET with query params

#### 3. `GET /api/ai/templates` - Get Prompt Templates
- **Description:** Get available AI prompt templates
- **Spec Location:** Line 140
- **Reason Unused:** No frontend UI for managing/viewing prompt templates
- **Recommendation:** Consider adding settings UI for custom prompts

#### 4. `GET /api/ai/health` - AI Service Health Check
- **Description:** Check if AI service is available
- **Spec Location:** Line 155
- **Reason Unused:** Frontend doesn't monitor AI service health separately
- **Recommendation:** Add to dashboard or status page

---

### Email Endpoints

#### 5. `GET /api/emails/search` - Search Emails
- **Description:** Search emails with pagination
- **Spec Location:** Line 234
- **Frontend Implementation:** `emailApi.searchEmails` exists but is never called in components
- **Recommendation:** Implement search UI or remove endpoint



#### 6. `POST /api/emails/prefetch` - Prefetch Multiple Emails
- **Description:** Batch fetch multiple emails by IDs
- **Spec Location:** Line 282
- **Reason Unused:** Frontend fetches emails individually or via list endpoint
- **Recommendation:** Could improve performance for bulk operations

#### 7. `PUT /api/emails/{id}/read` - Update Read Status
- **Description:** Mark email as read/unread
- **Spec Location:** Line 310
- **Frontend Implementation:** `emailApi.markEmailRead` exists but uses PUT with body instead of query param
- **Issue:** Parameter location mismatch (spec: query param, frontend: body)
- **Recommendation:** Align implementations

#### 8. `POST /api/emails/{id}/move` - Move Email to Folder
- **Description:** Move email to different folder
- **Spec Location:** Line 328
- **Frontend Implementation:** `emailApi.moveEmail` exists but is never called
- **Recommendation:** Implement folder management UI or remove

---

### Folder & Conversation Endpoints

#### 9. `GET /api/folders` - List Email Folders
- **Description:** Get list of available email folders
- **Spec Location:** Line 433
- **Reason Unused:** Frontend doesn't display folder navigation
- **Recommendation:** Add folder sidebar/navigation

#### 10. `GET /api/conversations/{id}` - Get Conversation Thread
- **Description:** Get email conversation thread by conversation ID
- **Spec Location:** Line 448
- **Reason Unused:** No conversation threading UI
- **Recommendation:** Add threaded email view

---

### Processing Pipeline Endpoints

#### 11. `POST /api/processing/start` - Start Processing Pipeline
- **Description:** Start background processing pipeline for emails
- **Spec Location:** Line 649
- **Reason Unused:** Frontend doesn't expose pipeline control
- **Recommendation:** Add admin/processing control panel

#### 12. `GET /api/processing/{id}/status` - Get Pipeline Status
- **Description:** Check status of processing pipeline
- **Spec Location:** Line 679
- **Reason Unused:** Related to unused start endpoint
- **Recommendation:** Add if pipeline control is implemented

---

## Endpoints with Implementation Issues

These endpoints have frontend implementations but don't match the spec:

### Method Mismatches
- **`/api/ai/action-items`**: Spec says POST, frontend uses GET query

### Parameter Mismatches
- **`/api/emails/{id}/read`**: Spec uses query param `read`, frontend sends body with `is_read`
- **`/api/emails/{id}/move`**: Spec uses query param `destination_folder`, frontend sends body with `folder_name`

---

## Recommendations

### High Priority
1. **Fix method/parameter mismatches** between spec and implementation
2. **Remove unused query implementations** from `emailApi` and `aiApi` to reduce bundle size
3. **Document intentionally unused endpoints** if they're for future features

### Medium Priority
4. **Implement search functionality** or remove `/api/emails/search`
5. **Consider folder navigation** UI for `/api/folders` endpoint

### Low Priority
7. **Add conversation threading** for better email UX
8. **Implement processing pipeline UI** for admin/power users
9. **Add prompt template management** in settings

---

## Used Endpoints (For Reference)

The following endpoints are actively used by the frontend:

- `GET /health` - Health check
- `POST /api/ai/classify` - Email classification
- `POST /api/ai/summarize` - Email summarization
- `GET /api/emails` - List emails
- `GET /api/emails/{id}` - Get email details
- `PUT /api/emails/{id}/classification` - Update classification
- `POST /api/emails/bulk-apply-to-outlook` - Bulk apply categories
- `POST /api/emails/sync-to-database` - Sync emails to DB
- `POST /api/emails/extract-tasks` - Extract tasks from emails
- `GET /api/tasks` - List tasks
- `GET /api/tasks/{id}` - Get task details
- `POST /api/tasks` - Create task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task
- `GET /api/tasks/stats` - Task statistics
- `GET /api/emails/stats` - Email statistics
- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings
- `DELETE /api/settings` - Reset settings

---

## Notes

- Some endpoints like `searchEmails` and `getEmailStats` are defined in the frontend API services but never imported/used in components
- The spec may include endpoints for future features or backwards compatibility
- Consider using OpenAPI code generation tools to keep frontend and spec in sync
