# Email Helper FastAPI Backend

This is the REST API backend for the Email Helper mobile application, built with FastAPI and integrating with the existing Email Helper infrastructure.

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

## Getting Started

### Prerequisites

- Python 3.9+
- Required packages (install with pip):
  ```
  fastapi uvicorn python-jose[cryptography] python-multipart 
  pydantic pydantic-settings passlib[bcrypt] email-validator
  ```

### Running the Server

1. **Using the entry point script:**
   ```bash
   python run_backend.py
   ```

2. **Using uvicorn directly:**
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **For development with auto-reload:**
   ```bash
   DEBUG=true python run_backend.py
   ```

The server will start on `http://localhost:8000` by default.

### Configuration

Configuration is handled through environment variables or a `.env` file:

```bash
# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Database
DATABASE_URL=sqlite:///./runtime_data/email_helper_history.db

# Azure OpenAI (if using AI features)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01

# CORS (for mobile app)
CORS_ORIGINS=["*"]  # Configure appropriately for production
```

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

## Production Deployment

For production deployment:

1. Set a strong `SECRET_KEY`
2. Configure appropriate `CORS_ORIGINS`
3. Use environment variables for sensitive configuration
4. Consider using a production ASGI server like Gunicorn with Uvicorn workers
5. Set up proper logging and monitoring
6. Use HTTPS in production environments