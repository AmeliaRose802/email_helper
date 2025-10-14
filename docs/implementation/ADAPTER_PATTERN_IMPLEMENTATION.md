# Adapter Pattern Implementation for Backend Integration

## Overview

This document describes the adapter pattern implementation for Task T0.1, which establishes the foundation for backend API integration by wrapping existing services (OutlookManager and AIProcessor) with clean interfaces.

## Objective

Extract core functionality from OutlookManager and AIProcessor into clean service interfaces without duplicating code. The adapter layer enables:

- Backend API integration with existing COM and AI logic
- Clean separation of concerns
- Easy testing through dependency injection
- Backward compatibility with existing code
- Foundation for FastAPI integration

## Architecture

### Interface Contracts

All adapters implement interfaces defined in `src/core/interfaces.py`:

- **EmailProvider**: Email access and manipulation
- **AIProvider**: AI processing and classification
- **StorageProvider**: Data persistence and retrieval (existing)

### Adapter Components

#### 1. OutlookEmailAdapter

**Location**: `src/adapters/outlook_email_adapter.py`

**Purpose**: Wraps OutlookManager to provide EmailProvider interface

**Key Methods**:
- `connect()`: Establish Outlook connection
- `get_emails()`: Retrieve emails with pagination
- `move_email()`: Move emails between folders
- `get_email_body()`: Get email content
- `get_folders()`: List available folders
- `mark_as_read()`: Mark emails as read
- `categorize_email()`: Apply categories to emails

**Features**:
- Converts COM objects to dictionaries
- Handles pagination for large email lists
- Robust error handling and recovery
- Maintains connection state
- Compatible with FastAPI dependency injection

**Example Usage**:
```python
from adapters import OutlookEmailAdapter

# Create and connect adapter
adapter = OutlookEmailAdapter()
adapter.connect()

# Get recent emails
emails = adapter.get_emails("Inbox", count=50, offset=0)

# Process emails
for email in emails:
    print(f"Subject: {email['subject']}")
    print(f"From: {email['sender']}")
```

#### 2. AIProcessorAdapter

**Location**: `src/adapters/ai_processor_adapter.py`

**Purpose**: Wraps AIProcessor to provide AIProvider interface

**Key Methods**:
- `classify_email()`: Classify email with confidence scoring
- `analyze_batch()`: Holistic analysis of multiple emails
- `extract_action_items()`: Extract actionable tasks
- `generate_summary()`: Generate email summaries

**Features**:
- Automatic confidence threshold evaluation
- Determines if manual review is required
- Batch processing for efficiency
- Integration with existing prompty templates
- Error handling with safe fallbacks

**Example Usage**:
```python
from adapters import AIProcessorAdapter

# Create adapter
adapter = AIProcessorAdapter()

# Classify email
result = adapter.classify_email(
    "Subject: Urgent Task\n\nPlease complete this by EOD"
)

print(f"Category: {result['category']}")
print(f"Confidence: {result['confidence']}")
print(f"Requires Review: {result['requires_review']}")
print(f"Reasoning: {result['reasoning']}")
```

### Design Principles

#### 1. No Code Duplication
- Adapters delegate to existing implementations
- No reimplementation of COM or AI logic
- Thin wrapper layer only

#### 2. Interface Compliance
- Strict adherence to interface contracts
- Predictable method signatures
- Consistent return value formats

#### 3. Error Resilience
- Graceful degradation on errors
- Safe fallback values
- Comprehensive error logging

#### 4. Testability
- Dependency injection support
- Easy mocking for unit tests
- Isolated component testing

#### 5. Backward Compatibility
- Existing code continues to work
- No breaking changes to current services
- Incremental adoption path

## Integration with FastAPI

The adapters are designed for seamless FastAPI integration:

### Dependency Injection Pattern

```python
from fastapi import Depends
from adapters import OutlookEmailAdapter, AIProcessorAdapter

# Create singleton instances
_email_adapter = None
_ai_adapter = None

def get_email_adapter() -> OutlookEmailAdapter:
    """FastAPI dependency for email adapter."""
    global _email_adapter
    if _email_adapter is None:
        _email_adapter = OutlookEmailAdapter()
        _email_adapter.connect()
    return _email_adapter

def get_ai_adapter() -> AIProcessorAdapter:
    """FastAPI dependency for AI adapter."""
    global _ai_adapter
    if _ai_adapter is None:
        _ai_adapter = AIProcessorAdapter()
    return _ai_adapter

# Use in endpoints
@app.get("/emails")
async def get_emails(
    email_adapter: OutlookEmailAdapter = Depends(get_email_adapter)
):
    emails = email_adapter.get_emails("Inbox", count=50)
    return {"emails": emails}

@app.post("/classify")
async def classify_email(
    email_content: str,
    ai_adapter: AIProcessorAdapter = Depends(get_ai_adapter)
):
    result = ai_adapter.classify_email(email_content)
    return result
```

