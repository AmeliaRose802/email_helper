# User-Agnostic Email System Setup

This system has been updated to be user-agnostic, meaning anyone can use it by providing their own job context and classification rules without modifying the core code.

## What Changed

The following user-specific information has been moved from hardcoded prompts to configurable data files:

1. **Job role and responsibilities** - moved from `email_classifier_system.prompty`
2. **Technical keywords and work areas** - extracted to user data
3. **Classification rules** - now customizable per user
4. **Work context** - separated from AI logic

## Setup Instructions

### 1. Run the Setup Script

```powershell
cd scripts
python setup_user_data_templates.py
```

This will create template files in `user_specific_data/` directory.

### 2. Customize Your Data Files

Edit the following files with your specific information:

#### `user_specific_data/username.txt`
- Your email username (used for @mentions and direct email detection)

#### `user_specific_data/job_role_context.md`
- Your job title and primary responsibilities
- Technical areas you work on
- Keywords relevant to your work domain
- Special roles or duties

#### `user_specific_data/classification_rules.md`
- Customize email classification categories
- Adjust priority rules based on your work
- Modify the logic for what constitutes urgent vs optional

#### `user_specific_data/job_summery.md`
- High-level overview of your role
- Focus areas and key responsibilities

#### `user_specific_data/job_skill_summery.md`
- Technical skills and experience
- Programming languages, tools, frameworks
- Domain expertise

### 3. Security Considerations

⚠️ **IMPORTANT**: The user_specific_data/ directory is added to .gitignore automatically to prevent accidentally committing personal job information to version control.

## How It Works

The AI system now loads your user-specific data at runtime:

1. **Email Classification**: Uses your custom classification rules and job context
2. **Relevance Assessment**: Compares events/opportunities to your skills profile  
3. **Summary Generation**: Contextualizes emails based on your work priorities

## Files Modified

### Prompts Updated
- `prompts/email_classifier_system.prompty` - Now uses dynamic user data
- `prompts/summerize_action_item.prompty` - Removed hardcoded role reference

### Scripts Updated
- `scripts/ai_processor.py` - Added methods to load user-specific data
- `scripts/setup_user_data_templates.py` - New setup utility

### New User Data Files
- `user_specific_data/job_role_context.md` - Role and responsibility definitions
- `user_specific_data/classification_rules.md` - Email classification logic

## Usage

Once configured, run the system normally:

```powershell
cd scripts
python email_manager_main.py
```

The system will automatically load your user-specific data and use it for AI processing.

## Sharing and Collaboration

This system can now be safely shared with others because:

1. ✅ No hardcoded personal job information
2. ✅ User data is in separate, gitignored files  
3. ✅ Easy setup process for new users
4. ✅ Customizable for different roles and domains

New users just need to:
1. Clone the repository
2. Run the setup script
3. Fill in their job information
4. Start using the system
