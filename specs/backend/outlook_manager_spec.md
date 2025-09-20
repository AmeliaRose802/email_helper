# Outlook Manager Component Specification

**Last Updated:** January 15, 2025  
**File:** `src/outlook_manager.py`  
**Purpose:** Outlook COM automation and email management interface

## 🎯 Purpose

The OutlookManager provides a comprehensive interface to Microsoft Outlook through COM automation, enabling secure email retrieval, folder management, and email operations. It serves as the **OUTLOOK BRIDGE** between the application and the user's email data.

**CRITICAL:** This component enables all Outlook integration functionality. Without it, the system cannot access user emails or perform any email management operations.

## 🔧 Core Features

**CRITICAL: These features MUST NOT be removed or modified without user approval**

### 1. Outlook COM Connection Management

- **Purpose:** Establishes and maintains secure connection to Outlook application
- **Method:** `connect_to_outlook()` - MUST establish COM connection safely
- **Error Handling:** MUST handle Outlook not running, COM errors, and permission issues
- **Connection State:** MUST track connection status and provide reconnection capability
- **Security:** MUST respect Outlook security prompts and user permissions

### 2. Email Folder Navigation System

- **Purpose:** Provides access to all Outlook folders with hierarchy support
- **Method:** `get_folders()` - Returns complete folder structure
- **Folder Types:** MUST support Inbox, Sent, Drafts, custom folders, and shared mailboxes
- **Hierarchy:** MUST preserve parent-child folder relationships
- **Search:** MUST enable folder search by name and path

### 3. Email Retrieval and Filtering

- **Purpose:** Retrieves emails with flexible filtering and sorting options
- **Method:** `get_emails(folder_name, count, filter_criteria)` - Returns email collection
- **Filtering:** MUST support date ranges, sender filters, subject filters, read/unread status
- **Sorting:** MUST support chronological, sender, and subject sorting
- **Performance:** MUST handle large mailboxes efficiently with pagination

### 4. Email Property Access

- **Purpose:** Extracts all email properties including metadata and content
- **Method:** `get_email_properties(email)` - Returns comprehensive email data
- **Properties:** MUST include subject, sender, recipients, body, attachments, dates
- **Metadata:** MUST include categories, importance, read status, message ID
- **Content:** MUST handle both plain text and HTML email bodies

### 5. Email Categorization System

- **Purpose:** Manages Outlook categories for email organization
- **Method:** `apply_category(email, category)` - Assigns category to email
- **Category Management:** MUST create, modify, and delete custom categories
- **Color Coding:** MUST support Outlook's color-coded category system
- **Bulk Operations:** MUST support applying categories to multiple emails

### 6. Email Movement and Organization

- **Purpose:** Moves emails between folders for organization
- **Method:** `move_email(email, destination_folder)` - Relocates email safely
- **Folder Validation:** MUST verify destination folder exists and is accessible
- **Batch Moving:** MUST support moving multiple emails efficiently
- **Undo Support:** MUST provide information for potential undo operations

### 7. Email Status Management

- **Purpose:** Updates email read/unread status and importance flags
- **Method:** `mark_as_read(email)`, `mark_as_unread(email)` - Updates email status
- **Flag Management:** MUST support follow-up flags and importance levels
- **Synchronization:** MUST ensure status changes sync with Outlook server
- **Bulk Updates:** MUST support status changes for multiple emails

### 8. Search and Query Operations

- **Purpose:** Advanced email searching across all folders and timeframes
- **Method:** `search_emails(query, scope, timeframe)` - Returns matching emails
- **Query Types:** MUST support subject, sender, content, and metadata searches
- **Scope Control:** MUST search specific folders or entire mailbox
- **Performance:** MUST use Outlook's native search for optimal speed

## 📊 Data Structures

### Email Object Format

```python
{
    'subject': str,           # Email subject line
    'sender': str,            # Sender email address
    'sender_name': str,       # Sender display name
    'recipients': list,       # List of recipient email addresses
    'cc_recipients': list,    # CC recipient list
    'bcc_recipients': list,   # BCC recipient list (if available)
    'body_text': str,         # Plain text email body
    'body_html': str,         # HTML email body
    'received_time': datetime, # When email was received
    'sent_time': datetime,    # When email was sent
    'categories': list,       # Applied Outlook categories
    'importance': str,        # high/normal/low importance
    'read_status': bool,      # True if email has been read
    'has_attachments': bool,  # True if email has attachments
    'attachment_names': list, # List of attachment filenames
    'message_id': str,        # Unique Outlook message identifier
    'entry_id': str,          # Outlook entry ID for operations
    'store_id': str,          # Outlook store ID for location
    'folder_name': str,       # Name of containing folder
    'size': int,             # Email size in bytes
    'flag_status': str       # Follow-up flag status
}
```

### Folder Structure Format

```python
{
    'name': str,             # Folder display name
    'path': str,             # Full folder path
    'item_count': int,       # Number of items in folder
    'unread_count': int,     # Number of unread items
    'subfolders': list,      # List of child folder objects
    'folder_type': str,      # inbox/sent/drafts/custom/shared
    'parent_folder': str,    # Parent folder name (if any)
    'can_create_items': bool, # Whether new items can be created
    'can_delete_items': bool, # Whether items can be deleted
    'folder_id': str         # Unique Outlook folder identifier
}
```

