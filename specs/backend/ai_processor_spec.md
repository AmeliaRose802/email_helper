# AI Processor Component Specification

**Last Updated:** January 15, 2025  
**File:** `src/ai_processor.py`  
**Purpose:** Azure OpenAI integration and AI-powered email analysis

## 🎯 Purpose

The AIProcessor manages all interactions with Azure OpenAI services to provide intelligent email classification, summarization, and action item extraction. It serves as the **AI BRAIN** of the email management system.

**CRITICAL:** This component enables the core AI functionality that makes the email manager intelligent. Without it, the system becomes a basic email viewer.

## 🔧 Core Features

**CRITICAL: These features MUST NOT be removed or modified without user approval**

### 1. Azure OpenAI Configuration Management
- **Purpose:** Manages secure Azure OpenAI API connections and credentials
- **Method:** `__init__()` - Loads configuration from `azure_config.py`
- **Security:** MUST protect API keys and endpoints from exposure
- **Validation:** MUST verify connection before processing emails
- **Configuration Keys:** `endpoint`, `api_key`, `deployment_name`, `api_version`

### 2. Email Classification System
- **Purpose:** Categorizes emails using AI analysis with prompty templates
- **Method:** `classify_email(email_content, subject, sender)` - MUST return valid category
- **Templates:** Uses `prompts/email_classifier_system.prompty` for consistent AI responses
- **Categories:** Returns one of: `required_action`, `team_action`, `optional_action`, `fyi`, `newsletter`, `job_listing`
- **Fallback:** Returns `fyi` if AI service fails or returns invalid category

### 3. Email Summarization Engine
- **Purpose:** Generates concise, actionable summaries of email content
- **Method:** `summarize_email(email_content)` - MUST return human-readable summary
- **Template:** Uses `prompts/email_one_line_summary.prompty` for consistency
- **Length:** Summaries MUST be concise (1-2 sentences) for UI display
- **Content:** MUST capture key action items and important details

### 4. Action Item Detection
- **Purpose:** Identifies specific actions required from email content
- **Method:** `extract_action_items(email_content)` - Returns structured action data
- **Template:** Uses `prompts/summerize_action_item.prompty` for extraction
- **Output:** MUST include action description, deadline (if any), and urgency level
- **Safety:** MUST handle emails with no clear action items gracefully

### 5. FYI Content Summarization
- **Purpose:** Creates informational summaries for non-actionable emails
- **Method:** `generate_fyi_summary(email_content)` - Returns informational summary
- **Template:** Uses `prompts/fyi_summary.prompty` for FYI-specific formatting
- **Focus:** Emphasizes key information without action requirements
- **Use Case:** News updates, announcements, informational content

### 6. Newsletter Processing
- **Purpose:** Specialized processing for newsletter and bulk email content
- **Method:** `process_newsletter(email_content)` - Returns newsletter-specific summary
- **Template:** Uses `prompts/newsletter_summary.prompty` for newsletter formatting
- **Extraction:** MUST identify key topics and important announcements
- **Filtering:** MUST distinguish between promotional and informational content

### 7. Job Listing Analysis
- **Purpose:** Analyzes job postings for relevance and qualification matching
- **Method:** `analyze_job_listing(email_content)` - Returns job analysis data
- **Skills Matching:** Compares job requirements to user skills (if configured)
- **Relevance Score:** MUST provide percentage match or relevance rating
- **Key Details:** Extracts position, company, requirements, and application deadline

### 8. Holistic Inbox Analysis
- **Purpose:** Provides overall inbox analysis and insights across multiple emails
- **Method:** `analyze_inbox_holistically(emails)` - Returns comprehensive analysis
- **Template:** Uses `prompts/holistic_inbox_analyzer.prompty` for batch analysis
- **Insights:** Identifies patterns, urgency trends, and workflow recommendations
- **Scope:** Analyzes batches of emails for broader context and prioritization

## 📊 Data Structures

### Azure Configuration Format
```python
{
    'endpoint': str,        # Azure OpenAI endpoint URL
    'api_key': str,         # Azure OpenAI API key
    'deployment_name': str, # Model deployment name
    'api_version': str,     # API version (e.g., "2023-12-01-preview")
    'model': str           # Model name (e.g., "gpt-4")
}
```

### Classification Result Format
```python
{
    'category': str,           # Primary category classification
    'confidence': float,       # Confidence score (0.0-1.0)
    'reasoning': str,          # AI explanation for classification
    'alternative_categories': list,  # Other possible categories
    'processing_time': float   # Time taken for classification
}
```

### Action Item Result Format
```python
{
    'action_required': str,    # Specific action description
    'deadline': str or None,   # Extracted deadline (ISO format)
    'urgency': str,           # high/medium/low urgency level
    'assignee': str or None,  # Who should take action (if specified)
    'context': str,           # Additional context or notes
    'estimated_time': str     # Estimated time to complete (if available)
}
```

