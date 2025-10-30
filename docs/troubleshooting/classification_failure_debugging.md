# Email Classification Failure Debugging Guide

## Problem Description

Only the first email in a batch gets classified successfully. All subsequent emails show classification failures with no clear error messages.

## Root Cause Investigation

### Added Comprehensive Logging

I've added detailed logging throughout the classification pipeline to track where failures occur:

1. **Backend API Layer** (`backend/api/ai.py`)
   - Logs when classification requests arrive
   - Logs the email content length and subject
   - Logs classification results and errors
   - Logs summary generation steps

2. **COM AI Service Layer** (`backend/services/com_ai_service.py`)
   - Logs when `classify_email()` is called
   - Logs content length being processed
   - Logs sync classification start and completion
   - Logs detailed error information with exception types and stack traces

3. **AI Processor Layer** (`src/ai_processor.py`)
   - Logs when `classify_email_with_explanation()` is called
   - Logs the email subject being processed
   - Logs prompty execution start and completion
   - Logs prompty response type and content
   - Logs JSON parsing steps
   - Logs detailed errors with exception types

## Logging Format

All logs now follow a consistent format:
- `[Component] message` - Standard log
- `[Component] [OK] message` - Success
- `[Component] [WARN] message` - Warning
- `[Component] [ERROR] message` - Error with details
- `[Component] [FILTER] message` - Content filter blocked
- `[Component] [JSON] message` - JSON format enforcement

## Potential Root Causes

Based on the code analysis, here are the likely causes:

### 1. **Azure OpenAI Rate Limiting**
- **Symptom**: First request succeeds, subsequent requests fail
- **Location**: `src/ai_processor.py` in `execute_prompty()`
- **What to look for in logs**:
  ```
  [AI Processor] [ERROR] Prompty execution failed: RateLimitError
  ```
- **Solution**: Add retry logic with exponential backoff

### 2. **Content Filter Violations**
- **Symptom**: Requests blocked by Azure content policy
- **Location**: `src/ai_processor.py` in `execute_prompty()`
- **What to look for in logs**:
  ```
  [AI Processor] [FILTER] Content filter blocked email_classifier_with_explanation.prompty
  ```
- **Solution**: Emails return fallback classification ("fyi" category)

### 3. **JSON Parsing Failures**
- **Symptom**: AI returns plain text instead of JSON
- **Location**: `src/ai_processor.py` in `classify_email_with_explanation()`
- **What to look for in logs**:
  ```
  [AI Processor] [WARN] Invalid classification format
  [AI Processor] [ERROR] Error parsing classification response
  ```
- **Solution**: Already implemented JSON format enforcement and fallback parsing

### 4. **Thread Pool Executor Issues**
- **Symptom**: Deadlock or thread exhaustion after first classification
- **Location**: `backend/services/com_ai_service.py` in `classify_email()`
- **What to look for in logs**:
  - Classification starts but never completes
  - No error messages at all (hangs)
- **Solution**: Check thread pool configuration in FastAPI

### 5. **AIProcessor State Corruption**
- **Symptom**: AIProcessor instance becomes unusable after first use
- **Location**: `src/ai_processor.py` initialization or prompty execution
- **What to look for in logs**:
  - First classification succeeds
  - Subsequent classifications fail with AttributeError or None references
- **Solution**: Ensure AIProcessor is stateless or properly reinitialized

## How to Debug

### Step 1: Check Backend Logs

Start the Electron app and watch for classification logs in the Python backend console. Look for:

1. **Request arrival**:
   ```
   [AI API] classify_email called - subject: <email subject>...
   ```

2. **Service call**:
   ```
   [COM AI Service] classify_email called - content length: <number>
   ```

3. **Sync processing**:
   ```
   [Classification] Starting classification for: <subject>...
   ```

4. **AI Processor**:
   ```
   [AI Processor] classify_email_with_explanation called for: <subject>...
   ```

5. **Prompty execution**:
   ```
   [AI Processor] Executing email_classifier_with_explanation.prompty with inputs: [...]
   ```

6. **Result**:
   ```
   [AI Processor] [OK] Classification complete: <category>
   ```

### Step 2: Run Test Script

Use the test script to isolate the issue:

```powershell
cd C:\Users\ameliapayne\email_helper
& .venv\Scripts\Activate.ps1
python scripts\test_classification.py
```

This will test:
1. AIProcessor directly (bypasses FastAPI)
2. COMAIService directly (bypasses HTTP)
3. Multiple sequential classifications (detects rate limiting/state issues)

