# Email Processor Component Specification

**Last Updated:** January 15, 2025  
**File:** `src/email_processor.py`  
**Purpose:** Core email processing, categorization, and workflow management

## 🎯 Purpose

The EmailProcessor is the **CENTRAL ORCHESTRATOR** of the email management system. It coordinates between Outlook, AI processing, email analysis, and summary generation to provide intelligent email categorization and action item extraction.

**CRITICAL:** This component is the backbone of the entire application. Removing or modifying its core features will break the entire email management workflow.

## 🔧 Core Features

**CRITICAL: These features MUST NOT be removed or modified without user approval**

### 1. Email Categorization System
- **Purpose:** Automatically categorizes emails into actionable categories
- **Categories:** `required_action`, `team_action`, `optional_action`, `fyi`, `newsletter`, `job_listing`
- **Method:** `categorize_email(email)` - MUST return valid category
- **Validation:** Each email MUST receive exactly one category classification
- **Fallback:** Defaults to `fyi` if AI classification fails

### 2. Deduplication System
- **Purpose:** Prevents processing duplicate emails
- **Method:** `_is_duplicate(email, existing_emails)` - MUST return boolean
- **Logic:** Compares subject lines and sender email addresses
- **Protection:** Prevents infinite processing loops and duplicate action items
- **Storage:** Maintains internal `processed_emails` tracking

### 3. Action Item Extraction
- **Purpose:** Extracts actionable tasks from categorized emails
- **Method:** `extract_action_items(emails)` - MUST return structured action data
- **Output Format:** Dictionary with keys: `required_actions`, `team_actions`, `optional_actions`, `job_listings`, `fyi_items`
- **Data Persistence:** All action items MUST include unique `task_id` for tracking

### 4. Email Content Processing
- **Purpose:** Cleans and prepares email content for AI analysis
- **Method:** `_clean_email_content(body)` - MUST handle HTML, attachments, signatures
- **Safety:** MUST handle malformed or empty email bodies gracefully
- **Character Encoding:** MUST handle various email encodings (UTF-8, ASCII, etc.)

### 5. Thread Analysis Integration
- **Purpose:** Groups related emails and maintains conversation context
- **Method:** `_analyze_email_threads(emails)` - MUST group by conversation
- **Data Structure:** Each email MUST include `thread_data` with count and relationships
- **Use Case:** Prevents duplicate action items from email conversations

### 6. Batch Processing System
- **Purpose:** Processes multiple emails efficiently with progress tracking
- **Method:** `process_emails(emails, progress_callback=None)` - MUST support cancellation
- **Progress Tracking:** Reports percentage complete via callback function
- **Cancellation:** MUST respond to `self.cancelled` flag for user cancellation
- **Error Recovery:** MUST continue processing other emails if one fails

## 📊 Data Structures

### Email Data Format (Input)
```python
{
    'subject': str,           # REQUIRED - Email subject line
    'body': str,             # REQUIRED - Email body content  
    'sender': str,           # REQUIRED - Sender email address
    'sender_name': str,      # OPTIONAL - Sender display name
    'received_time': str,    # REQUIRED - ISO format timestamp
    'entry_id': str,         # REQUIRED - Outlook unique identifier
    'store_id': str,         # REQUIRED - Outlook store identifier
    'folder_name': str       # REQUIRED - Source folder name
}
```

### Email Suggestion Format (Output)
```python
{
    'email_data': dict,             # Original email data
    'ai_suggestion': str,           # AI-recommended category
    'initial_classification': str,  # First AI classification
    'ai_summary': str,             # AI-generated summary
    'processing_notes': list,      # Processing status messages
    'thread_data': dict,           # Thread analysis results
    'action_item': dict or None    # Extracted action item if applicable
}
```

