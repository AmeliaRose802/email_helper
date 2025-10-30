# Email Helper - AI-Powered Email Management System

An intelligent email classification and management system designed for professionals with ADHD who need focused, actionable email summaries.

## 🚀 Quick Setup - Desktop App (Recommended)

### Launch the Desktop App
```bash
# Windows - Double-click launcher
launch-desktop.bat

# Or use PowerShell
./launch-desktop.ps1

# Or use npm
npm run electron:dev
```

The desktop app provides:
- Native Windows application experience
- Auto-starting backend server
- System tray integration
- No login required

### Web App Alternative
```bash
npm start
```
This will start the React frontend and API backend for browser use.

### Option 2: Localhost Development Setup

For developers working on the web application (React frontend + FastAPI backend):

#### Prerequisites
- **Windows 10/11** with Microsoft Outlook installed and configured
- **Python 3.12+** and pip ([download](https://www.python.org/downloads/))
- **Node.js 18+** and npm ([download](https://nodejs.org/))

#### Quick Start
```bash
# 1. Clone and navigate to the repository
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

> **📖 Detailed Instructions:** See [Localhost Setup Guide](docs/LOCALHOST_SETUP.md) for comprehensive setup instructions, configuration options, and troubleshooting.

### Option 3: Desktop GUI Application

For the original desktop application with Tkinter GUI:

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Configure Azure Authentication
Choose your preferred authentication method:

**Option A: Azure CLI (Recommended - Most Secure)**
```bash
az login
```

**Option B: Environment Variables (Fallback)**
```bash
# Copy template and configure
cp .env.template .env
# Edit .env with your Azure OpenAI details
```

#### 3. Set Up Personal Configuration
```bash
# Create user-specific data directory (if not exists)
mkdir user_specific_data

# Copy templates and customize
cp job_summery.md.template user_specific_data/job_summery.md
cp job_skill_summery.md.template user_specific_data/job_skill_summery.md

# Edit the files with your job context and skills
```

#### 4. Run the Application
```bash
python email_manager_main.py
```

## 📁 Project Structure

```
email_helper/
├── email_manager_main.py # Main entry point (GUI)
├── src/                  # Application code
│   ├── unified_gui.py    # Unified GUI interface  
│   ├── ai_processor.py   # AI/prompty integration
│   ├── azure_config.py   # Secure Azure authentication
│   └── ...
├── prompts/              # AI prompt templates
│   ├── email_classifier_system.prompty
│   ├── email_one_line_summary.prompty
│   └── ...
├── user_specific_data/   # Your personal data (NOT COMMITTED)
│   ├── job_summery.md    # Your job context
│   └── job_skill_summery.md  # Your skills profile
├── .env                  # Environment variables (NOT COMMITTED)
├── .env.template         # Template for environment setup
└── requirements.txt      # Python dependencies
```

## 🔐 Security & Privacy

### What's NOT Committed to Git
- **`user_specific_data/`** - Your job context, skills, and personal information
- **`.env`** - Environment variables and API keys  
- **`*summary*.html`** - Generated email summaries (may contain sensitive content)
- **Azure credentials** - All authentication tokens and keys

### Authentication Methods (Priority Order)
1. **Azure DefaultCredential** (`az login`) - Most secure, no stored credentials
2. **Environment Variables** (`.env` file) - Secure fallback

## 📋 User-Specific Data Setup

The AI system needs to understand your job context and skills to classify emails accurately. These files contain your personal information and are kept private.

### Required Files (in `user_specific_data/`)

#### `job_summery.md`
Describe your role, responsibilities, and work focus areas:

```markdown
I am a Software Engineer working on Azure Compute Node Services, specifically:
- Your job role here
[Add your specific job context...]
```

#### `job_skill_summery.md` 
List your technical skills and learning interests:
```markdown
## Core Technical Skills
- Programming Languages: C#, Python, Go
- Cloud Platforms: Azure (Expert), AWS (Basic)
[Add your skills and interests...]
```

#### `username.txt`
Your username/email alias for personalized email classification:
```
your_username
```
*Note: This is used to identify emails sent directly to you vs. mass distribution.*

## 🎯 Features

- **Smart Email Classification**: Automatically categorizes emails into actionable categories
- **ADHD-Friendly Summaries**: Focused, concise summaries without distractions
- **Secure Authentication**: Multiple authentication options with security best practices
- **Learning System**: Improves classification accuracy based on your feedback - TODO: Currently stores this but does not learn from it yet
- **Customizable Categories**: Tailored to professional workflows and priorities

## 📖 Documentation

### Setup & Configuration
- **[Localhost Setup Guide](docs/LOCALHOST_SETUP.md)** - Complete localhost development setup
- **[Backend README](backend/README.md)** - Backend API documentation and setup
- **[Frontend README](frontend/README.md)** - React frontend documentation and setup
- [`SECURITY_SETUP.md`](SECURITY_SETUP.md) - Detailed security configuration guide
- [`scripts/README.md`](scripts/README.md) - Technical implementation details

### Additional Documentation
- **[Complete Documentation Index](docs/README.md)** - Start here for all documentation
- **[Quick Start Guide](QUICK_START.md)** - Get up and running quickly
- **[User Setup](docs/setup/USER_SETUP.md)** - Detailed setup instructions
- **[Feature Guides](docs/features/)** - Learn about specific features
- **[Technical Documentation](docs/technical/)** - Architecture and design details
- **[Test Documentation](test/TEST_ORGANIZATION.md)** - Testing guide and organization
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🐛 Troubleshooting

### Localhost Development Issues

**Backend won't start:**
```bash
# Check if port 8000 is already in use
netstat -ano | findstr :8000

# Verify Python dependencies are installed
pip install -r requirements.txt

# Check Outlook is installed and configured
```

**Frontend can't connect to backend:**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check .env.local has correct API URL
cat frontend/.env.local | grep VITE_API_BASE_URL

# Ensure CORS is configured in backend .env
```

**Outlook COM errors:**
- Ensure Microsoft Outlook is installed (2016 or later)
- Open Outlook manually to verify it works
- Run the application with administrator privileges
- Check Windows COM settings

> **📖 More Help:** See the [Troubleshooting Guide](docs/TROUBLESHOOTING.md) for comprehensive troubleshooting steps.

## � Testing

Run all tests with a single command:

```bash
npm test
# OR
.\run-all-tests.ps1
```

Run specific test suites:

```bash
npm run test:backend     # Backend Python tests
npm run test:src         # Src Python tests  
npm run test:frontend    # Frontend unit tests
npm run test:e2e         # Frontend E2E tests
npm run test:coverage    # All tests with coverage
```

For detailed testing documentation, see [`TEST_RUNNER_README.md`](TEST_RUNNER_README.md).

## � Contributing

This is a personal productivity tool, but improvements are welcome! Please ensure:

- No personal data in commits
- Security best practices maintained  
- Documentation updated for changes
- **Tests written and passing** - Run `npm test` before committing
- Follow guidelines in `.github/copilot-instructions.md`

## ⚠️ Important Notes

- **Never commit personal data** - The `.gitignore` protects you, but double-check
- **Review summaries before sharing** - Generated content may contain sensitive information
- **Keep authentication secure** - Use `az login` when possible, rotate API keys regularly