### Step 3: Check for Rate Limit Errors

If you see rate limit errors, add delays between classifications:

```python
# In backend/api/ai.py or backend/services/com_ai_service.py
import asyncio
await asyncio.sleep(1)  # 1 second delay between classifications
```

### Step 4: Check Azure OpenAI Logs

1. Go to Azure Portal
2. Navigate to your Azure OpenAI resource
3. Check "Metrics" for:
   - Request rate
   - Throttled requests
   - Error rate

### Step 5: Enable Debug Logging

Set logging level to DEBUG in `backend/main.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Expected Log Flow for Successful Classification

```
[AI API] classify_email called - subject: Test Email...
[AI API] Email text prepared - length: 123
[AI API] Calling ai_service.classify_email...
[COM AI Service] classify_email called - content length: 123
[Classification] Starting classification for: Test Email...
[Classification] Email dict prepared - subject length: 10, body length: 100
[AI Processor] classify_email_with_explanation called for: Test Email...
[AI Processor] Executing email_classifier_with_explanation.prompty with inputs: ['context', 'username', 'subject', 'sender', 'date', 'body']
[AI Processor] Using prompty library for email_classifier_with_explanation.prompty
[AI Processor] [JSON] Enforcing JSON format for email_classifier_with_explanation.prompty
[AI Processor] Calling prompty.run with 6 inputs
[AI Processor] [OK] email_classifier_with_explanation.prompty returned JSON string
[AI Processor] Prompty returned: <class 'str'> - {"category": "work_relevant", "explanation": "..."}
[AI Processor] Cleaned result: {"category": "work_relevant", "explanation": "..."}
[AI Processor] [OK] Classification complete: work_relevant - Email contains work-related...
[Classification] [OK] Email classified as work_relevant (confidence: None)
[COM AI Service] Classification completed successfully
[AI API] Generating one-line summary...
[AI API] [OK] Classification complete: work_relevant (confidence: None)
```

## Expected Log Flow for Failed Classification

Look for where the log stops to identify the failure point:

```
[AI API] classify_email called - subject: Test Email...
[AI API] Email text prepared - length: 123
[AI API] Calling ai_service.classify_email...
[COM AI Service] classify_email called - content length: 123
[Classification] Starting classification for: Test Email...
[Classification] Email dict prepared - subject length: 10, body length: 100
[AI Processor] classify_email_with_explanation called for: Test Email...
[AI Processor] Executing email_classifier_with_explanation.prompty with inputs: [...]
[AI Processor] Using prompty library for email_classifier_with_explanation.prompty
[AI Processor] [ERROR] Prompty execution failed for email_classifier_with_explanation.prompty: RateLimitError: Rate limit exceeded
```

## Quick Fixes

### If Rate Limited
Add to `backend/services/com_ai_service.py`:

```python
async def classify_email(self, email_content: str, context: Optional[str] = None):
    # ... existing code ...
    try:
        result = await loop.run_in_executor(...)
        await asyncio.sleep(0.5)  # Add 500ms delay
        return result
```

### If Content Filtered
The system already handles this with fallback classifications. Check logs for `[FILTER]` messages.

### If JSON Parsing Failed
The system already has fallback parsing. Check logs for `[WARN] Invalid classification format`.

## Files Modified

1. `backend/services/com_ai_service.py` - Added logging to `classify_email()` and `_classify_email_sync()`
2. `src/ai_processor.py` - Added logging to `classify_email_with_explanation()` and `execute_prompty()`
3. `backend/api/ai.py` - Added logging to `classify_email()` endpoint
4. `scripts/test_classification.py` - New test script for debugging

## Next Steps

1. **Run the app** and classify multiple emails while watching the backend console
2. **Look for the pattern**: Does logging stop at a specific point?
3. **Check for errors**: Are there any exception stack traces?
4. **Run the test script**: Does it reproduce the issue?
5. **Report findings**: Copy the relevant log section that shows the failure

## Common Issues and Solutions

| Issue | Log Pattern | Solution |
|-------|-------------|----------|
| Rate limiting | `RateLimitError` or `429` | Add delays between requests |
| Content filter | `[FILTER]` or `ResponsibleAIPolicyViolation` | Already handled with fallbacks |
| JSON parse error | `[WARN] Invalid classification format` | Already handled with fallbacks |
| Thread deadlock | Logs stop with no error | Increase thread pool size |
| AI service down | `Connection refused` or timeout | Check Azure OpenAI service status |
| Invalid credentials | `401 Unauthorized` or `Authentication failed` | Verify Azure OpenAI API key |
