# API Field Naming Migration Guide

## Overview

As part of issue **email_helper-401** (API Simplification: Standardize field naming), we are standardizing field names across all API endpoints to improve consistency and reduce confusion.

## Standardized Field Names

### Email Content Fields

| **NEW (Standardized)** | **OLD (Deprecated)** | **Description** |
|------------------------|----------------------|-----------------|
| `content` | `body` | Email body content/text |
| `received_time` | `date`, `received_date` | When email was received |
| `ai_category` | N/A | AI-assigned category classification |
| `category` | N/A | User-corrected category (for accuracy tracking) |

## Migration Timeline

- **Phase 1 (Current - Month 6)**: Backward compatibility period
  - All endpoints return BOTH new and old field names
  - Frontend accepts both field names
  - New code should use standardized names
  - Old field names will show deprecation warnings in logs

- **Phase 2 (Month 6+)**: Deprecation warnings increase
  - API documentation marks old fields as deprecated
  - Console warnings when old fields are accessed
  - All new features use only standardized names

- **Phase 3 (Month 12)**: Removal of deprecated fields
  - Old field names removed from API responses
  - Breaking change - requires frontend update
  - Will be communicated via changelog and release notes

## Code Examples

### Before (Deprecated)

```typescript
// Frontend - OLD way (deprecated)
const emailDate = new Date(email.date);
const emailBody = email.body;
```

```python
# Backend - OLD way (deprecated)
email_dict = {
    'date': email.received_date,
    'body': email.content,
}
```

### After (Standardized)

```typescript
// Frontend - NEW way (standardized)
const emailDate = new Date(email.received_time);
const emailBody = email.content;
```

```python
# Backend - NEW way (standardized)
email_dict = {
    'received_time': email.received_time,
    'content': email.content,
    'ai_category': email.ai_category,
}
```

### Backward Compatible Access (Transition Period)

```typescript
// Frontend - Safe approach during transition
const emailDate = new Date(email.received_time || email.date);
const emailBody = email.content || email.body;
```

## Updated Endpoints

All endpoints that return email data now use standardized field names:

- `GET /api/emails` - List emails
- `GET /api/emails/{id}` - Get single email
- `GET /api/emails/search` - Search emails
- `POST /api/emails/batch-process` - Batch process emails
- `POST /api/emails/bulk-apply-to-outlook` - Bulk apply classifications

AI endpoints:

- `POST /api/ai/classify` - Classify email (returns `ai_category`)
- `POST /api/ai/classify-batch-stream` - Stream classification (returns `ai_category`)

## Testing

Run the field consistency test suite to verify standardization:

```bash
pytest backend/tests/test_api_field_consistency.py -v
```

## Benefits

### For Developers

1. **Clearer intent**: `content` is more professional than `body`
2. **No ambiguity**: `received_time` is more specific than `date`
3. **Consistent codebase**: Same field names everywhere
4. **Fewer bugs**: No more mapping between different field names

### For Users

1. **More reliable**: Fewer edge cases and bugs
2. **Better performance**: Simplified frontend cache management
3. **Clearer API**: Documentation is more consistent

## Breaking Changes

### In Month 12 (Final Migration)

When deprecated fields are removed, the following will break:

```typescript
// ❌ This will break:
const date = email.date;  // Field removed
const body = email.body;  // Field removed

// ✅ Use this instead:
const date = email.received_time;
const body = email.content;
```

## Migration Checklist

For **Frontend Developers**:

- [ ] Update all `email.date` references to `email.received_time`
- [ ] Update all `email.body` references to `email.content`
- [ ] Update TypeScript types to use standardized field names
- [ ] Test with both old and new API responses
- [ ] Remove backward compatibility code after Month 12

For **Backend Developers**:

- [ ] Return both standardized and deprecated fields
- [ ] Log deprecation warnings when old fields are accessed
- [ ] Update documentation to show preferred field names
- [ ] Plan removal of deprecated fields for Month 12 release

For **API Consumers**:

- [ ] Review API documentation for field name changes
- [ ] Update client code to use standardized names
- [ ] Plan for breaking changes in Month 12
- [ ] Subscribe to changelog for migration updates

## Related Issues

- **email_helper-401**: API Simplification: Standardize field naming
- **email_helper-402**: API Simplification: Unify pagination
- **email_helper-411**: Epic: API Contract Simplification and Standardization

## Questions?

If you have questions about this migration, please:

1. Check this guide first
2. Review the test suite: `backend/tests/test_api_field_consistency.py`
3. Check the API documentation
4. File an issue with the `api` label
