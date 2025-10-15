# Email Helper FastAPI Backend

This is the REST API backend for the Email Helper mobile application, built with FastAPI and integrating with the existing Email Helper infrastructure.

## 🚀 Quick Start - Localhost Development

Get the backend running locally in 3 steps:

### Prerequisites
- **Windows 10/11** with Microsoft Outlook installed and configured
- **Python 3.12+** and pip ([download](https://www.python.org/downloads/))
- **Microsoft Outlook** desktop client (2016 or later)

### Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.localhost.example .env
# Edit .env if needed (works out of the box for localhost)

# 3. Start the server
python run_backend.py
```

The backend will be accessible at **http://localhost:8000**

**Verify setup:**
- ✅ Server started without errors
- ✅ Visit http://localhost:8000/health to check health status
- ✅ Visit http://localhost:8000/docs for interactive API documentation
- ✅ Outlook is running and accessible

> **📖 Detailed Setup:** See [Localhost Setup Guide](../docs/LOCALHOST_SETUP.md) for comprehensive instructions, configuration options, and troubleshooting.

### Environment Configuration

The backend uses the **COM backend** for localhost development, which connects directly to your local Outlook installation:

- **No cloud credentials needed** - Uses local Outlook via COM interface
- **Authentication disabled** by default for development (`REQUIRE_AUTHENTICATION=false`)
- **Azure OpenAI optional** - AI features work if configured, but not required

**Key environment variables** (in `.env`):
```bash
USE_COM_BACKEND=true           # Use local Outlook COM interface
EMAIL_PROVIDER=com             # COM provider for localhost
DEBUG=true                     # Enable debug logging
PORT=8000                      # Server port
```

See [Configuration Reference](../docs/LOCALHOST_SETUP.md#configuration-reference) for all options.

## Features

- **JWT Authentication**: Secure user authentication with access and refresh tokens
- **Database Integration**: SQLite database with existing Email Helper data structures
- **CORS Support**: Configured for React Native mobile app integration
- **Auto-generated Documentation**: Available at `/docs` and `/redoc` endpoints
- **Health Monitoring**: Health check endpoint for monitoring
- **Service Integration**: Adapts existing Email Helper services for API use

## API Endpoints

### Health & Info
- `GET /health` - Health check with database status
- `GET /` - API information and links

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login (returns JWT tokens)
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user information

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Alternative Running Methods

Besides the quick start above, you can also run the backend in these ways:

### Using uvicorn directly
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### With debug and auto-reload
```bash
DEBUG=true python run_backend.py
```

### With custom port
```bash
PORT=8001 python run_backend.py
```

## Configuration Reference

Configuration is handled through environment variables in the `.env` file. The `.env.localhost.example` provides a complete template for localhost development.

**Essential localhost settings:**
```bash
USE_COM_BACKEND=true              # Use local Outlook
EMAIL_PROVIDER=com                # COM provider
DEBUG=true                        # Enable debug logging
REQUIRE_AUTHENTICATION=false      # Skip auth for development
```

**Database:**
```bash
DATABASE_URL=sqlite:///./runtime_data/email_helper_history.db
```

**CORS (for frontend):**
```bash
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

**Azure OpenAI (optional):**
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

> **📖 Complete Reference:** See [Configuration Reference](../docs/LOCALHOST_SETUP.md#configuration-reference) for all available options.

## Architecture

### Directory Structure

```
backend/
├── api/                    # API endpoints
│   └── auth.py            # Authentication endpoints
├── core/                  # Core configuration
│   └── config.py         # Settings and configuration
├── database/              # Database management
│   └── connection.py     # Database connection and setup
├── models/                # Pydantic models
│   ├── user.py           # User models
│   ├── email.py          # Email models  
│   └── task.py           # Task models
├── tests/                 # Test suite
├── main.py               # FastAPI application
└── README.md             # This file
```

### Key Components

- **FastAPI App**: Main application with middleware and routing
- **JWT Authentication**: Secure token-based authentication
- **Database Manager**: Handles SQLite connections and table creation
- **Pydantic Models**: Data validation and serialization
- **Service Integration**: Adapts existing Email Helper services

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest backend/tests/ -v

# Run specific test file
python -m pytest backend/tests/test_auth.py -v

# Run with coverage
python -m pytest backend/tests/ --cov=backend --cov-report=html
```

## API Usage Examples

### Register a new user
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "email": "user@example.com", "password": "securepassword"}'
```

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "password": "securepassword"}'
```

### Access protected endpoint
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Check health
```bash
curl http://localhost:8000/health
```

## Integration with Existing Email Helper

This backend integrates with the existing Email Helper infrastructure:

- **Database**: Uses the same SQLite database as the desktop application
- **Configuration**: Adapts existing configuration patterns from `src/core/config.py`
- **Services**: Can import and use existing services through the ServiceFactory pattern
- **Data Models**: Compatible with existing data structures

## Security Considerations

- **JWT Tokens**: Access tokens expire in 30 minutes, refresh tokens in 30 days
- **Password Hashing**: Uses bcrypt for secure password storage
- **CORS**: Configure `CORS_ORIGINS` appropriately for production
- **Secret Key**: Use a strong, unique secret key in production
- **Database**: SQLite connections are configured with appropriate threading settings

## Development Notes

- The backend is designed to be modular and extensible
- Additional API endpoints can be added to the `api/` directory
- Database migrations are handled through the existing migration system
- Error handling follows FastAPI best practices with consistent JSON responses
- The server includes comprehensive logging and monitoring capabilities

## 🐛 Troubleshooting

### Server Won't Start

**Port already in use:**
```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Or use a different port
PORT=8001 python run_backend.py
```

**Missing dependencies:**
```bash
# Reinstall all dependencies
pip install -r requirements.txt

# Check for pywin32 specifically (required for COM)
pip install pywin32
```

### Outlook COM Errors

**"Cannot connect to Outlook":**
1. Verify Outlook is installed and can be launched manually
2. Try opening Outlook before starting the backend
3. Run the backend with administrator privileges
4. Check Windows Event Viewer for COM errors

**"Outlook profile not found":**
- Ensure you have at least one email account configured in Outlook
- Open Outlook and check that it loads successfully
- Configure a default Outlook profile

### Database Issues

**"Table does not exist" errors:**
```bash
# Delete and recreate database
rm runtime_data/email_helper_history.db
python run_backend.py
```

### API Errors

**CORS errors from frontend:**
- Check `CORS_ORIGINS` in `.env` includes frontend URL
- Verify format: `CORS_ORIGINS=["http://localhost:3000"]`
- Restart backend after changing .env

**401 Unauthorized errors:**
- Check if `REQUIRE_AUTHENTICATION=false` in `.env` for development
- Or provide valid JWT token in Authorization header

> **📖 More Help:** See the [Troubleshooting Guide](../docs/TROUBLESHOOTING.md) for comprehensive solutions to common issues.

## Production Deployment

For production deployment:

1. Set a strong `SECRET_KEY`
2. Configure appropriate `CORS_ORIGINS`
3. Use environment variables for sensitive configuration
4. Consider using a production ASGI server like Gunicorn with Uvicorn workers
5. Set up proper logging and monitoring
6. Use HTTPS in production environments