### Summary Result Format
```python
{
    'summary': str,           # Main summary text
    'key_points': list,       # Important points as bullet items
    'sentiment': str,         # positive/neutral/negative/urgent
    'topics': list,           # Main topics or themes
    'entities': list          # Important names, dates, locations
}
```

## 🔗 Dependencies

### Required Configuration
- **azure_config.py:** Azure OpenAI connection settings and credentials
- **prompts/*.prompty:** AI prompt templates for consistent processing

### External Dependencies
- **prompty:** Template execution engine for AI prompts
- **openai:** Azure OpenAI client library
- **requests:** HTTP client for API communication
- **json:** Response parsing and data serialization

### Template Dependencies
- `email_classifier_system.prompty` - Email categorization prompts
- `email_one_line_summary.prompty` - Email summarization prompts
- `summerize_action_item.prompty` - Action item extraction prompts
- `fyi_summary.prompty` - FYI content summarization prompts
- `newsletter_summary.prompty` - Newsletter processing prompts
- `holistic_inbox_analyzer.prompty` - Batch analysis prompts

## ⚠️ Preservation Notes

### NEVER Remove These Methods:
1. `__init__(self)` - Constructor MUST load Azure configuration
2. `classify_email(email_content, subject, sender)` - Core classification functionality
3. `summarize_email(email_content)` - Email summarization engine
4. `extract_action_items(email_content)` - Action item detection
5. `generate_fyi_summary(email_content)` - FYI content processing
6. `process_newsletter(email_content)` - Newsletter analysis
7. `analyze_job_listing(email_content)` - Job posting analysis
8. `analyze_inbox_holistically(emails)` - Batch inbox analysis

### NEVER Change These Attributes:
- `self.azure_config` - Azure OpenAI configuration dictionary
- `self.client` - Azure OpenAI client instance
- `self.prompty_templates` - Loaded prompt templates cache

### NEVER Modify These Category Constants:
- `required_action` - Personal action items requiring user action
- `team_action` - Team-related actions and coordination
- `optional_action` - Optional activities and events
- `fyi` - Informational content with no action required
- `newsletter` - Newsletter and bulk informational content
- `job_listing` - Job opportunities and career-related content

### NEVER Remove Prompty Template Usage:
- Template execution MUST use prompty engine for consistency
- Prompt modifications MUST be done in .prompty files, not hardcoded
- Template loading MUST handle missing template files gracefully
- Response parsing MUST handle AI service failures and unexpected responses

## 🧪 Validation

### Unit Tests Location
- Primary: `test/test_ai_processor_comprehensive.py`
- Integration: `test/test_enhanced_ui_comprehensive.py`

### Manual Validation Steps
1. **Azure Connection:** Verify connection to Azure OpenAI service
2. **Classification Accuracy:** Test with various email types, verify correct categories
3. **Summary Quality:** Confirm summaries are concise and capture key information
4. **Action Extraction:** Verify action items include all required fields
5. **Error Handling:** Test with malformed content, verify graceful failure
6. **Template Loading:** Confirm all prompty templates load correctly
7. **Response Parsing:** Test with various AI response formats

### Success Criteria
- Azure OpenAI connection established successfully
- Email classification returns valid categories with >80% accuracy
- Summaries are concise (1-2 sentences) and informative
- Action items include action description, deadline (when available), urgency
- System handles AI service failures without crashing
- All prompty templates load and execute successfully
- Response parsing handles unexpected AI outputs gracefully

## 🚨 Integration Impact

### GUI Dependencies
- **Category Display:** Depends on classification category constants
- **Summary Display:** Depends on summary format and structure
- **Action Lists:** Depends on action item data structure
- **Progress Tracking:** Depends on processing time estimates

### Data Flow Dependencies
- **Input:** Raw email content from EmailProcessor
- **Processing:** Azure OpenAI API calls via prompty templates
- **Output:** Structured classification and analysis data
- **Storage:** Results cached for subsequent GUI display

### Breaking Changes Impact
- Changing category names breaks EmailProcessor categorization logic
- Modifying data structures breaks GUI display components
- Removing methods breaks EmailProcessor workflow integration
- Changing Azure configuration format breaks initialization

### Security Considerations
- API keys MUST be stored securely in azure_config.py
- API responses MUST be validated before processing
- Error messages MUST NOT expose sensitive configuration details
- Network failures MUST be handled gracefully with appropriate user feedback

---

**🛡️ CRITICAL REMINDER: This component provides the AI intelligence that makes the email manager valuable. All features must be preserved to maintain the system's core value proposition.**