# API Usage Patterns

## Overview

The Email Helper API is designed for desktop applications with specific patterns optimized for:
- Efficient network usage with batch operations
- Clear data source abstraction (Outlook vs Database)
- Consistent REST naming conventions
- Real-time progress feedback for long operations

This guide covers common usage patterns and best practices.

## Core API Principles

### 1. Atomic vs Batch Operations

**Pattern:** Singular endpoint names for single operations, plural for batch operations.

#### Atomic Operations (Single Item)

Use singular nouns for operations on one item:
- `POST /api/ai/classification` - Classify one email
- `POST /api/ai/summary` - Summarize one email
- `PUT /api/emails/{id}/classification` - Update one email's category
- `PUT /api/tasks/{id}` - Update one task

**When to use:**
- Real-time classification as user reads email
- Single email operations triggered by user actions
- Updating individual item status

**Example:**
```javascript
// Classify email in real-time as user opens it
async function classifyEmail(email) {
  const response = await fetch('http://localhost:8000/api/ai/classification', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      subject: email.subject,
      sender: email.sender,
      content: email.body,
      context: ''
    })
  });
  return await response.json();
}
```

#### Batch Operations (Multiple Items)

Use plural nouns for operations on multiple items:
- `POST /api/ai/classifications` - Classify multiple emails
- `POST /api/ai/summaries` - Summarize multiple emails
- `POST /api/emails/classifications/apply` - Apply classifications to multiple emails
- `POST /api/tasks/updates` - Update multiple tasks
- `DELETE /api/tasks` (with body: `{task_ids: []}`) - Delete multiple tasks

**When to use:**
- Background processing of inbox
- Bulk operations selected by user
- Scheduled batch jobs

**Benefits:**
- **One HTTP request** instead of N requests
- Server-side transaction handling
- Better error handling (partial success reporting)
- Reduced network overhead

**Example:**
```javascript
// Classify selected emails in bulk
async function classifySelectedEmails(emailIds) {
  const response = await fetch('http://localhost:8000/api/ai/classifications', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email_ids: emailIds, context: '' })
  });
  
  const result = await response.json();
  
  // Handle partial failures
  console.log(`Classified ${result.successful} of ${result.total} emails`);
  result.results.forEach(item => {
    if (!item.success) {
      console.error(`Failed to classify ${item.email_id}: ${item.error}`);
    }
  });
  
  return result;
}
```

#### Batch Response Format

All batch operations return standardized response:

```json
{
  "total": 10,
  "successful": 8,
  "failed": 2,
  "results": [
    {
      "item_id": "email-1",
      "success": true,
      "data": { "category": "fyi", "confidence": 0.95 }
    },
    {
      "item_id": "email-2",
      "success": false,
      "error": "EMAIL_NOT_FOUND: Email not found"
    }
  ]
}
```

**Note:** Batch operations return 200 OK even with partial failures. Always check the `failed` count and individual `success` flags.

### 2. Data Source Selection

**Pattern:** Single endpoint intelligently selects data source based on query parameters.

#### The `/api/emails` Unified Endpoint

This endpoint abstracts over two data sources:
- **Live Outlook** (via COM interface): Fresh data, current folder locations
- **SQLite Database**: Cached data with AI classifications and summaries

**Data Source Selection:**
```
/api/emails                          → Outlook Inbox (live)
/api/emails?folder=Sent              → Outlook Sent folder (live)
/api/emails?category=fyi             → Database (cached with classification)
/api/emails?category=action_required → Database (cached with classification)
```

**Why this matters:**
- **Outlook queries** fetch current emails with latest folder locations
- **Database queries** include AI classifications, summaries, and action items
- Frontend doesn't need to know implementation details
- Transparent data source routing based on semantic query intent

**Example Usage:**

```javascript
// Browse current inbox (live from Outlook)
async function getInboxEmails() {
  const response = await fetch(
    'http://localhost:8000/api/emails?folder=Inbox&limit=50'
  );
  return await response.json();
}

// View classified FYI emails (from database)
async function getFYIEmails() {
  const response = await fetch(
    'http://localhost:8000/api/emails?category=fyi&limit=100'
  );
  return await response.json();
}

// Get action items (from database with AI classifications)
async function getActionItems() {
  const response = await fetch(
    'http://localhost:8000/api/emails?category=action_required'
  );
  return await response.json();
}
```

