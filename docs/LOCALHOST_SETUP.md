# Localhost Setup Guide

This comprehensive guide walks you through setting up the Email Helper application for local development on Windows. The application uses a React frontend with a FastAPI backend that integrates with Microsoft Outlook via COM interface.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Verification](#verification)
- [Configuration Reference](#configuration-reference)
- [Starting the Application](#starting-the-application)
- [Next Steps](#next-steps)

## Prerequisites

Before you begin, ensure you have the following installed and configured:

### Required Software

- **Python 3.12+** - [Download from python.org](https://www.python.org/downloads/)
  - Ensure `python` and `pip` are in your PATH
  - Verify: `python --version` and `pip --version`

- **Node.js 18+** - [Download from nodejs.org](https://nodejs.org/)
  - Includes npm package manager
  - Verify: `node --version` and `npm --version`

- **Microsoft Outlook (Desktop Client)** - Must be installed and configured
  - Version: Outlook 2016 or later
  - Must have at least one email account configured
  - Outlook must be able to launch successfully

- **Git** - For cloning the repository
  - [Download Git for Windows](https://git-scm.com/download/win)

### Platform Requirements

- **Windows 10 or 11** (Required for COM interface)
- **Administrator privileges** (for Python package installation)

### Optional but Recommended

- **Azure OpenAI API Access** - For AI-powered email classification and summarization
  - Azure OpenAI resource endpoint
  - API key with access to GPT-4o or similar model
  - See [Azure OpenAI Service documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)

- **Visual Studio Code** - Recommended IDE
  - Python extension
  - TypeScript/JavaScript extensions

## Quick Start

For users who want to get started quickly:

```bash
# 1. Clone the repository
git clone https://github.com/AmeliaRose802/email_helper.git
cd email_helper

# 2. Set up backend
pip install -r requirements.txt
cp .env.localhost.example .env

# 3. Set up frontend
cd frontend
npm install
cp .env.local.example .env.local
cd ..

# 4. Start backend (in one terminal)
python run_backend.py

# 5. Start frontend (in another terminal)
cd frontend
npm run dev
```

Then open your browser to **http://localhost:3000** or **http://localhost:5173**

> **Note:** Continue reading for detailed setup instructions and configuration options.

## Backend Setup

The backend is built with FastAPI and provides REST API endpoints for email operations, authentication, and AI processing.

### 1. Install Python Dependencies

From the project root directory:

```bash
pip install -r requirements.txt
```

This installs all required packages including:
- FastAPI and Uvicorn (web framework and server)
- pywin32 (Windows COM interface for Outlook)
- SQLAlchemy (database ORM)
- Azure OpenAI SDK (AI features)
- And other dependencies

### 2. Configure Environment Variables

The backend uses environment variables for configuration. Create a `.env` file in the project root:

```bash
# Copy the localhost example configuration
cp .env.localhost.example .env
```

Edit the `.env` file with your settings:

```bash
# APPLICATION SETTINGS
APP_NAME="Email Helper API"
APP_VERSION="1.0.0"
DEBUG=true

# SERVER SETTINGS
HOST=0.0.0.0
PORT=8000

# SECURITY SETTINGS
SECRET_KEY=localhost-development-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# AUTHENTICATION & EMAIL PROVIDER
EMAIL_PROVIDER=com
USE_COM_BACKEND=true
REQUIRE_AUTHENTICATION=false

# DATABASE SETTINGS
DATABASE_URL=sqlite:///./runtime_data/email_helper_history.db

# CORS SETTINGS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173", "http://localhost:8081"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
CORS_ALLOW_HEADERS=["*"]

# AZURE OPENAI SETTINGS (Optional - leave blank to skip AI features)
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01
```

### 3. Set Up Azure OpenAI (Optional)

If you want AI-powered email classification and summarization:

1. Create an Azure OpenAI resource in the [Azure Portal](https://portal.azure.com/)
2. Deploy a model (e.g., gpt-4o)
3. Get your endpoint URL and API key from the resource's "Keys and Endpoint" section
4. Update the `.env` file with your credentials:

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

**Alternative:** Use Azure CLI authentication (recommended for security):

```bash
# Login to Azure CLI
az login

# The application will automatically use your Azure credentials
```

### 4. Create Required Directories

The application needs these directories to store data:

```bash
# Create if they don't exist
mkdir runtime_data
mkdir user_specific_data
```

### 5. Run the Backend Server

Start the backend server:

```bash
python run_backend.py
```

You should see output similar to:

```
🌟 Starting Email Helper API v1.0.0
🔧 Debug mode: True
🌐 Server: 0.0.0.0:8000
📋 API docs: http://0.0.0.0:8000/docs
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The backend is now running and ready to accept requests!

**Alternative ways to run the backend:**

```bash
# Using uvicorn directly
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# With debug and auto-reload
DEBUG=true python run_backend.py
```

## Frontend Setup

The frontend is a modern React application built with Vite, TypeScript, and Tailwind CSS.

### 1. Install Node Dependencies

Navigate to the frontend directory and install dependencies:

```bash
cd frontend
npm install
```

This installs all required packages including:
- React and React Router (UI framework)
- Vite (build tool)
- TypeScript (type safety)
- Tailwind CSS (styling)
- Axios (HTTP client)

### 2. Configure Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
# From the frontend directory
cp .env.local.example .env.local
```

Edit the `.env.local` file:

```env
# Backend API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Application Settings
VITE_APP_TITLE=Email Helper
VITE_APP_ENV=development

# Development Features
VITE_DEBUG_LOGGING=true
VITE_LOCALHOST_MODE=true
```

> **Important:** All frontend environment variables must start with `VITE_` to be accessible in the application.

### 3. Start the Development Server

From the `frontend/` directory:

```bash
npm run dev
```

You should see output similar to:

```
  VITE v5.0.0  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.1.100:5173/
  ➜  press h to show help
```

The frontend is now running! Open your browser to the displayed URL (usually http://localhost:5173/ or http://localhost:3000/).

**Alternative commands:**

```bash
# Run on a specific port
npm run dev -- --port 3001

# Build for production
npm run build

# Preview production build
npm run preview
```

## Verification

Follow these steps to verify your setup is working correctly.

### 1. Check Backend Health

Open a new terminal and test the backend health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "email-helper-api",
  "version": "1.0.0",
  "database": "healthy",
  "debug": true
}
```

You can also visit http://localhost:8000/health in your browser.

### 2. Check API Documentation

The backend provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These pages let you explore all available API endpoints and test them directly.

### 3. Verify Outlook Connection

Test the COM connection to Outlook:

```bash
curl http://localhost:8000/api/emails/connect
```

Expected response (if Outlook is running):

```json
{
  "success": true,
  "message": "Connected to Outlook successfully"
}
```

If this fails, see the [Troubleshooting Guide](./TROUBLESHOOTING.md#outlook-com-errors).

### 4. Test Frontend Connection

Open your browser to http://localhost:5173/ (or http://localhost:3000/)

You should see:
- The Email Helper application interface
- No console errors in browser DevTools (F12)
- Ability to navigate between pages

### 5. Verify Frontend-Backend Communication

In the browser DevTools Console (F12), run:

```javascript
fetch('http://localhost:8000/health')
  .then(res => res.json())
  .then(console.log)
```

This should return the health check data without CORS errors.

### 6. Test Email Retrieval

Try fetching emails from Outlook:

1. Open the Email Helper UI in your browser
2. Click "Refresh Emails" or similar button
3. Verify emails appear in the interface

If emails don't load, check the browser console and backend logs for errors.

### 7. Test AI Classification (Optional)

If you configured Azure OpenAI:

1. Select an email in the interface
2. Click "Classify" or "Analyze"
3. Verify AI-generated categories and summary appear

## Configuration Reference

### Backend Configuration (.env)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HOST` | Server host address | `0.0.0.0` | No |
| `PORT` | Server port | `8000` | No |
| `DEBUG` | Enable debug mode | `false` | No |
| `SECRET_KEY` | JWT token secret | - | Yes |
| `EMAIL_PROVIDER` | Email provider (`com` or `graph`) | `com` | Yes |
| `USE_COM_BACKEND` | Use COM interface | `true` | No |
| `REQUIRE_AUTHENTICATION` | Require user auth | `false` | No |
| `DATABASE_URL` | SQLite database path | `sqlite:///./runtime_data/email_helper_history.db` | Yes |
| `CORS_ORIGINS` | Allowed frontend URLs | `["http://localhost:3000"]` | Yes |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | - | No* |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | - | No* |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name | `gpt-4o` | No* |

\* Required only if using AI features

### Frontend Configuration (.env.local)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` | Yes |
| `VITE_API_TIMEOUT` | Request timeout (ms) | `30000` | No |
| `VITE_APP_TITLE` | Application title | `Email Helper` | No |
| `VITE_APP_ENV` | Environment | `development` | No |
| `VITE_DEBUG_LOGGING` | Enable debug logs | `false` | No |
| `VITE_LOCALHOST_MODE` | Localhost mode | `true` | No |

### File Locations

```
email_helper/
├── .env                          # Backend environment variables (not committed)
├── runtime_data/                 # Database and runtime files (not committed)
│   └── email_helper_history.db   # SQLite database
├── user_specific_data/           # User-specific configurations (not committed)
│   ├── job_summery.md            # Your job context for AI
│   └── job_skill_summery.md      # Your skills for AI
├── backend/
│   ├── main.py                   # FastAPI application
│   ├── core/                     # Core backend modules
│   └── services/                 # Email and AI services
└── frontend/
    ├── .env.local                # Frontend environment (not committed)
    ├── src/                      # React source code
    └── public/                   # Static assets
```

## Starting the Application

### One-Command Start (Easy)

Use the provided startup scripts:

**Windows:**
```bash
npm start
```

Or manually:
```bash
start.bat
```

**Linux/Mac:**
```bash
npm start
```

Or manually:
```bash
./start.sh
```

These scripts will:
1. Start the backend server in one terminal
2. Start the frontend dev server in another terminal
3. Display status messages and URLs

### Manual Start (Recommended for Development)

For better control during development:

**Terminal 1 - Backend:**
```bash
python run_backend.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Stopping the Application

- **In each terminal:** Press `Ctrl+C`
- **Windows scripts:** Close the terminal windows that opened
- **To kill ports if stuck:**
  ```bash
  # Windows - kill process on port 8000
  netstat -ano | findstr :8000
  taskkill /PID <process_id> /F
  
  # Kill process on port 3000
  netstat -ano | findstr :3000
  taskkill /PID <process_id> /F
  ```

## Next Steps

After successful setup:

### Explore the Application

1. **Dashboard**: View email summary and statistics
2. **Email List**: Browse and search your emails
3. **AI Analysis**: Use AI to classify and summarize emails
4. **Tasks**: View extracted action items

### Customize AI Behavior

Edit user-specific context files to improve AI accuracy:

1. `user_specific_data/job_summery.md` - Describe your job role and responsibilities
2. `user_specific_data/job_skill_summery.md` - List your skills and areas of expertise

These help the AI better understand which emails are relevant to you.

### Development Workflow

- **Backend changes**: Server auto-reloads with `--reload` flag
- **Frontend changes**: Vite provides hot module replacement (HMR)
- **API testing**: Use Swagger UI at http://localhost:8000/docs
- **Debugging**: Check browser DevTools console and backend terminal logs

### Learn More

- [Backend Architecture](../backend/README.md)
- [Frontend Architecture](../frontend/README.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
- [Graph API Setup](./GRAPH_API_SETUP.md) (for cloud deployment)

### Common Development Tasks

**Running tests:**
```bash
# Backend tests
python -m pytest backend/tests/ -v

# Frontend tests (if configured)
cd frontend
npm test
```

**Linting and formatting:**
```bash
# Backend
black backend/
pylint backend/

# Frontend
cd frontend
npm run lint
```

**Database management:**
```bash
# View database contents
sqlite3 runtime_data/email_helper_history.db
.tables
.schema emails
.quit
```

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](./TROUBLESHOOTING.md)
2. Review backend logs in the terminal
3. Check browser DevTools console (F12)
4. Verify all prerequisites are installed correctly
5. Try setup on a clean environment
6. Review the [Issues page](https://github.com/AmeliaRose802/email_helper/issues)

## Summary Checklist

Use this checklist to ensure complete setup:

- [ ] Python 3.12+ installed and in PATH
- [ ] Node.js 18+ installed and in PATH
- [ ] Microsoft Outlook desktop client installed and configured
- [ ] Git installed
- [ ] Repository cloned
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created and configured
- [ ] Runtime directories created (`runtime_data`, `user_specific_data`)
- [ ] Frontend dependencies installed (`npm install` in frontend/)
- [ ] `.env.local` file created in frontend/
- [ ] Backend starts successfully (`python run_backend.py`)
- [ ] Health endpoint responds (http://localhost:8000/health)
- [ ] Frontend starts successfully (`npm run dev`)
- [ ] Frontend loads in browser (http://localhost:5173/)
- [ ] Outlook connection works
- [ ] Emails can be retrieved and displayed
- [ ] (Optional) Azure OpenAI configured and working

Congratulations! Your Email Helper localhost environment is ready for development. 🎉
