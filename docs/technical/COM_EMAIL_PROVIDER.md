# COM Email Provider Documentation

## Overview

The COM Email Provider (`backend/services/com_email_provider.py`) is a FastAPI-compatible adapter that wraps the existing OutlookManager functionality to enable COM-based email operations through the backend API.

## Architecture

```
┌─────────────────────────────────────────┐
│     FastAPI Backend API                 │
│  (backend/api/emails.py)                │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│   EmailProvider Interface               │
│  (backend/services/email_provider.py)   │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│   COMEmailProvider                      │
│  (backend/services/com_email_provider.py)│
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│   OutlookEmailAdapter                   │
│  (src/adapters/outlook_email_adapter.py)│
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│   OutlookManager                        │
│  (src/outlook_manager.py)               │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│   Microsoft Outlook COM Interface       │
└─────────────────────────────────────────┘
```

## Features

### Implemented Methods

The COM Email Provider implements all required EmailProvider interface methods:

1. **`authenticate(credentials: Dict[str, str]) -> bool`**
   - Establishes connection to local Outlook application
   - Credentials parameter ignored (Windows integrated auth)
   - Returns True on success, raises HTTPException on failure

2. **`get_emails(folder_name: str, count: int, offset: int) -> List[Dict[str, Any]]`**
   - Retrieves emails from specified folder with pagination
   - Returns list of email dictionaries with standardized fields
   - Default: 50 emails from Inbox

3. **`get_email_content(email_id: str) -> Dict[str, Any]`**
   - Retrieves full email content by EntryID
   - Returns email dictionary with complete body text
   - Returns None if email not found

4. **`get_folders() -> List[Dict[str, str]]`**
   - Lists all available email folders
   - Returns list of folder dictionaries with id, name, type

5. **`mark_as_read(email_id: str) -> bool`**
   - Marks specified email as read
   - Returns True on success, False on failure

6. **`move_email(email_id: str, destination_folder: str) -> bool`**
   - Moves email to specified folder
   - Creates folder if it doesn't exist
   - Returns True on success, False on failure

7. **`get_conversation_thread(conversation_id: str) -> List[Dict[str, Any]]`**
   - Retrieves all emails in a conversation thread
   - Returns list of related emails

8. **`get_email_body(email_id: str) -> str`**
   - Compatibility method for legacy code
   - Returns email body text only

## Configuration

### Enable COM Provider

In `backend/core/config.py`, add or set:

```python
class Settings(BaseSettings):
    use_com_backend: bool = True  # Enable COM provider
    
    # Other settings...
```

### Environment Variables

Create a `.env` file:

```bash
USE_COM_BACKEND=true
```

### Provider Selection Logic

The provider factory (`get_email_provider_instance()`) selects providers in this order:

1. **COM Provider** - If `use_com_backend=True` and pywin32 is available
2. **Graph API Provider** - If Graph API credentials are configured
3. **Mock Provider** - For development/testing

## Usage Examples

### Basic Usage

```python
from backend.services.com_email_provider import COMEmailProvider

# Create provider instance
provider = COMEmailProvider()

# Authenticate (connect to Outlook)
provider.authenticate({})

# Get emails
emails = provider.get_emails("Inbox", count=10, offset=0)

# Process emails
for email in emails:
    print(f"Subject: {email['subject']}")
    print(f"From: {email['sender']}")
    print(f"Read: {email['is_read']}")
```

### With FastAPI

```python
from fastapi import APIRouter, Depends
from backend.services.email_provider import get_email_provider

router = APIRouter()

@router.get("/emails")
async def get_emails(
    provider: EmailProvider = Depends(get_email_provider)
):
    # Provider automatically selected based on configuration
    emails = provider.get_emails("Inbox", count=20)
    return {"emails": emails}
```

### Error Handling

```python
from fastapi import HTTPException

try:
    provider = COMEmailProvider()
    provider.authenticate({})
    emails = provider.get_emails()
except HTTPException as e:
    if e.status_code == 401:
        print("Not authenticated")
    elif e.status_code == 503:
        print("Outlook not available")
    elif e.status_code == 500:
        print("Internal error")
```

## Requirements

### System Requirements

- **Operating System**: Windows only
- **Python Package**: `pywin32` (pip install pywin32)
- **Application**: Microsoft Outlook (installed and configured)
- **Status**: Outlook must be running

### Python Dependencies

```txt
pywin32>=306
fastapi>=0.100.0
```

## Error Handling

### HTTP Status Codes

- **401 Unauthorized**: Not authenticated or connection lost
- **500 Internal Server Error**: Unexpected errors during operation
- **503 Service Unavailable**: Cannot connect to Outlook

### Common Errors

1. **ImportError**: pywin32 not installed
   ```
   Solution: pip install pywin32
   ```

2. **HTTPException 503**: Outlook not running
   ```
   Solution: Start Microsoft Outlook application
   ```

3. **RuntimeError**: Connection lost during operation
   ```
   Solution: Check Outlook is still running, reconnect
   ```

## Testing

### Run Unit Tests

```bash
python -m pytest backend/tests/test_com_email_provider.py -v
```

### Test Coverage

- Interface compliance tests
- Authentication and connection tests
- Email operation tests
- Error handling tests
- Integration tests

All 21 tests passing ✅

### Mock Testing

The test suite uses mock objects to simulate Outlook COM operations, allowing tests to run on any platform without requiring Outlook.

## Thread Safety

COM operations are single-threaded by nature. The provider:

- Maintains COM objects on the main thread
- Uses proper error handling for concurrent access
- Logs all operations for debugging

## Performance Considerations

- **Connection**: Reuses existing Outlook connection
- **Caching**: Outlook handles internal caching
- **Pagination**: Supports offset/count for efficient retrieval
- **Batch Operations**: Uses OutlookManager's batch methods

## Logging

The provider logs all operations:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('backend.services.com_email_provider')
```

Log levels:
- **INFO**: Successful operations, connection status
- **DEBUG**: Method calls, parameters
- **WARNING**: Failed operations, retries
- **ERROR**: Connection errors, exceptions

## Compatibility

### Tkinter Application

The COM provider maintains full compatibility with the existing Tkinter application:

- Uses same OutlookManager instance
- No changes to existing functionality
- Parallel operation supported

### Backend API

Fully compatible with FastAPI backend:

- Implements EmailProvider interface
- Supports dependency injection
- Async-compatible (sync methods wrapped)

## Limitations

1. **Windows Only**: Requires Windows OS and Outlook
2. **Local Only**: Cannot access cloud mailboxes directly
3. **Single User**: Uses current Windows user's Outlook profile
4. **Outlook Required**: Outlook must be installed and running

## Future Enhancements

Potential improvements:

1. **Async Support**: Native async/await for better concurrency
2. **Connection Pool**: Multiple Outlook instances
3. **Caching**: Redis cache for frequently accessed emails
4. **Enhanced Threading**: Better thread safety for concurrent requests
5. **Retry Logic**: Automatic reconnection on failures

## Support

For issues or questions:

1. Check logs for detailed error messages
2. Verify Outlook is running and accessible
3. Ensure pywin32 is properly installed
4. Review test suite for usage examples

## References

- [EmailProvider Interface](email_provider.py)
- [OutlookEmailAdapter](../../src/adapters/outlook_email_adapter.py)
- [OutlookManager](../../src/outlook_manager.py)
- [Test Suite](../tests/test_com_email_provider.py)