**Design Principle:** Query by semantic meaning (what you want), not implementation (where it's stored).

### 3. Pagination

**Pattern:** Offset-based pagination with `limit` and `offset` parameters.

**Common Endpoints:**
- `GET /api/emails?limit=50&offset=0`
- `GET /api/tasks?page=1&limit=20`

**Response includes pagination metadata:**
```json
{
  "emails": [...],
  "total": 342,
  "offset": 0,
  "limit": 50,
  "has_more": true
}
```

**Example: Infinite Scroll**

```javascript
class EmailList {
  constructor() {
    this.emails = [];
    this.offset = 0;
    this.limit = 50;
    this.hasMore = true;
  }
  
  async loadMore() {
    if (!this.hasMore) return;
    
    const response = await fetch(
      `http://localhost:8000/api/emails?limit=${this.limit}&offset=${this.offset}`
    );
    const data = await response.json();
    
    this.emails.push(...data.emails);
    this.offset += this.limit;
    this.hasMore = data.has_more;
    
    return data.emails;
  }
}
```

**Example: Page-Based Navigation**

```javascript
async function loadTaskPage(pageNumber, pageSize = 20) {
  const response = await fetch(
    `http://localhost:8000/api/tasks?page=${pageNumber}&limit=${pageSize}`
  );
  const data = await response.json();
  
  return {
    tasks: data.tasks,
    totalPages: Math.ceil(data.total_count / pageSize),
    currentPage: data.page,
    hasNext: data.has_next
  };
}
```

### 4. Streaming for Long Operations

**Pattern:** Server-Sent Events (SSE) for real-time progress updates.

**Endpoint:** `POST /api/ai/classifications/stream`

**Use case:** Batch classify 100+ emails with progress indicator in UI.

**Example:**

```javascript
async function classifyWithProgress(emailIds, onProgress) {
  const response = await fetch(
    'http://localhost:8000/api/ai/classifications/stream',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email_ids: emailIds })
    }
  );
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        // Update progress bar
        onProgress({
          current: data.current,
          total: data.total,
          progress: data.progress,
          status: data.status,
          emailId: data.email_id,
          category: data.category
        });
        
        if (data.status === 'completed') {
          console.log('Batch classification completed');
        } else if (data.status === 'error') {
          console.error(`Error processing ${data.email_id}: ${data.error}`);
        }
      }
    }
  }
}

// Usage
classifyWithProgress(emailIds, (update) => {
  progressBar.style.width = `${update.progress}%`;
  statusText.textContent = `Processing ${update.current} of ${update.total}...`;
});
```

**When to use streaming:**
- Batch operations with 50+ items
- Long-running AI processing
- Need real-time UI feedback
- User needs to see incremental progress

**When to use non-streaming batch:**
- Small batches (< 20 items)
- Background processing (no UI feedback needed)
- Simpler client implementation

### 5. Error Handling

**Pattern:** Consistent error response format with application error codes.

**Error Response Structure:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": "Additional context (optional)"
  }
}
```

