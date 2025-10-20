# Task Extraction Fix - Root Cause Analysis

## Problem
Tasks, newsletters, and FYI items are not being generated from emails because:

1. **Emails aren't stored in the database** - Only fetched from Outlook COM on-demand
2. **No task extraction happening** - The `/emails/extract-tasks` endpoint is never called
3. **Missing workflow** - Classification happens in frontend, but results aren't persisted or used

## Current Workflow (BROKEN)
```
Outlook → Frontend fetches → Classifies with AI → Shows in UI → ❌ STOPS HERE
```

## Required Workflow (WORKING)
```
Outlook → Frontend fetches → Classifies with AI → Stores in DB → Extract Tasks → Show tasks
```

## Solution Implementation

### Step 1: Add endpoint to sync emails to database
Add to `backend/api/emails.py`:
```python
@router.post("/emails/sync-to-database")
async def sync_emails_to_database(emails: List[Dict], user_id: int = 1):
    # Store classified emails in database
    pass
```

### Step 2: Add extraction button in frontend
Update `EmailList.tsx` to add "Extract Tasks" button after classification completes

### Step 3: Call extraction endpoint
After classification, call `/emails/extract-tasks` with classified email IDs

## Files to Modify
1. `backend/api/emails.py` - Add sync endpoint  
2. `frontend/src/pages/EmailList.tsx` - Add extraction button
3. `frontend/src/services/emailApi.ts` - Add API calls
