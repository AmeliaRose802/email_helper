# GitHub Copilot Instructions for Email Helper Project

## Project Overview

This is an intelligent email management system that helps users process, categorize, and summarize emails from their Outlook inbox. The system uses AI to analyze emails, extract action items, and provide focused summaries.

## Key Architecture Components

### Core Modules

- `email_manager_main.py` - Main entry point and orchestration
- `src/outlook_manager.py` - Outlook integration and email retrieval
- `src/ai_processor.py` - AI analysis and processing logic
- `src/email_analyzer.py` - Email content analysis and categorization
- `src/summary_generator.py` - Summary generation and formatting
- `src/unified_gui.py` - User interface components
- `src/task_persistence.py` - Task management and persistence

### Data Flow

1. Connect to Outlook and retrieve emails
2. Analyze and categorize emails using AI
3. Extract action items and generate summaries
4. Store results in database for persistence
5. Present results through GUI interface

## Coding Standards

### Python Style

- Follow PEP 8 conventions
- Use type hints where appropriate
- Include comprehensive docstrings for all functions and classes
- Use descriptive variable and function names
- Prefer composition over inheritance

### Error Handling

- Use try-catch blocks for external API calls
- Implement graceful degradation for AI service failures
- Log errors appropriately using the existing logging infrastructure
- Provide user-friendly error messages in GUI components

### Testing

- Write unit tests for new functionality in the `test/` directory
- Follow existing test patterns and naming conventions
- Include both positive and negative test cases
- Mock external dependencies (Outlook, AI services)

## Dependencies & Integration

### External Services

- **Microsoft Graph API** - For Outlook email access
- **Azure OpenAI** - For AI processing and analysis
- **SQLite Database** - For local data persistence

### Key Libraries

- `win32com.client` - Outlook COM interface
- `sqlite3` - Database operations
- `tkinter` - GUI framework
- `requests` - HTTP API calls
- `json` - Data serialization

## Configuration Management

- Configuration is managed through `src/azure_config.py`
- User-specific data is stored in `user_specific_data/`
- Sensitive credentials should use environment variables
- Follow existing patterns for configuration loading

## Database Schema

- Email data is stored with unique identifiers and metadata
- Task persistence uses structured JSON storage
- Maintain backward compatibility when modifying schemas
- Use migrations for database structure changes

## AI Integration Patterns

### Prompt Engineering

- Prompts are stored in the `prompts/` directory as `.prompty` files
- Follow existing prompt structure and formatting
- Include clear instructions and examples in prompts
- Test prompts thoroughly before deployment

### Response Processing

- Parse AI responses defensively with error handling
- Validate JSON structures before processing
- Implement fallback behaviors for malformed responses
- Cache responses when appropriate to reduce API calls

## GUI Development

### Tkinter Patterns

- Use the existing widget patterns from `unified_gui.py`
- Implement responsive layouts that work across screen sizes
- Follow consistent styling and color schemes
- Provide user feedback for long-running operations

### User Experience

- Minimize clicks required for common operations
- Provide clear status indicators and progress feedback
- Implement keyboard shortcuts for power users
- Ensure accessibility considerations

## File Organization

### Directory Structure

- `src/` - Core application code
- `test/` - Unit and integration tests
- `prompts/` - AI prompt templates
- `docs/` - Documentation and guides
- `runtime_data/` - Generated data and temporary files
- `user_specific_data/` - User configuration and personalization

### Naming Conventions

- Use snake_case for Python files and functions
- Use descriptive names that indicate purpose
- Group related functionality in appropriately named modules
- Keep file names concise but clear

## Common Patterns

### Email Processing

```python
# Follow this pattern for email analysis
def process_email(email_data):
    try:
        # Validate input
        # Call AI service
        # Process response
        # Store results
        # Return structured data
    except Exception as e:
        logger.error(f"Error processing email: {e}")
        return default_response
```

### Database Operations

```python
# Use connection context managers
def store_data(data):
    with get_database_connection() as conn:
        cursor = conn.cursor()
        # Perform operations
        conn.commit()
```

### AI Service Calls

```python
# Follow existing patterns for AI integration
def call_ai_service(prompt, data):
    try:
        response = ai_client.process(prompt, data)
        return parse_ai_response(response)
    except Exception as e:
        logger.warning(f"AI service unavailable: {e}")
        return fallback_response()
```

## Performance Considerations

- Cache frequently accessed data
- Implement pagination for large email lists
- Use background processing for time-consuming operations
- Optimize database queries and use appropriate indexes
- Monitor memory usage when processing large datasets

## Security Guidelines

- Never log sensitive email content or credentials
- Validate all user inputs
- Use secure methods for credential storage
- Implement appropriate access controls
- Follow principle of least privilege

## Development Workflow

1. Create feature branches for new functionality
2. Write tests before implementing features (TDD when appropriate)
3. Update documentation for public APIs
4. Test integration with existing components
5. Submit pull requests with clear descriptions

## Debugging Tips

- Use the existing logging infrastructure
- Check `runtime_data/` for generated files and debugging info
- Test with various email types and content
- Verify AI service responses and error handling
- Use the test framework for isolated component testing

Remember: This project handles sensitive user data (emails). Always prioritize security, privacy, and reliability in your implementations.