**HTTP Status Codes:**
- `400` - Bad Request (client error, don't retry)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error (retry after delay)
- `503` - Service Unavailable (retry after delay)

**Retry Strategy:**

```javascript
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      
      if (response.ok) {
        return await response.json();
      }
      
      const error = await response.json();
      
      // Don't retry 400/404 (client errors)
      if (response.status === 400 || response.status === 404) {
        throw new APIError(error.error.code, error.error.message);
      }
      
      // Retry 500/503 (server errors)
      if ((response.status === 500 || response.status === 503) && i < maxRetries - 1) {
        // Exponential backoff: 1s, 2s, 4s
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
        continue;
      }
      
      throw new APIError(error.error.code, error.error.message);
      
    } catch (networkError) {
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
        continue;
      }
      throw networkError;
    }
  }
}

class APIError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}
```

**Error Code Handling:**

```javascript
try {
  const result = await classifyEmail(email);
} catch (error) {
  switch (error.code) {
    case 'VALIDATION_ERROR':
      showFieldError(error.message);
      break;
      
    case 'AI_SERVICE_ERROR':
      showNotification('AI service unavailable. Try again later.');
      break;
      
    case 'EMAIL_NOT_FOUND':
      removeEmailFromList(email.id);
      break;
      
    case 'REQUEST_TIMEOUT':
      showNotification('Request timed out. Email may be too long.');
      break;
      
    default:
      showGenericError(error.message);
  }
}
```

See [ERROR_CODES.md](./ERROR_CODES.md) for complete error code reference.

### 6. Filtering and Search

**Pattern:** Combine multiple query parameters for precise filtering.

**Examples:**

```javascript
// Filter tasks by status and priority
async function getHighPriorityPending() {
  const response = await fetch(
    'http://localhost:8000/api/tasks?status=pending&priority=high'
  );
  return await response.json();
}

// Search tasks
async function searchTasks(searchTerm) {
  const response = await fetch(
    `http://localhost:8000/api/tasks?search=${encodeURIComponent(searchTerm)}`
  );
  return await response.json();
}

// Combine filters
async function getFilteredTasks(filters) {
  const params = new URLSearchParams();
  
  if (filters.status) params.append('status', filters.status);
  if (filters.priority) params.append('priority', filters.priority);
  if (filters.search) params.append('search', filters.search);
  if (filters.page) params.append('page', filters.page);
  if (filters.limit) params.append('limit', filters.limit);
  
  const response = await fetch(
    `http://localhost:8000/api/tasks?${params.toString()}`
  );
  return await response.json();
}

// Usage
const tasks = await getFilteredTasks({
  status: 'pending',
  priority: 'high',
  search: 'budget',
  page: 1,
  limit: 20
});
```

## Common Workflows

### Workflow 1: Process Inbox on Startup

```javascript
async function processInboxOnStartup() {
  // 1. Get unclassified emails from Outlook
  const inboxResponse = await fetch(
    'http://localhost:8000/api/emails?folder=Inbox&limit=100'
  );
  const { emails } = await inboxResponse.json();
  
  // Filter to emails not yet classified (no ai_category)
  const unclassifiedEmails = emails.filter(e => !e.ai_category);
  
  if (unclassifiedEmails.length === 0) {
    console.log('All emails already classified');
    return;
  }
  
  // 2. Batch classify with streaming progress
  const emailIds = unclassifiedEmails.map(e => e.id);
  await classifyWithProgress(emailIds, (progress) => {
    updateProgressBar(progress);
  });
  
  // 3. Apply classifications to Outlook folders
  const applyResponse = await fetch(
    'http://localhost:8000/api/emails/classifications/apply',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email_ids: emailIds,
        apply_to_outlook: true
      })
    }
  );
  
  const applyResult = await applyResponse.json();
  console.log(`Applied classifications to ${applyResult.successful} emails`);
  
  // 4. Extract action items
  const actionEmailIds = unclassifiedEmails
    .filter(e => ['required_personal_action', 'team_action'].includes(e.ai_category))
    .map(e => e.id);
    
  if (actionEmailIds.length > 0) {
    await fetch('http://localhost:8000/api/emails/extract-tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email_ids: actionEmailIds })
    });
  }
}
```

### Workflow 2: Real-time Email Classification

```javascript
// Classify email as user opens it
async function onEmailOpened(email) {
  // Check if already classified
  if (email.ai_category) {
    displayClassification(email.ai_category, email.ai_confidence);
    return;
  }
  
  // Show loading indicator
  showClassificationLoading();
  
  try {
    // Classify in real-time
    const result = await fetch('http://localhost:8000/api/ai/classification', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subject: email.subject,
        sender: email.sender,
        content: email.body,
        context: ''
      })
    });
    
    const classification = await result.json();
    
    // Update UI
    displayClassification(classification.category, classification.confidence);
    
    // Update database
    await fetch(`http://localhost:8000/api/emails/${email.id}/classification`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        category: classification.category,
        apply_to_outlook: true
      })
    });
    
  } catch (error) {
    showClassificationError(error.message);
  }
}
```

### Workflow 3: Bulk Task Management

```javascript
// Update multiple tasks at once
async function updateSelectedTasks(taskIds, updates) {
  const response = await fetch('http://localhost:8000/api/tasks/updates', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      task_ids: taskIds,
      updates: updates
    })
  });
  
  const result = await response.json();
  
  // Handle partial failures
  if (result.failed > 0) {
    const failedTasks = result.results
      .filter(r => !r.success)
      .map(r => r.item_id);
    
    showWarning(`Failed to update ${result.failed} tasks: ${failedTasks.join(', ')}`);
  }
  
  return result;
}