### Action Items Data Format
```python
{
    'required_actions': [
        {
            'subject': str,          # Email subject
            'sender': str,           # Sender email
            'due_date': str,         # Extracted or default deadline
            'action_required': str,  # Specific action description
            'explanation': str,      # AI explanation of action
            'task_id': str,         # Unique task identifier
            'batch_count': int,     # Processing batch number
            'priority': str         # high/medium/low priority
        }
    ],
    'team_actions': [...],      # Same structure for team actions
    'optional_actions': [...],  # Same structure for optional actions
    'job_listings': [...],      # Job-specific fields
    'fyi_items': [...]         # FYI-specific fields
}
```

## 🔗 Dependencies

### Required Components
- **OutlookManager:** Email retrieval and folder operations
- **AIProcessor:** Email classification and summarization  
- **EmailAnalyzer:** Content analysis and action extraction
- **SummaryGenerator:** Summary formatting and display
- **TaskPersistence:** Action item storage and retrieval

### External Dependencies
- **prompty:** AI prompt template execution
- **datetime:** Timestamp processing and date calculations
- **re:** Regular expression for content cleaning
- **json:** Data serialization for storage

## ⚠️ Preservation Notes

### NEVER Remove These Methods:
1. `__init__(self, outlook_manager, ai_processor, email_analyzer, summary_generator)` - Constructor MUST accept all four dependencies
2. `process_emails(emails, progress_callback=None)` - Main processing entry point
3. `categorize_email(email)` - Core categorization logic
4. `extract_action_items(emails)` - Action item extraction
5. `get_action_items_data()` - Data accessor for GUI
6. `_is_duplicate(email, existing_emails)` - Deduplication protection
7. `_clean_email_content(body)` - Content sanitization

### NEVER Change These Attributes:
- `self.outlook_manager` - Outlook integration reference
- `self.ai_processor` - AI processing reference  
- `self.email_analyzer` - Analysis component reference
- `self.summary_generator` - Summary component reference
- `self.processed_emails` - Deduplication tracking list
- `self.cancelled` - Processing cancellation flag

### NEVER Modify These Category Names:
- `required_action` - Personal action items
- `team_action` - Team coordination items
- `optional_action` - Optional activities
- `fyi` - Informational items
- `newsletter` - Newsletter content
- `job_listing` - Job opportunities

## 🧪 Validation

### Unit Tests Location
- Primary: `test/test_email_processor_comprehensive.py`
- Integration: `test/test_enhanced_ui_comprehensive.py`

### Manual Validation Steps
1. **Email Processing:** Feed test emails, verify categorization accuracy
2. **Deduplication:** Send duplicate emails, confirm only one is processed
3. **Action Extraction:** Verify action items are created with all required fields
4. **Progress Tracking:** Confirm progress callbacks work during batch processing
5. **Cancellation:** Test that processing stops when `cancelled` flag is set
6. **Error Handling:** Verify graceful handling of malformed email data

### Success Criteria
- All emails receive valid category classifications
- No duplicate emails are processed twice
- Action items include all required fields (`task_id`, `subject`, `sender`, etc.)
- Progress callbacks report accurate completion percentages
- Processing stops immediately when cancelled
- System continues processing after individual email failures

## 🚨 Integration Impact

### GUI Dependencies
- **Email Tree Display:** Depends on email suggestion format for display
- **Progress Bar:** Depends on progress callback mechanism
- **Category Editing:** Depends on category name constants
- **Action Summary:** Depends on action items data structure

### Data Flow Dependencies
- **Input:** Raw emails from OutlookManager
- **Processing:** AI categorization via AIProcessor
- **Analysis:** Action extraction via EmailAnalyzer  
- **Output:** Structured action items for TaskPersistence
- **Display:** Formatted data for GUI components

### Breaking Changes Impact
- Changing category names breaks GUI dropdown and display logic
- Modifying data structures breaks GUI display and data persistence
- Removing methods breaks GUI event handlers and workflow logic
- Changing constructor parameters breaks application initialization

---

**🛡️ CRITICAL REMINDER: This component orchestrates the entire email processing workflow. Any changes must preserve all listed features and maintain data structure compatibility with dependent components.**