## Testing

### Unit Tests

**Location**: 
- `test/test_outlook_email_adapter.py`
- `test/test_ai_processor_adapter.py`

**Coverage**:
- Interface compliance verification
- Success path testing
- Error handling validation
- Pagination logic
- Confidence threshold evaluation
- Edge case handling

**Test Results**:
- OutlookEmailAdapter: 13 tests, all passing
- AIProcessorAdapter: 15 tests, all passing

### Running Tests

```bash
# Run all adapter tests
python -m pytest test/test_outlook_email_adapter.py test/test_ai_processor_adapter.py -v

# Run with coverage
python -m pytest test/test_outlook_email_adapter.py test/test_ai_processor_adapter.py --cov=src/adapters
```

### Mock Strategy

Tests use mocking to isolate adapter logic:
- Mock OutlookManager COM operations
- Mock AIProcessor Azure OpenAI calls
- Verify correct delegation
- Validate data transformations

## Configuration

No additional configuration required. Adapters use existing configuration:

- **Azure OpenAI**: Via `azure_config.py`
- **Outlook COM**: Via system Outlook installation
- **User Data**: Via `user_specific_data/` directory

## Performance Considerations

### OutlookEmailAdapter
- Lazy connection initialization
- Efficient pagination support
- Minimal data transformation overhead
- Connection reuse across requests

### AIProcessorAdapter
- Batch processing support
- Reuses existing prompt templates
- No additional API calls
- Efficient confidence evaluation

## Future Enhancements

### Planned for T1.1-T1.3
1. Integration with backend API endpoints
2. FastAPI dependency injection setup
3. Enhanced error reporting
4. Connection pooling for COM
5. Caching layer for frequently accessed data

### Potential Improvements
1. Async/await support for I/O operations
2. Metrics and telemetry collection
3. Rate limiting for API protection
4. Connection health monitoring
5. Automatic retry logic

## Migration Path

### For Existing Code
1. No changes required to current functionality
2. Continue using OutlookManager and AIProcessor directly
3. Gradually migrate to adapters as needed

### For New Backend Code
1. Use adapters exclusively
2. Leverage dependency injection
3. Follow interface contracts
4. Add new methods to adapters as needed

## Troubleshooting

### Common Issues

**Issue**: "Not connected to Outlook" error
**Solution**: Call `adapter.connect()` before using email operations

**Issue**: AI classification returns low confidence
**Solution**: Check Azure OpenAI configuration and API quota

**Issue**: Pagination returns wrong emails
**Solution**: Verify offset and count parameters are correct

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

adapter = OutlookEmailAdapter()
adapter.connect()
```

## Dependencies

### Required Packages
- `win32com.client`: COM interface for Outlook
- `typing`: Type hints
- Existing project dependencies (see `requirements.txt`)

### Python Version
- Python 3.8 or higher
- Tested on Python 3.12.10

## Success Metrics

### Task T0.1 Completion Criteria

✅ Clean adapter interfaces created  
✅ No code duplication  
✅ All unit tests passing (28 tests total)  
✅ Documentation complete  
✅ Backward compatibility maintained  
✅ Ready for FastAPI integration  

### Performance Targets
- Email retrieval: < 1 second for 50 emails
- AI classification: < 3 seconds per email
- Batch analysis: < 10 seconds for 20 emails
- Zero breaking changes to existing code

## Related Tasks

- **T1.1**: Create COM Email Provider Adapter (builds on this)
- **T1.2**: Create AI Service Adapter (builds on this)
- **T1.3**: Update API Dependencies (uses these adapters)
- **T1.5**: Create Test Infrastructure (extends these tests)

## References

- Interface contracts: `src/core/interfaces.py`
- Original services: `src/outlook_manager.py`, `src/ai_processor.py`
- Backend structure: `backend/` directory
- Test suite: `test/` directory

## Authors

- Implementation: GitHub Copilot
- Review: Development Team
- Date: October 14, 2025

## Changelog

- **2025-10-14**: Initial adapter implementation
- **2025-10-14**: Unit tests created and verified passing
- **2025-10-14**: Documentation completed