// Usage: Mark selected tasks as completed
const selectedIds = [1, 2, 3, 4, 5];
await updateSelectedTasks(selectedIds, {
  status: 'completed',
  completed_at: new Date().toISOString()
});
```

### Workflow 4: Search and Filter Tasks

```javascript
// Build dynamic task query
class TaskQuery {
  constructor() {
    this.filters = {};
  }
  
  status(status) {
    this.filters.status = status;
    return this;
  }
  
  priority(priority) {
    this.filters.priority = priority;
    return this;
  }
  
  search(term) {
    this.filters.search = term;
    return this;
  }
  
  page(pageNum, pageSize = 20) {
    this.filters.page = pageNum;
    this.filters.limit = pageSize;
    return this;
  }
  
  async execute() {
    const params = new URLSearchParams(this.filters);
    const response = await fetch(
      `http://localhost:8000/api/tasks?${params.toString()}`
    );
    return await response.json();
  }
}

// Usage: Find high-priority pending tasks containing "budget"
const tasks = await new TaskQuery()
  .status('pending')
  .priority('high')
  .search('budget')
  .page(1, 20)
  .execute();

console.log(`Found ${tasks.total_count} matching tasks`);
```

## Performance Best Practices

### 1. Use Batch Operations

❌ **Bad: N+1 requests**
```javascript
for (const emailId of emailIds) {
  await fetch('http://localhost:8000/api/ai/classification', {
    method: 'POST',
    body: JSON.stringify({ email_id: emailId })
  });
}
```

✅ **Good: Single batch request**
```javascript
await fetch('http://localhost:8000/api/ai/classifications', {
  method: 'POST',
  body: JSON.stringify({ email_ids: emailIds })
});
```

### 2. Pagination for Large Lists

❌ **Bad: Load all data at once**
```javascript
const allEmails = await fetch('http://localhost:8000/api/emails?limit=50000');
```

✅ **Good: Paginate and lazy-load**
```javascript
const firstPage = await fetch('http://localhost:8000/api/emails?limit=50&offset=0');
// Load more as user scrolls
```

### 3. Cache Expensive Operations

```javascript
class EmailCache {
  constructor() {
    this.cache = new Map();
    this.maxAge = 5 * 60 * 1000; // 5 minutes
  }
  
  async getEmail(id) {
    const cached = this.cache.get(id);
    
    if (cached && Date.now() - cached.timestamp < this.maxAge) {
      return cached.data;
    }
    
    const response = await fetch(`http://localhost:8000/api/emails/${id}`);
    const data = await response.json();
    
    this.cache.set(id, { data, timestamp: Date.now() });
    return data;
  }
}
```

### 4. Debounce Search Queries

```javascript
function debounce(func, delay) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

const searchTasks = debounce(async (searchTerm) => {
  const response = await fetch(
    `http://localhost:8000/api/tasks?search=${encodeURIComponent(searchTerm)}`
  );
  const data = await response.json();
  updateSearchResults(data.tasks);
}, 300);

