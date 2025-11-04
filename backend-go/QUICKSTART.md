# Email Helper Go Backend - Quick Start

This document will help you get the Go backend running quickly.

## Prerequisites

1. **Go 1.21+**: Download from https://golang.org/dl/
2. **Windows with Outlook**: For COM integration
3. **Azure OpenAI Access**: API key and endpoint

## Quick Start (5 minutes)

### 1. Install Dependencies

```powershell
cd backend-go
.\build.ps1 -Install
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your Azure OpenAI credentials:

```powershell
Copy-Item .env.example .env
# Edit .env with your text editor
```

Required settings in `.env`:
```env
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-actual-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

### 3. Run in Development Mode

```powershell
.\build.ps1 -Dev
```

The server will start on http://localhost:8000

### 4. Test It Works

Open another PowerShell window:

```powershell
# Test health endpoint
curl http://localhost:8000/health

# Test API root
curl http://localhost:8000/
```

## Development Workflow

### Hot Reload Development

For automatic restart on file changes:

```powershell
# Install air (one-time)
go install github.com/cosmtrek/air@latest

# Run with hot reload
.\build.ps1 -Dev
```

### Build and Run

```powershell
# Build binary
.\build.ps1 -Build

# Run built binary
.\build.ps1 -Run

# Or do both
.\build.ps1 -Build -Run
```

### Run Tests

```powershell
.\build.ps1 -Test
```

### Clean Build

```powershell
.\build.ps1 -Clean -Build
```

## Project Structure

```
backend-go/
├── cmd/api/main.go              # Entry point
├── config/config.go             # Configuration
├── internal/
│   ├── handlers/handlers.go    # HTTP handlers (TO IMPLEMENT)
│   ├── services/               # Business logic (TO IMPLEMENT)
│   ├── database/               # Database layer (TO IMPLEMENT)
│   └── models/                 # Data models (DONE)
├── pkg/
│   ├── outlook/                # Outlook COM (TO IMPLEMENT)
│   └── azureopenai/            # Azure OpenAI (TO IMPLEMENT)
├── api-spec.yml                # OpenAPI specification
├── IMPLEMENTATION_GUIDE.md     # Detailed implementation guide
└── build.ps1                   # Build script
```

## Implementation Status

✅ **Completed:**
- Project structure
- Configuration management
- Data models
- API routes skeleton
- OpenAPI specification
- Build scripts

❌ **To Implement:**
1. Database layer (SQLite)
2. Outlook COM integration
3. Azure OpenAI client
4. Handler implementations
5. Service layer
6. WebSocket support
7. Tests

## Next Steps

### 1. Implement Database Layer

Start with `internal/database/connection.go`:

```go
package database

import (
    "database/sql"
    _ "github.com/mattn/go-sqlite3"
)

func Connect(dbPath string) (*sql.DB, error) {
    db, err := sql.Open("sqlite3", dbPath)
    if err != nil {
        return nil, err
    }
    
    // Initialize schema
    if err := initSchema(db); err != nil {
        return nil, err
    }
    
    return db, nil
}
```

See `IMPLEMENTATION_GUIDE.md` for complete database schema.

### 2. Implement Outlook COM Provider

Start with `pkg/outlook/provider.go`:

```go
package outlook

import (
    "github.com/go-ole/go-ole"
    "github.com/go-ole/go-ole/oleutil"
)

type OutlookProvider struct {
    outlook *ole.IDispatch
    mapi    *ole.IDispatch
}

func New() (*OutlookProvider, error) {
    ole.CoInitialize(0)
    
    unknown, err := oleutil.CreateObject("Outlook.Application")
    if err != nil {
        return nil, err
    }
    
    outlook, err := unknown.QueryInterface(ole.IID_IDispatch)
    if err != nil {
        return nil, err
    }
    
    mapi := oleutil.MustGetProperty(outlook, "GetNamespace", "MAPI").ToIDispatch()
    
    return &OutlookProvider{
        outlook: outlook,
        mapi:    mapi,
    }, nil
}
```

See `IMPLEMENTATION_GUIDE.md` for complete COM examples.

### 3. Implement Azure OpenAI Client

Start with `pkg/azureopenai/client.go`:

```go
package azureopenai

import (
    "context"
    "github.com/sashabaranov/go-openai"
)

type Client struct {
    client   *openai.Client
    deployment string
}

func New(endpoint, apiKey, deployment string) *Client {
    config := openai.DefaultAzureConfig(apiKey, endpoint)
    config.APIVersion = "2024-02-01"
    
    return &Client{
        client:   openai.NewClientWithConfig(config),
        deployment: deployment,
    }
}

func (c *Client) Classify(ctx context.Context, emailContent string) (*ClassificationResult, error) {
    // Implement classification logic
    // See IMPLEMENTATION_GUIDE.md for prompt structure
}
```

## Testing the Backend

### Manual API Testing

```powershell
# Health check
curl http://localhost:8000/health

# Test classification (once implemented)
curl -X POST http://localhost:8000/api/ai/classify `
  -H "Content-Type: application/json" `
  -d '{"subject":"Test","sender":"test@test.com","content":"Test email"}'

# Get emails (once implemented)
curl http://localhost:8000/api/emails?limit=10
```

### Frontend Integration

Once handlers are implemented, the frontend will work without changes:

1. Stop Python backend
2. Start Go backend on port 8000
3. Frontend connects automatically

## Troubleshooting

### "go: command not found"

Install Go from https://golang.org/dl/

### "Cannot find module"

```powershell
.\build.ps1 -Install
go mod tidy
```

### "Outlook.Application not found"

Ensure Microsoft Outlook is installed and has been run at least once.

### Port 8000 already in use

```powershell
# Stop Python backend
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force

# Or use different port
.\build.ps1 -Dev -Port 9000
```

## Resources

- **OpenAPI Spec**: `api-spec.yml` - Complete API documentation
- **Implementation Guide**: `IMPLEMENTATION_GUIDE.md` - Detailed implementation details
- **Go Documentation**: https://golang.org/doc/
- **Gin Framework**: https://gin-gonic.com/docs/
- **go-ole**: https://github.com/go-ole/go-ole

## Getting Help

1. Check `IMPLEMENTATION_GUIDE.md` for detailed examples
2. Review Python backend implementation in `../backend/`
3. Check `api-spec.yml` for API specifications
4. Use `go doc` for package documentation

## Performance Goals

The Go backend should achieve:

- ⚡ <10ms response time for simple endpoints
- ⚡ <100ms for AI classification (network dependent)
- 💾 <50MB memory usage at rest
- 🚀 <1 second startup time
- 🔄 1000+ concurrent requests supported

Good luck with the implementation! 🚀
