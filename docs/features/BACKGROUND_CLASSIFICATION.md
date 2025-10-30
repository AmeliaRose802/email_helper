# Background Email Classification

## Overview

The Email Helper application now includes **automatic background email classification** that continues to work even when the application window is minimized or not in focus. This ensures your emails are always being processed and categorized by AI without requiring constant user interaction.

## How It Works

### Architecture Components

1. **Electron Background Throttling Disabled**
   - Setting: `backgroundThrottling: false` in Electron `BrowserWindow`
   - Effect: Allows the renderer process to continue executing when minimized
   - Location: `electron/main.js`

2. **Auto Email Processor Service**
   - File: `backend/services/auto_processor.py`
   - Purpose: Continuously polls for unclassified emails and queues them for AI processing
   - Runs independently of UI interactions

3. **Background Email Worker**
   - File: `backend/workers/email_processor.py`
   - Purpose: Processes queued emails with AI classification
   - Handles email analysis, categorization, and task extraction

### Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Backend Startup (FastAPI lifespan)                        │
│  ↓                                                          │
│  Auto Processor Starts                                     │
│  ↓                                                          │
│  Polling Loop (every 60 seconds by default)                │
│  ↓                                                          │
│  Check for unclassified emails                             │
│  ↓                                                          │
│  Queue emails for processing (max 10 per batch)            │
│  ↓                                                          │
│  Email Worker processes batch with AI                      │
│  ↓                                                          │
│  Update email records with AI classification               │
│  ↓                                                          │
│  WebSocket broadcasts status to connected clients          │
│  ↓                                                          │
│  Repeat polling loop                                       │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Default Settings

- **Poll Interval**: 60 seconds
- **Max Batch Size**: 10 emails per batch
- **Auto-start**: Enabled by default when backend starts

### Adjusting Settings

To modify the auto processor settings, edit `backend/services/auto_processor.py`:

```python
# At the bottom of the file
auto_email_processor = AutoEmailProcessor(
    poll_interval=60,      # Change polling interval (seconds)
    max_batch_size=10      # Change batch size (emails)
)
```

**Considerations:**
- Lower poll interval = faster classification but more CPU usage
- Higher batch size = more emails processed at once but longer wait times
- Balance based on your email volume and system resources

### Disabling Auto Processing

If you prefer manual control, you can disable auto processing:

**Option 1: API Call**
```bash
POST /api/processing/auto-processor/stop
```

**Option 2: Environment Variable**
Add to backend configuration:
```python
AUTO_PROCESSING_ENABLED = False
```

## API Endpoints

### Get Auto Processor Status

```http
GET /api/processing/auto-processor/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "enabled": true,
  "poll_interval_seconds": 60,
  "max_batch_size": 10,
  "emails_processed": 145,
  "worker_active": true,
  "message": "Auto processor monitors for unclassified emails in background"
}
```

### Start Auto Processor

```http
POST /api/processing/auto-processor/start
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "started",
  "message": "Automatic email processor started successfully"
}
```

### Stop Auto Processor

```http
POST /api/processing/auto-processor/stop
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "stopped",
  "message": "Automatic email processor stopped successfully"
}
```

## Benefits

### User Experience
- ✅ **Zero-touch processing**: Emails are classified without manual intervention
- ✅ **Works while minimized**: Application continues working even when not focused
- ✅ **Always up-to-date**: New emails are automatically processed as they arrive
- ✅ **Reduced waiting**: Email list loads faster with pre-classified emails

### Technical Benefits
- ✅ **Efficient batching**: Processes emails in optimal batch sizes
- ✅ **Rate limiting**: Built-in delays prevent API throttling
- ✅ **Fault tolerance**: Automatic retry on errors
- ✅ **Memory management**: Tracks processed emails efficiently (last 1000)

## Monitoring

### Backend Logs

The auto processor logs its activity to the backend console:

```
🤖 Automatic email processor started - AI classification runs in background
   📊 Polling interval: 60s
   📦 Batch size: 10 emails
```

During operation:
```
📧 Found 15 new unclassified emails, queuing 10 for AI processing
✅ Created processing pipeline abc123 for 10 emails
```

### Checking Status

Use the status endpoint to monitor the auto processor:

```bash
curl -X GET "http://localhost:8000/api/processing/auto-processor/status" \
  -H "Authorization: Bearer <your-token>"
```

### WebSocket Updates

Connect to WebSocket for real-time processing updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/processing/ws?user_id=<user-id>');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Processing update:', update);
};
```

## Troubleshooting

### Auto Processor Not Starting

**Symptoms:** No background classification happening

**Possible Causes:**
1. Email service not initialized
2. Backend startup error
3. Auto processor disabled

**Solutions:**
1. Check backend logs for startup errors
2. Verify email service configuration
3. Try manual start: `POST /api/processing/auto-processor/start`

### Slow Classification

**Symptoms:** Emails taking too long to classify

**Possible Causes:**
1. High email volume
2. Low poll interval
3. AI service throttling

**Solutions:**
1. Increase `max_batch_size` (process more at once)
2. Increase `poll_interval` (reduce frequency)
3. Check Azure OpenAI rate limits and quotas

### Memory Usage

**Symptoms:** High memory consumption

**Possible Causes:**
1. Too many tracked processed emails
2. Large batch sizes
3. Memory leaks in processing loop

**Solutions:**
1. Auto processor automatically limits to 1000 tracked emails
2. Reduce `max_batch_size`
3. Restart backend service periodically

## Performance Tips

### Optimizing for Different Scenarios

**High Email Volume (100+ per day):**
```python
auto_email_processor = AutoEmailProcessor(
    poll_interval=30,      # Poll more frequently
    max_batch_size=20      # Process larger batches
)
```

**Low Email Volume (< 20 per day):**
```python
auto_email_processor = AutoEmailProcessor(
    poll_interval=300,     # Poll less frequently (5 min)
    max_batch_size=5       # Smaller batches sufficient
)
```

**Battery Saving (Laptops):**
```python
auto_email_processor = AutoEmailProcessor(
    poll_interval=600,     # Poll every 10 minutes
    max_batch_size=5       # Minimal batches
)
```

## Related Documentation

- [Email Processing Architecture](../technical/EMAIL_PROCESSING_ARCHITECTURE.md)
- [AI Classification Implementation](REACT_CLASSIFICATION_IMPLEMENTATION.md)
- [Backend Worker System](../technical/WORKER_SYSTEM.md)
- [Performance Optimization](../technical/PERFORMANCE.md)

## Future Enhancements

Potential improvements planned:
- [ ] Configurable polling schedule (e.g., only during work hours)
- [ ] Priority-based processing (urgent emails first)
- [ ] Smart polling (adjust frequency based on email patterns)
- [ ] User preferences for auto processing behavior
- [ ] Email notification when classification completes