// Usage: Search as user types (with 300ms delay)
searchInput.addEventListener('input', (e) => {
  searchTasks(e.target.value);
});
```

### 5. Parallel Independent Requests

```javascript
// Load multiple resources in parallel
async function loadDashboard() {
  const [tasks, emails, stats] = await Promise.all([
    fetch('http://localhost:8000/api/tasks?status=pending&limit=10').then(r => r.json()),
    fetch('http://localhost:8000/api/emails?category=action_required&limit=20').then(r => r.json()),
    fetch('http://localhost:8000/api/tasks/stats').then(r => r.json())
  ]);
  
  renderDashboard({ tasks, emails, stats });
}
```

## Deprecation Handling

Some endpoints are deprecated in favor of more consistent naming. The API returns deprecation headers:

```
X-Deprecation-Warning: This endpoint is deprecated. Use POST /api/ai/classification instead
X-Sunset: 2025-05-01
```

**Migration Strategy:**

```javascript
async function classifyEmail(email) {
  // Try new endpoint first
  try {
    return await fetch('http://localhost:8000/api/ai/classification', {
      method: 'POST',
      body: JSON.stringify(email)
    });
  } catch (error) {
    // Fallback to deprecated endpoint
    console.warn('Using deprecated /api/ai/classify endpoint');
    return await fetch('http://localhost:8000/api/ai/classify', {
      method: 'POST',
      body: JSON.stringify(email)
    });
  }
}
```

**Deprecated Endpoints:**
- `/api/ai/classify` → Use `/api/ai/classification`
- `/api/ai/summarize` → Use `/api/ai/summary`
- `/api/ai/classify-batch-stream` → Use `/api/ai/classifications/stream`
- `/api/emails/bulk-apply-to-outlook` → Use `/api/emails/classifications/apply`
- `/api/emails/batch-process` → Use `/api/ai/classifications`
- `/api/tasks/bulk-update` → Use `/api/tasks/updates`
- `/api/tasks/bulk-delete` → Use `DELETE /api/tasks` (with body)

All deprecated endpoints will be removed on **2025-05-01**.

## Testing API Endpoints

### Using curl

```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Classify email
curl -X POST "http://localhost:8000/api/ai/classification" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Team meeting tomorrow",
    "sender": "manager@company.com",
    "content": "Please join us for the team meeting tomorrow at 2 PM",
    "context": ""
  }'

# Get inbox emails
curl -X GET "http://localhost:8000/api/emails?folder=Inbox&limit=10"

# Get classified FYI emails
curl -X GET "http://localhost:8000/api/emails?category=fyi&limit=20"

# Get tasks
curl -X GET "http://localhost:8000/api/tasks?status=pending&priority=high"

# Batch classify emails
curl -X POST "http://localhost:8000/api/ai/classifications" \
  -H "Content-Type: application/json" \
  -d '{
    "email_ids": ["email-1", "email-2", "email-3"],
    "context": ""
  }'
```

### Using Postman

Import the provided Postman collection: `email_helper.postman_collection.json`

The collection includes:
- All API endpoints with example requests
- Environment variables for localhost
- Pre-request scripts for authentication
- Test assertions for responses

## API Client Libraries

### JavaScript/TypeScript

```typescript
class EmailHelperClient {
  constructor(private baseURL: string = 'http://localhost:8000') {}
  
  async classifyEmail(email: EmailContent): Promise<Classification> {
    const response = await fetch(`${this.baseURL}/api/ai/classification`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(email)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new APIError(error.error.code, error.error.message);
    }
    
    return await response.json();
  }
  
  async getEmails(params: EmailQueryParams): Promise<EmailListResponse> {
    const queryParams = new URLSearchParams(params as any);
    const response = await fetch(
      `${this.baseURL}/api/emails?${queryParams.toString()}`
    );
    return await response.json();
  }
  
  async getTasks(params: TaskQueryParams): Promise<TaskListResponse> {
    const queryParams = new URLSearchParams(params as any);
    const response = await fetch(
      `${this.baseURL}/api/tasks?${queryParams.toString()}`
    );
    return await response.json();
  }
}

// Usage
const client = new EmailHelperClient();
const classification = await client.classifyEmail({
  subject: 'Meeting tomorrow',
  sender: 'manager@company.com',
  content: 'Team meeting at 2 PM'
});
```

## Additional Resources

- [Error Codes Reference](./ERROR_CODES.md) - Complete error code documentation
- [OpenAPI Specification](../../backend-go/api-spec.yml) - Full API specification
- [Postman Collection](../../email_helper.postman_collection.json) - Ready-to-use API collection
