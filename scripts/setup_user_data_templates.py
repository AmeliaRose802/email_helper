#!/usr/bin/env python3
"""
User Data Setup Script - Creates template files for user-specific data
"""

import os
import shutil

def setup_user_data():
    """Set up user-specific data files from templates"""
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    user_data_dir = os.path.join(project_root, 'user_specific_data')
    
    # Ensure user_specific_data directory exists
    os.makedirs(user_data_dir, exist_ok=True)
    
    print("🔧 Setting up user-specific data files...")
    print("=" * 50)
    
    # List of files to check/create
    user_files = {
        'username.txt': 'your-email-username-here',
        'job_role_context.md': '''# Job Role Context

## Role Title
[Your Job Title]

## Primary Responsibilities

### Core Work Areas
- [List your main work responsibilities]
- [Include specific technical areas you work on]
- [Add any security or compliance duties]

### Technical Keywords
- [List technical terms and keywords relevant to your work]
- [Include service names, tools, and technologies you use]
- [Add any acronyms or domain-specific terms]

## Work Context Notes
- [Add notes about your work context]
- [Include information about your team/domain]
- [Note any special responsibilities or roles]
''',
        'classification_rules.md': '''# Email Classification Rules

## Categories and Priorities

### High Priority Categories

#### REQUIRED_PERSONAL_ACTION
- Direct personal communication requiring immediate action
- Emails sent directly TO {{username}} (not CC/BCC) from non-automated accounts  
- Emails where {{username}} is @ mentioned requiring response
- Personal surveys or feedback requests with deadlines
- Manager communications requiring action
- Core work responsibilities needing personal action (see job role context)

#### TEAM_ACTION
- Code reviews and technical discussions
- Partner team coordination
- Debugging sessions and technical failures requiring group effort
- Performance diagnostics requiring team input
- Infrastructure issues needing team input
- Technical content requiring team review

### Medium Priority Categories

#### OPTIONAL_ACTION
- Optional surveys and feedback requests
- Training requests related to role but not mandatory
- Documentation improvements (optional participation)
- Quality initiatives you can contribute to but aren't required

#### JOB_LISTING
- Job postings and career opportunities
- Internal role notifications
- Recruitment emails

#### OPTIONAL_EVENT
- Webinars, conferences, invitations
- Technical presentations and demos
- Networking events and connection calls
- Training sessions and skill development opportunities

### Low Priority Categories

#### WORK_RELEVANT
- Technical emails containing work-relevant keywords (see job role context)
- Email threads previously participated in (for reference)
- Technical documentation
- Performance reports and diagnostics (for awareness)
- Work-related announcements
- Security updates and compliance information (informational)

#### SPAM_TO_DELETE
- Automated reports with no direct relevance
- Empty status reports with 0 issues found
- Mass distribution lists without work relevance
- Generic announcements without technical context
- External marketing emails
- Content outside work domain
- Past meeting invites with no ongoing relevance

## Classification Logic

1. **First Priority**: Check for personal action items related to core work areas
2. **Second Priority**: Identify team collaboration needs and technical discussions  
3. **Third Priority**: Categorize optional activities, events, and reference material
4. **Default**: If clearly promotional, automated nonsense, or out-of-scope → spam_to_delete
''',
        'job_summery.md': '''---
name: Job Role Summary  
description: Role focus and responsibilities
version: 1.0
tags: [job-context, work-focus]
---

# Role Focus

- [Describe your primary role and responsibilities]
- [Include main technical areas you work on]
- [Add any special duties or roles]
- [Note your involvement in processes like code reviews, incident response, etc.]
''',
        'job_skill_summery.md': '''# Job Skills Summary

**Role:** [Your Role Title]
**Years of experience:** [X]
**Domain:** [Your main domain/area]

## Education

- [Your education background]
- [Any relevant coursework]

## Core Technical Skills

- **Programming Languages:** [List languages]
- **Frameworks & Protocols:** [List frameworks]
- **Cloud & Infrastructure:** [Cloud platforms/tools]
- **Security & Compliance:** [Security tools/knowledge]
- **DevOps & Automation:** [DevOps tools/practices]
- **Monitoring & Observability:** [Monitoring tools]

## Collaboration & Program Experience

- [Team collaboration experience]
- [Cross-team coordination]
- [Process contributions]
'''
    }
    
    # Check each file and create if missing
    for filename, template_content in user_files.items():
        filepath = os.path.join(user_data_dir, filename)
        
        if os.path.exists(filepath):
            print(f"✅ {filename} already exists")
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template_content)
            print(f"📝 Created template: {filename}")
    
    print(f"\n📁 User data directory: {user_data_dir}")
    print("\n📝 NEXT STEPS:")
    print("1. Edit the template files in user_specific_data/ with your information")
    print("2. Replace placeholder text with your actual job details")
    print("3. Customize classification rules based on your work priorities")
    print("4. Update technical keywords relevant to your domain")
    print("\n⚠️  DO NOT commit these files to version control if they contain sensitive information!")
    
    # Check if .gitignore exists and add user_specific_data if not present
    gitignore_path = os.path.join(project_root, '.gitignore')
    gitignore_entry = "user_specific_data/"
    
    gitignore_exists = os.path.exists(gitignore_path)
    entry_exists = False
    
    if gitignore_exists:
        with open(gitignore_path, 'r') as f:
            content = f.read()
            entry_exists = gitignore_entry in content
    
    if not entry_exists:
        with open(gitignore_path, 'a' if gitignore_exists else 'w') as f:
            if gitignore_exists:
                f.write('\n')
            f.write(f"# User-specific data (contains personal job information)\n{gitignore_entry}\n")
        print(f"✅ Added {gitignore_entry} to .gitignore")
    else:
        print("✅ .gitignore already contains user_specific_data/")

if __name__ == "__main__":
    setup_user_data()
