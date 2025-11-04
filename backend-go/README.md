# Email Helper Backend (Go)

A high-performance Go backend for the Email Helper application, replacing the Python FastAPI backend.

## Features

- **High Performance**: Go's native concurrency and efficiency
- **Outlook Integration**: COM integration for Windows Outlook access
- **Azure OpenAI**: AI-powered email classification and analysis
- **Prompty Templates**: Uses `.prompty` files for prompt management (shared with Python backend)
- **SQLite Database**: Local email and task persistence
- **Real-time Updates**: WebSocket support for processing pipelines
- **RESTful API**: Compatible with existing frontend

## Prerequisites

- Go 1.21 or higher
- Windows with Microsoft Outlook installed
- Azure OpenAI API access
- SQLite3

## Installation

```powershell
# Initialize Go modules
cd backend-go
go mod download

# Build the application
go build -o bin/email-helper.exe cmd/api/main.go
```

## Configuration

Create a `.env` file or configure via environment variables:

```env
# Server
PORT=8000
HOST=0.0.0.0
DEBUG=false

# Database
DATABASE_PATH=../runtime_data/database/email_helper_history.db

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01

# Email Provider
USE_COM_BACKEND=true
EMAIL_PROVIDER=outlook
```

## Running

```powershell
# Development mode
go run cmd/api/main.go

# Production mode (from built binary)
./bin/email-helper.exe
```

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /` - API info

### AI Processing
- `POST /api/ai/classify` - Classify email
- `POST /api/ai/action-items` - Extract action items
- `POST /api/ai/summarize` - Generate summary
- `GET /api/ai/templates` - List available templates
- `GET /api/ai/health` - AI service health
- `POST /api/ai/classify-batch-stream` - Batch classification with streaming

### Email Management
- `GET /api/emails` - List emails (paginated)
- `GET /api/emails/{id}` - Get specific email
- `GET /api/emails/search` - Search emails
- `GET /api/emails/stats` - Email statistics
- `POST /api/emails/prefetch` - Prefetch multiple emails
- `GET /api/emails/category-mappings` - Category to folder mappings
- `GET /api/emails/accuracy-stats` - AI accuracy statistics
- `PUT /api/emails/{id}/read` - Update read status
- `POST /api/emails/{id}/mark-read` - Mark as read (deprecated)
- `POST /api/emails/{id}/move` - Move email to folder
- `PUT /api/emails/{id}/classification` - Update classification
- `POST /api/emails/bulk-apply-to-outlook` - Bulk apply classifications
- `POST /api/emails/batch-process` - Batch process emails
- `POST /api/emails/extract-tasks` - Extract tasks from emails
- `POST /api/emails/sync-to-database` - Sync emails to database
- `POST /api/emails/analyze-holistically` - Holistic email analysis

### Folders & Conversations
- `GET /api/folders` - List email folders
- `GET /api/conversations/{id}` - Get conversation thread

### Task Management
- `GET /api/tasks` - List tasks (paginated)
- `POST /api/tasks` - Create task
- `GET /api/tasks/{id}` - Get task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task
- `GET /api/tasks/stats` - Task statistics
- `PUT /api/tasks/{id}/status` - Update task status
- `POST /api/tasks/{id}/link-email` - Link email to task
- `POST /api/tasks/bulk-update` - Bulk update tasks
- `POST /api/tasks/bulk-delete` - Bulk delete tasks
- `POST /api/tasks/deduplicate/fyi` - Deduplicate FYI tasks
- `POST /api/tasks/deduplicate/newsletters` - Deduplicate newsletter tasks

### Settings
- `GET /api/settings` - Get user settings
- `PUT /api/settings` - Update settings
- `DELETE /api/settings` - Reset settings

### Processing Pipelines
- `POST /api/processing/start` - Start processing pipeline
- `GET /api/processing/{id}/status` - Get pipeline status
- `GET /api/processing/{id}/jobs` - Get pipeline jobs
- `POST /api/processing/{id}/cancel` - Cancel pipeline
- `GET /api/processing/stats` - Processing statistics
- `WS /api/processing/ws/{id}` - WebSocket for pipeline updates
- `WS /api/processing/ws` - General WebSocket endpoint

## Project Structure

```
backend-go/
├── cmd/
│   └── api/
│       └── main.go           # Application entry point
├── internal/
│   ├── handlers/             # HTTP handlers
│   │   ├── ai.go            # AI endpoints
│   │   ├── emails.go        # Email endpoints
│   │   ├── tasks.go         # Task endpoints
│   │   ├── settings.go      # Settings endpoints
│   │   └── processing.go    # Processing endpoints
│   ├── services/            # Business logic
│   │   ├── ai_service.go    # AI processing service
│   │   ├── email_service.go # Email operations
│   │   ├── task_service.go  # Task management
│   │   └── websocket.go     # WebSocket manager
│   ├── database/            # Database layer
│   │   ├── connection.go    # Database connection
│   │   ├── emails.go        # Email queries
│   │   ├── tasks.go         # Task queries
│   │   └── settings.go      # Settings queries
│   └── models/              # Data models
│       ├── email.go         # Email models
│       ├── task.go          # Task models
│       ├── ai.go            # AI request/response models
│       └── settings.go      # Settings models
├── pkg/
│   ├── outlook/             # Outlook COM integration
│   │   └── provider.go      # COM email provider
│   ├── azureopenai/         # Azure OpenAI client
│   │   └── client.go        # OpenAI API client
│   └── prompty/             # Prompty template parser
│       ├── parser.go        # .prompty file parser
│       └── parser_test.go   # Parser tests
├── config/
│   └── config.go            # Configuration management
├── go.mod                   # Go module definition
└── README.md               # This file
```

## Prompty Integration

The Go backend reads AI prompts from `.prompty` files in the `prompts/` directory, ensuring consistency with the Python backend.

### How It Works

1. On startup, the backend loads all `.prompty` files from `../prompts/`
2. Prompts are parsed to extract:
   - System and user prompt templates
   - Model parameters (temperature, max_tokens)
   - Metadata (name, description, version)
3. Templates use variable substitution (e.g., `{{subject}}`, `{{sender}}`, `{{body}}`)
4. Falls back to hardcoded prompts if `.prompty` files aren't found

### Used Prompty Files

- `email_classifier_with_explanation.prompty` - Email classification
- `summerize_action_item.prompty` - Action item extraction
- `email_one_line_summary.prompty` - Email summarization

### Testing Prompty Integration

```powershell
# Run prompty parser tests
go test ./pkg/prompty/... -v

# Test prompty loading with actual files
go run ./cmd/test-prompty
```

See [docs/PROMPTY_INTEGRATION.md](docs/PROMPTY_INTEGRATION.md) for detailed documentation.

## Development

### Testing

```powershell
go test ./...
```

### Building

```powershell
# Windows
go build -o bin/email-helper.exe cmd/api/main.go

# Linux/Mac
GOOS=linux go build -o bin/email-helper cmd/api/main.go
```

### Code Style

- Follow standard Go conventions
- Use `gofmt` for formatting
- Run `golint` and `go vet` before commits

## Performance Advantages

- **Faster startup**: Sub-second server startup vs. 2-3 seconds with Python
- **Lower memory**: ~20MB vs. 100MB+ with Python/FastAPI
- **Better concurrency**: Native goroutines vs. async/await
- **No GIL**: True parallelism for CPU-bound operations
- **Static binary**: No virtual environment or dependency issues

## Migration from Python Backend

The Go backend is a drop-in replacement for the Python backend. All API endpoints maintain the same signatures and behavior. Simply:

1. Stop the Python backend
2. Start the Go backend on port 8000
3. Frontend will work without changes

## License

Same as main Email Helper project
