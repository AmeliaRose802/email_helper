# Email Categorization Rules
Based on Amelia's Few-Shot Examples and Work Patterns

## Category Definitions

### 1. 🔴 REQUIRED ACTION ITEMS
**Folder**: Keep in Inbox
**Action**: Generate summary with action required

- **Surveys and Feedback**
  - Overlakees survey requests
  - Feedback collection emails
  - DRI requests for input
  
- **Training and Development**
  - Required training notifications
  - Skills assessment requests
  
- **Work Process Items**
  - Outage management processes
  - Policy updates requiring acknowledgment

**Summary Format:**
- Subject line with action required
- Due date (if specified)
- Links to complete action
- Brief explanation of what's needed

### 2. 💼 JOB LISTINGS
**Folder**: job_listings
**Action**: Analyze for qualification match

- **Keywords**: position, job, role, hiring, career, rewards received
- **Specific Roles**: Copilot extensibility, Program Manager, Customer Experience
- **Context**: "Looking around" or career opportunity emails

**Summary Format:**
- Role title and company
- Key qualifications mentioned
- Match assessment to current skills
- Application deadline (if provided)
- Links to apply

### 3. 📊 SUMMARIES TO REVIEW
**Folder**: summarized
**Action**: Extract key points and action items

- **Weekly/Monthly Updates**
  - End of week summaries
  - Azure Core team updates
  - Core team communications
  
- **Technical Summaries**
  - Project status updates
  - Technical decision summaries

**Summary Format:**
- Key achievements/progress
- Action items for follow-up
- Important dates or deadlines
- Links to detailed information

### 4. 🌐 WHAT'S GOING ON
**Folder**: whats_going_on
**Action**: Brief note for awareness

- **Events and Invitations**
  - Gleam invitations
  - Connection calls
  - Webinars and events
  - Lightning talks (if no specific topic)

**Summary Format:**
- Event name and date
- Brief description
- Optional attendance note

### 5. ⚡ WORK-RELEVANT (Stay in Inbox)
**Folder**: Inbox (no move)
**Action**: Keep for active work

- **Technical Work**
  - Ubuntu, vulnerability reports
  - Host gateway, IMDS, WireServer
  - Azure Compute issues
  - Security-related communications
  - AHG (Azure Host Gateway) work
  
- **Team Communications**
  - M1 team discussions
  - Re: threads on technical topics
  - Debug and issue resolution
  
- **Lightning Talks with Content**
  - Lightning talks with specific topics (not "no topic")

### 6. 🔧 AUTOMATED NOTIFICATIONS
**Folder**: automated
**Action**: File for reference, no summary

- **System Notifications**
  - "Joined the team" messages
  - S360 KPI reports
  - Automated onboarding templates
  - System-generated updates

### 7. 💰 FINANCIAL IMPORTANT
**Folder**: Keep in Inbox
**Action**: Flag for attention

- **Stock and Compensation**
  - Stock vesting notifications
  - Award confirmations
  - Financial service updates

### 8. 🗑️ SPAM TO DELETE
**Folder**: ai_deleted
**Action**: Remove from summary

- **External Marketing**
  - Upskill promotions
  - Season-related marketing
  - BMI stats (irrelevant)
  - Flow and other external tools
  
- **Low-Value External**
  - Email addresses with @email., @marketing, @no-reply
  - Generic promotional content

## Summary Generation Rules

### Action Items Format:
```
**[Subject Line]**
From: [Sender]
Due: [Date if specified, otherwise "No specific deadline"]
Action: [What needs to be done]
Links: [Relevant URLs]
Priority: [High/Medium/Low based on urgency]
```

### Job Listings Format:
```
**[Role Title] at [Company]**
Qualifications: [Key requirements]
Match Assessment: [How well you fit]
Application: [Link and deadline]
Notes: [Additional relevant info]
```

### Work Summaries Format:
```
**[Team/Project Name] Update**
Key Points:
- [Important point 1]
- [Important point 2]
Action Items:
- [What you need to do]
Next Steps: [Timeline information]
```

## Decision Logic Priority

1. **Financial** → Always keep in inbox, high priority
2. **Action Items** → Keep in inbox, create action summary
3. **Work-Relevant Technical** → Keep in inbox for active work
4. **Job Listings** → Move to folder, analyze qualifications
5. **Team Summaries** → Move to summarized, extract key points
6. **Events/Social** → Move to whats_going_on, brief note
7. **Automated** → Move to automated folder, minimal processing
8. **Spam/External** → Move to ai_deleted, exclude from summary

## Quality Assurance Rules

- **Conservative Approach**: When in doubt, categorize as work-relevant
- **Context Matters**: Consider sender, time of day, and email thread
- **Learning Integration**: Use previous user feedback to refine categories
- **Link Preservation**: Always include relevant links in summaries
- **Date Extraction**: Parse due dates and deadlines from email content
- **Thread Awareness**: Consider email chains and reply context