### Category Definition Format

```python
{
    'name': str,             # Category name
    'color': str,            # Outlook color name or RGB value
    'shortcut_key': str,     # Keyboard shortcut (if assigned)
    'description': str,      # Category description
    'is_custom': bool,       # True if user-created category
    'usage_count': int       # Number of emails with this category
}
```

## 🔗 Dependencies

### External Dependencies

- **win32com.client:** Core COM automation for Outlook integration
- **pythoncom:** COM threading and error handling
- **datetime:** Date and time processing for email timestamps
- **logging:** Operation logging and error tracking

### Outlook Dependencies

- **Microsoft Outlook:** Must be installed and configured on system
- **MAPI:** Outlook's messaging API for advanced operations
- **Exchange/IMAP:** Email server connectivity for synchronization

### Internal Dependencies

- **Azure Configuration:** May use for logging and error reporting
- **Email Processor:** Provides processed email data for storage
- **Task Persistence:** Stores email operation results and metadata

## ⚠️ Preservation Notes

### NEVER Remove These Methods:

1. `__init__(self)` - Constructor MUST initialize COM connection
2. `connect_to_outlook()` - Core Outlook connection establishment
3. `get_folders()` - Folder structure retrieval
4. `get_emails(folder_name, count, filter_criteria)` - Email retrieval engine
5. `get_email_properties(email)` - Email property extraction
6. `apply_category(email, category)` - Email categorization
7. `move_email(email, destination_folder)` - Email movement operations
8. `mark_as_read(email)` - Email status management
9. `mark_as_unread(email)` - Email status management
10. `search_emails(query, scope, timeframe)` - Advanced email search

### NEVER Change These Attributes:

- `self.outlook_app` - Outlook application COM object
- `self.namespace` - MAPI namespace for email access
- `self.folders` - Cached folder structure
- `self.categories` - Available Outlook categories
- `self.connected` - Connection status flag

### NEVER Modify These Constants:

- Folder type constants: `INBOX`, `SENT`, `DRAFTS`, `CUSTOM`, `SHARED`
- Category color constants: Outlook color name mappings
- Email status constants: `READ`, `UNREAD`, `FLAGGED`, `COMPLETED`
- Importance level constants: `HIGH`, `NORMAL`, `LOW`

### NEVER Remove COM Error Handling:

- COM connection errors MUST be caught and handled gracefully
- Outlook permission prompts MUST be respected
- Network connectivity issues MUST be handled with appropriate retries
- Email access errors MUST provide meaningful user feedback

## 🧪 Validation

### Unit Tests Location

- Primary: `test/test_outlook_manager_comprehensive.py`
- Integration: `test/test_enhanced_ui_comprehensive.py`

### Manual Validation Steps

1. **Outlook Connection:** Verify connection establishment and error handling
2. **Folder Access:** Confirm all folders accessible, including shared mailboxes
3. **Email Retrieval:** Test with various filter criteria and large mailboxes
4. **Category Operations:** Verify category creation, application, and color management
5. **Email Movement:** Test moving emails between folders, including error cases
6. **Search Functionality:** Validate search accuracy across different query types
7. **Status Updates:** Confirm read/unread and flag status changes sync properly

### Success Criteria

- Outlook connection established without security prompt issues
- All user folders accessible with correct hierarchy and item counts
- Email retrieval handles large volumes (1000+ emails) efficiently
- Category operations complete successfully with visual confirmation in Outlook
- Email movements complete without data loss or duplication
- Search results match Outlook's native search functionality
- Status changes immediately reflect in Outlook interface

## 🚨 Integration Impact

### GUI Dependencies

- **Email Display:** Depends on email property format and structure
- **Folder Navigation:** Depends on folder structure format
- **Category Display:** Depends on category definition format
- **Status Indicators:** Depends on read status and flag information

### Data Flow Dependencies

- **Input:** User folder selections and filter criteria from GUI
- **Processing:** COM operations to retrieve and manipulate Outlook data
- **Output:** Structured email and folder data for GUI display
- **Synchronization:** Real-time updates between application and Outlook

### Breaking Changes Impact

- Changing email object structure breaks EmailProcessor integration
- Modifying folder format breaks GUI navigation components
- Removing methods breaks email management workflow
- Changing category format breaks AI classification integration

### Security Considerations

- COM operations MUST respect Outlook security model
- Email access MUST handle permission denied scenarios gracefully
- User credentials MUST NOT be stored or logged
- Email content MUST be handled securely in memory
- Network operations MUST handle connectivity issues appropriately

### Performance Considerations

- Large mailbox operations MUST use pagination and background processing
- COM calls MUST be minimized to reduce Outlook performance impact
- Email caching MUST balance memory usage with access speed
- Background updates MUST not interfere with user's Outlook usage

---

**🛡️ CRITICAL REMINDER: This component is the foundation of all email access functionality. Any changes that break Outlook integration will render the entire application non-functional.**