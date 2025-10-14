# COM AI Service Adapter - Documentation

## Overview

The COM AI Service Adapter (`backend/services/com_ai_service.py`) provides a FastAPI-compatible wrapper around the existing `AIProcessor` class for COM-based email processing integration.

## Purpose

This adapter was created as part of Task T1.2 to:
- Wrap existing AIProcessor functionality for FastAPI integration
- Reuse Azure OpenAI configuration from `src/azure_config.py`
- Leverage existing prompty files in `prompts/` directory
- Provide async methods compatible with FastAPI patterns
- Maintain compatibility with existing email classification, summarization, and analysis features

## Architecture

```
COMAIService
├── Wraps: AIProcessor (src/ai_processor.py)
├── Config: Azure OpenAI (src/azure_config.py)
└── Templates: Prompty files (prompts/*.prompty)
```

## Key Features

### 1. Email Classification
```python
result = await service.classify_email(
    email_content="Subject: Meeting\n\nJoin us tomorrow",
    context="Work context"
)
# Returns: {
#   'category': 'optional_event',
#   'confidence': 0.85,
#   'reasoning': 'Email contains meeting invitation...',
#   'alternatives': [...],
#   'requires_review': False
# }
```

Uses: `email_classifier_with_explanation.prompty`

### 2. Action Item Extraction
```python
result = await service.extract_action_items(
    email_content="Subject: Report\n\nPlease review by Friday",
    context="Work assignment"
)
# Returns: {
#   'action_items': [...],
#   'action_required': 'Review report',
#   'due_date': '2024-01-15',
#   'explanation': 'Manager request',
#   'relevance': 'Direct assignment',
#   'links': [...],
#   'confidence': 0.8
# }
```

Uses: `summerize_action_item.prompty`

### 3. Summary Generation
```python
result = await service.generate_summary(
    email_content="Subject: Project Update\n\nLong email content...",
    summary_type="brief"
)
# Returns: {
#   'summary': 'Project update with key milestones',
#   'key_points': ['Milestone 1', 'Milestone 2', ...],
#   'confidence': 0.8
# }
```

Uses: `email_one_line_summary.prompty`

### 4. Duplicate Detection
```python
emails = [
    {'id': '1', 'subject': 'Test', 'content': 'Hello'},
    {'id': '2', 'subject': 'Test', 'content': 'Hello'}
]
duplicates = await service.detect_duplicates(emails)
# Returns: ['2']  # List of duplicate email IDs
```

Uses: `email_duplicate_detection.prompty`

### 5. Template Discovery
```python
templates = await service.get_available_templates()
# Returns: {
#   'templates': ['email_classifier.prompty', ...],
#   'descriptions': {'email_classifier.prompty': 'Description...'}
# }
```

## FastAPI Integration

### Dependency Injection
```python
from fastapi import Depends, FastAPI
from backend.services.com_ai_service import COMAIService, get_com_ai_service

app = FastAPI()

@app.post("/classify")
async def classify_email(
    email_content: str,
    service: COMAIService = Depends(get_com_ai_service)
):
    result = await service.classify_email(email_content)
    return result
```

### Example Endpoint
```python
@app.post("/api/ai/classify")
async def classify_endpoint(
    subject: str,
    content: str,
    sender: str,
    service: COMAIService = Depends(get_com_ai_service)
):
    email_text = f"Subject: {subject}\nFrom: {sender}\n\n{content}"
    return await service.classify_email(email_text)
```

## Configuration

The service automatically uses existing configuration:

### Azure OpenAI Settings
From `src/azure_config.py`:
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_KEY` - API key (or use Azure credentials)
- `AZURE_OPENAI_DEPLOYMENT` - Deployment name (default: gpt-4o)
- `AZURE_OPENAI_API_VERSION` - API version (default: 2024-02-01)

### Prompty Files
Located in `prompts/` directory:
- `email_classifier_with_explanation.prompty` - Email classification
- `summerize_action_item.prompty` - Action item extraction
- `email_one_line_summary.prompty` - Email summarization
- `email_duplicate_detection.prompty` - Duplicate detection
- Additional prompty files for specialized operations

## Error Handling

All methods include comprehensive error handling:

```python
result = await service.classify_email(email_content)
if 'error' in result:
    print(f"Classification failed: {result['error']}")
    # Fallback behavior is included in result
```

### Graceful Degradation
- AI service failures return safe fallback results
- Low confidence scores trigger manual review flags
- Invalid responses are parsed with fallback strategies

## Testing

Comprehensive test suite in `backend/tests/test_com_ai_service.py`:

```bash
# Run all COM AI service tests
pytest backend/tests/test_com_ai_service.py -v

# Run specific test
pytest backend/tests/test_com_ai_service.py::TestCOMAIService::test_classify_email_success -v
```

Test coverage includes:
- Service initialization and lazy loading
- All async method operations
- Error handling and edge cases
- JSON parsing and fallback strategies
- Mock Azure OpenAI responses
- Async/await compatibility

## Performance Considerations

### Async Thread Pool Execution
CPU-bound AI operations run in thread pool to avoid blocking the event loop:

```python
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(
    None,
    self._classify_email_sync,
    email_content,
    context
)
```

### Lazy Initialization
Service components are initialized on first use to minimize startup time.

### Confidence Thresholds
Reuses AIProcessor confidence thresholds for consistency:
- FYI: 90% confidence for auto-approval
- Required Personal Action: Always requires review
- Optional Action: 80% confidence for auto-approval
- Work Relevant: 80% confidence for auto-approval

## Comparison with Existing Services

### COMAIService vs AIService
- **COMAIService**: New COM-specific adapter (T1.2)
- **AIService**: Original async wrapper for general use
- Both wrap AIProcessor but with different integration patterns

### When to Use
- Use **COMAIService** for COM-based email processing
- Use **AIService** for general FastAPI endpoints
- Both share the same underlying AIProcessor and prompty files

## Migration Path

### From Direct AIProcessor Usage
```python
# Old
processor = AIProcessor()
result = processor.classify_email_with_explanation(email_content, [])

# New
service = COMAIService()
result = await service.classify_email(email_content)
```

### From AIService
```python
# AIService pattern
from backend.services.ai_service import get_ai_service
service = get_ai_service()

# COMAIService pattern
from backend.services.com_ai_service import get_com_ai_service
service = get_com_ai_service()
```

## Related Files

- `src/ai_processor.py` - Core AI processing logic
- `src/azure_config.py` - Azure OpenAI configuration
- `prompts/*.prompty` - AI prompt templates
- `backend/services/ai_service.py` - Original async wrapper
- `src/adapters/ai_processor_adapter.py` - Interface adapter
- `backend/tests/test_com_ai_service.py` - Test suite

## Future Enhancements

Planned improvements for Wave 1 tasks:
1. Integration with COM email provider (T1.1)
2. Rate limiting and caching
3. Enhanced batch processing
4. Metrics and telemetry
5. Advanced error recovery

## Support

For issues or questions:
1. Check test suite for usage examples
2. Review AIProcessor documentation
3. Verify Azure OpenAI configuration
4. Check prompty file syntax

## Version History

- **v1.0** (2025-10-14): Initial implementation for T1.2
  - Created COM AI service adapter
  - Comprehensive test suite (23 tests)
  - Full prompty file integration
  - Async FastAPI compatibility
