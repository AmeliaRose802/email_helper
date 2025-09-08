# Unified Email Management GUI - User Guide

## Overview

The new unified email management GUI provides a complete workflow for processing emails in a single interface. No more switching between command line and GUI - everything is integrated into one seamless experience.

## Complete Workflow

### 1. Launch the Application

Run the main entry point:
```bash
python email_manager_main.py
```

The application will:
- Connect to Outlook automatically
- Display a modern tabbed interface
- Show three main workflow tabs

### 2. Tab 1: Process Emails

**Features:**
- Select number of emails to process (25, 50, 100, 200, or custom)
- Real-time processing with live progress updates
- Background processing with cancellation support
- Detailed progress log showing each email as it's processed

**Steps:**
1. Choose email count (recommended: 50 for first use)
2. Click "🚀 Start Processing Emails"
3. Watch real-time progress as emails are analyzed
4. See AI classification for each conversation
5. Tab 2 automatically becomes available when complete

### 3. Tab 2: Review & Edit

**Features:**
- View all processed emails in a clean list
- See AI categories with thread information
- Edit individual classifications with explanations
- Apply changes to Outlook directly
- Real-time preview of email content

**Email List Columns:**
- **Subject**: Email subject (shows 🧵 for conversation threads)
- **From**: Sender or participant count for threads
- **Category**: AI-assigned category
- **Date**: Received date

**Editing Process:**
1. Click on any email in the list
2. Review details in the right panel
3. Change category if needed using dropdown
4. Provide reason for change
5. Click "✅ Apply Change"

**Actions Available:**
- 🔄 Refresh List: Reload the email list
- ✅ Apply to Outlook: Apply all categories to your Outlook emails
- ➡️ Generate Summary: Proceed to summary generation

### 4. Tab 3: Summary & Results

**Features:**
- Generate comprehensive HTML summary
- Preview summary content in-app
- Open full summary in browser
- Start new processing session

**Summary Generation:**
1. Click "📋 Generate Summary"
2. View preview in the text area
3. Click "🌐 Open in Browser" for full HTML view
4. Use "🔄 Process New Batch" to start over

## Key Features

### Real-Time Processing
- Watch emails being processed live
- Cancel processing at any time
- Clear progress indicators and status updates

### Thread Awareness
- Automatically groups conversation threads
- Shows participant counts and thread context
- AI analyzes full conversation context for better categorization

### Integrated Workflow
- No switching between interfaces
- All data flows seamlessly between tabs
- Complete audit trail of changes

### Error Handling
- Graceful error handling with user-friendly messages
- Connection status monitoring
- Automatic recovery capabilities

## Categories Supported

The system recognizes and processes these email categories:

1. **Required Personal Action** - Emails requiring immediate action from you
2. **Team Action** - Emails requiring team coordination or response  
3. **Optional Action** - Emails with optional actions or feedback requests
4. **Job Listing** - Job opportunities and career-related emails
5. **Optional Event** - Meeting invites, conferences, and optional events
6. **FYI Notice** - Informational notices and updates
7. **Newsletter** - Newsletters and periodic updates
8. **Work Relevant** - General work-related informational content
9. **Spam To Delete** - Emails marked for deletion

## Summary Sections

The generated summary includes:

- **Overview Statistics** - Total items and high priority count
- **Required Action Items (ME)** - Your urgent tasks with due dates
- **Team Action Items** - Items requiring team coordination  
- **Optional Action Items** - Optional tasks and feedback requests
- **Job Listings** - Career opportunities with match assessments
- **Optional Events** - Events with relevance analysis
- **FYI Notices** - Bullet-pointed informational updates
- **Newsletter Summary** - Consolidated newsletter highlights

## Tips for Best Results

1. **Start Small**: Begin with 25-50 emails for your first session
2. **Review Categories**: Check a few classifications and correct if needed to improve AI learning
3. **Thread Context**: The system considers full conversation history for better categorization
4. **Regular Use**: Use regularly to build up AI accuracy through feedback

## Troubleshooting

### Common Issues

**"Failed to connect to Outlook"**
- Ensure Microsoft Outlook is installed and running
- Check that your email account is properly configured
- Try restarting Outlook

**"Processing failed"**
- Check your internet connection
- Verify Azure OpenAI credentials are configured
- Ensure sufficient API quota

**"No emails found"**
- Check that you have emails in your inbox
- Verify date range settings
- Try increasing the email count

### Getting Help

If you encounter issues:
1. Check the status bar for error messages
2. Review the progress log for detailed error information
3. Try cancelling and restarting processing
4. Restart the application if needed

## Performance Notes

- Processing time: ~2-3 seconds per email/conversation
- Memory usage increases with email count
- Browser opens automatically for summary viewing
- All data is saved locally for future reference

Enjoy the streamlined email management experience! 🚀
