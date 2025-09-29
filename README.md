# Email Helper - AI-Powered Email Management System

This repo is an experiment in vibe codign with no human intervention. Please do not take it as reflective of my general code quality practices

An intelligent email classification and management system designed for professionals with ADHD who need focused, actionable email summaries.

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Azure Authentication
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

### 3. Set Up Personal Configuration
```bash
# Create user-specific data directory (if not exists)
mkdir user_specific_data

# Copy templates and customize
cp job_summery.md.template user_specific_data/job_summery.md
cp job_skill_summery.md.template user_specific_data/job_skill_summery.md

# Edit the files with your job context and skills
```

### 4. Run the Application
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

- [`SECURITY_SETUP.md`](SECURITY_SETUP.md) - Detailed security configuration guide
- [`scripts/README.md`](scripts/README.md) - Technical implementation details
- [`docs/`](docs/) - Additional documentation and guides

## 🛠️ Development

### Adding New Categories

1. Update prompts in `prompts/email_classifier_system.prompty`
2. Update documentation

### Customizing Prompts
All AI prompts are in the `prompts/` directory using Microsoft Prompty format. Edit these files to customize the AI behavior for your specific needs.

## 🤝 Contributing

This is a personal productivity tool, but improvements are welcome! Please ensure:
- No personal data in commits
- Security best practices maintained  
- Documentation updated for changes

## ⚠️ Important Notes

- **Never commit personal data** - The `.gitignore` protects you, but double-check
- **Review summaries before sharing** - Generated content may contain sensitive information
- **Keep authentication secure** - Use `az login` when possible, rotate API keys regularly
