# AI Service Error Diagnosis Guide

## Overview
The backend now logs **detailed error information** showing exactly why task extraction fails for specific emails. This helps distinguish between:
- ⚠️ Content filtering (expected for certain content)
- ⏱️ Rate limiting (need to slow down)
- 🔌 Network issues (transient, can retry)
- ❌ Unexpected errors (bugs to fix)

## Error Types You'll See

### 1. ⚠️ CONTENT FILTER
**What it means:** Azure OpenAI's content safety system blocked the email

**Log example:**
```
[Task Extraction] ⚠️ CONTENT FILTER: Email 00000000C14B3E2B7C4E364A8A8C blocked by Azure content policy. Email contains flagged content.
```

**Common causes:**
- URLs to certain external sites (job boards, social media)
- Promotional content with marketing language
- External newsletter links
- Sensitive topics (politics, controversial subjects)

**What to do:** 
- ✅ This is EXPECTED behavior - not a bug
- ✅ Content-filtered emails get fallback text: "Review email manually"
- ❌ Don't try to bypass - it's an Azure policy

---

### 2. ⏱️ RATE LIMIT
**What it means:** Too many API calls to Azure OpenAI in short time

**Log example:**
```
[Task Extraction] ⏱️ RATE LIMIT: Throttled while processing email 00000000C14B3E2B7C4E364A8A8C. Azure OpenAI rate limit exceeded. Error: 429 Too Many Requests
```

**Common causes:**
- Processing too many emails at once
- Delays between calls are too short
- Multiple users/processes hitting same Azure resource

**What to do:**
- ✅ Increase delays in code (currently 2 seconds between emails)
- ✅ Implement exponential backoff
- ✅ Reduce batch size from 10 to 5 emails at a time

---

### 3. 🔌 CONNECTION ERROR
**What it means:** Network or connectivity issue with Azure

**Log example:**
```
[Task Extraction] 🔌 CONNECTION: Network issue processing email 00000000C14B3E2B7C4E364A8A8C. Error: Connection timeout
```

**Common causes:**
- Internet connectivity hiccup
- Azure service temporary outage
- Firewall/proxy issues
- DNS resolution failure

**What to do:**
- ✅ Retry the email (usually succeeds second time)
- ✅ Check internet connection
- ✅ Check Azure service status

---

### 4. ⚠️ BAD REQUEST
**What it means:** Invalid data sent to Azure OpenAI

**Log example:**
```
[Task Extraction] ⚠️ BAD REQUEST: Invalid data in email 00000000C14B3E2B7C4E364A8A8C. Error: Invalid input
```

**Common causes:**
- Email body too long (>8000 tokens)
- Malformed email content
- Special characters or encoding issues
- Empty/null fields

**What to do:**
- ✅ Implement content truncation
- ✅ Sanitize email input
- ✅ Add character encoding handling

---

### 5. ❌ UNEXPECTED ERROR
**What it means:** Something went wrong that wasn't handled

**Log example:**
```
[Task Extraction] ❌ UNEXPECTED ERROR (KeyError) processing email 00000000C14B3E2B7C4E364A8A8C: 'action_required'
```

**Common causes:**
- Bug in code
- Missing field in response
- Type mismatch
- Database constraint violation

**What to do:**
- 🐛 This is a real bug - needs investigation
- 🐛 Check stack trace in logs
- 🐛 Add defensive coding for missing fields

---

## How to View Errors

### In Terminal/Console
Backend logs show in real-time:
```
INFO:     Started server process [12345]
[Task Extraction] Starting background processing for 10 emails
[Task Extraction] ⚠️ CONTENT FILTER blocked action extraction for email 00000000C14B3E2B...
[Task Extraction] ⏱️ RATE LIMIT hit during job listing extraction for email 00000000D25C4F3A...
[Task Extraction] Created task #103 for email 00000000A18B2D1C...
```

### In Task Descriptions
Failed tasks show the error:
```
Title: [ACTION REQUIRED] Credential Expiring
Description: Action: Review email manually
Details: AI service unavailable
Relevance: Manual review needed
```

---

## Current Rate Limiting

The code now includes delays to prevent rate limiting:

| Operation | Delay | Purpose |
|-----------|-------|---------|
| Classification | 1.0s | Before classifying unclassified emails |
| Action extraction | 1.5s | Before extracting action items |
| Job listings | 1.5s | Before analyzing job postings |
| Events | 1.5s | Before assessing event relevance |
| Summaries | 1.5s | Before generating newsletter/FYI summaries |
| Between emails | 2.0s | Cooldown between processing emails |

**Total time for 10 emails:** ~20-30 seconds (depends on category mix)

---

## Debugging Checklist

When you see "AI service unavailable" in tasks:

1. ✅ Check backend terminal logs for the emoji indicators
2. ✅ Look for the specific error type (filter, rate, connection, etc.)
3. ✅ If CONTENT FILTER: Expected - email has flagged content
4. ✅ If RATE LIMIT: Increase delays or reduce batch size
5. ✅ If CONNECTION: Check network, retry
6. ✅ If UNEXPECTED: File a bug with full error message

---

## Example Full Log Session

```
[Task Extraction] Starting background processing for 7 emails
[Task Extraction] Processing email 00000000C14B3E2B7C4E364A8A8C...
[Task Extraction] ⚠️ CONTENT FILTER blocked action extraction for email 00000000C14B3E2B: ResponsibleAIPolicyViolation
[Task Extraction] Created task #96 for email 00000000A18B2D1C (fallback content)
[Task Extraction] ⏱️ RATE LIMIT hit during event extraction for email 00000000D25C4F3A: 429 Too Many Requests
[Task Extraction] 🔌 CONNECTION: Network issue processing email 00000000E36D5G4B: Connection timeout
[Task Extraction] Created task #97 for email 00000000F47E6H5C
[Task Extraction] Created task #98 for email 00000000G58F7I6D
[Task Extraction] Completed: 5 tasks, 2 summaries created
```

In this example:
- 1 email blocked by content filter
- 1 email hit rate limit
- 1 email had connection issue
- 4 emails processed successfully

This is **normal operation** - some failures are expected!
