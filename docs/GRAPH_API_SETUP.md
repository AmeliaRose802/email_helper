# Microsoft Graph API Setup Guide

This guide explains how to set up Microsoft Graph API integration for the Email Helper API T2 implementation.

## Azure AD App Registration

### Step 1: Create Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Fill in the registration form:
   - **Name**: `Email Helper API`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**: `Web` - `http://localhost:8000/auth/callback`
5. Click **Register**

### Step 2: Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission** > **Microsoft Graph** > **Delegated permissions**
3. Add the following permissions:
   - `Mail.Read` - Read user mail
   - `Mail.ReadWrite` - Read and write access to user mail
   - `Mail.Send` - Send mail as a user
   - `User.Read` - Sign in and read user profile
4. Click **Add permissions**
5. Click **Grant admin consent** (if you have admin rights)

### Step 3: Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Add description: `Email Helper API Secret`
4. Set expiration as needed (recommended: 24 months)
5. Click **Add**
6. **Copy the secret value immediately** (you won't be able to see it again)

### Step 4: Get Configuration Values

From the **Overview** page of your app registration, copy:
- **Application (client) ID** → `GRAPH_CLIENT_ID`
- **Directory (tenant) ID** → `GRAPH_TENANT_ID`
- **Client secret value** (from step 3) → `GRAPH_CLIENT_SECRET`

## Environment Configuration

Create a `.env` file in the project root with your Azure AD app values:

```env
# Microsoft Graph API Settings
GRAPH_CLIENT_ID="your-application-client-id"
GRAPH_CLIENT_SECRET="your-client-secret-value"
GRAPH_TENANT_ID="your-directory-tenant-id"
GRAPH_REDIRECT_URI="http://localhost:8000/auth/callback"
```

## Authentication Flows

### OAuth2 Authorization Code Flow (Recommended)

This is the secure flow for production applications:

1. **Get Authorization URL**:
   ```bash
   GET /api/auth/graph/authorize
   ```

2. **User visits URL and grants consent**

3. **Handle callback with authorization code**:
   ```bash
   POST /api/auth/graph/token
   {
     "authorization_code": "authorization_code_from_callback"
   }
   ```

### Username/Password Flow (Testing Only)

⚠️ **Not recommended for production** - use only for testing:

```bash
POST /api/auth/graph/token
{
  "username": "user@example.com",
  "password": "userpassword"
}
```

## API Usage Examples

### 1. Get Emails

```bash
# Get 10 most recent emails from Inbox
GET /api/emails?limit=10&folder=Inbox
Authorization: Bearer your-jwt-token
```

### 2. Get Specific Email

```bash
# Get full email content
GET /api/emails/AAMkAGE1M2IyNGNmLTI5MTktNDUyZi1iOTVl...
Authorization: Bearer your-jwt-token
```

### 3. Mark Email as Read

```bash
POST /api/emails/AAMkAGE1M2IyNGNmLTI5MTktNDUyZi1iOTVl.../mark-read
Authorization: Bearer your-jwt-token
```

### 4. Get Folders

```bash
GET /api/folders
Authorization: Bearer your-jwt-token
```

### 5. Get Conversation Thread

```bash
GET /api/conversations/AAQkAGE1M2IyNGNmLTI5MTktNDUyZi1iOTVl...
Authorization: Bearer your-jwt-token
```

## Testing with Mock Provider

For development and testing, the API automatically uses a mock email provider when Graph API credentials are not configured. The mock provider returns sample emails:

```bash
# Works without Graph API configuration
GET /api/emails
Authorization: Bearer your-jwt-token

# Returns mock emails:
{
  "emails": [
    {
      "id": "mock-email-1",
      "subject": "Test Email 1",
      "sender": "test1@example.com",
      "body": "This is a test email body."
    }
  ]
}
```

## Error Handling

The API handles various Graph API errors:

- **401 Unauthorized**: Token expired or invalid
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Email or folder not found
- **429 Too Many Requests**: Rate limiting (automatically retried)
- **500 Internal Server Error**: Graph API service errors

## Rate Limiting

The Graph API client includes automatic rate limiting handling:
- Respects `Retry-After` headers
- Exponential backoff for failed requests
- Maximum 3 retries per request

## Security Considerations

1. **Store secrets securely**: Never commit `.env` files to version control
2. **Use HTTPS in production**: Redirect URI should use HTTPS
3. **Rotate secrets regularly**: Update client secrets periodically
4. **Principle of least privilege**: Only request necessary permissions
5. **Monitor access**: Review Azure AD sign-in logs regularly

## Troubleshooting

### Common Issues

1. **"Invalid client" error**:
   - Check `GRAPH_CLIENT_ID` is correct
   - Verify app registration exists

2. **"Invalid client secret" error**:
   - Check `GRAPH_CLIENT_SECRET` is the secret value, not ID
   - Verify secret hasn't expired

3. **"Insufficient privileges" error**:
   - Check API permissions are granted
   - Ensure admin consent is given

4. **"Redirect URI mismatch" error**:
   - Verify `GRAPH_REDIRECT_URI` matches Azure AD configuration
   - Check for trailing slashes or case sensitivity

### Debug Mode

Enable debug mode to see detailed request/response logs:

```env
DEBUG=true
```

This will log Graph API requests and responses (credentials are masked).

## Production Deployment

For production deployment:

1. **Use HTTPS**: Update redirect URI to use HTTPS
2. **Environment Variables**: Use secure environment variable management
3. **Certificate Authentication**: Consider using certificates instead of secrets
4. **Monitoring**: Set up monitoring for Graph API calls and errors
5. **Backup Authentication**: Have fallback authentication methods

## Support

For issues with this integration:
1. Check Azure AD app registration configuration
2. Verify environment variables are set correctly
3. Review API error messages and status codes
4. Check Azure AD sign-in logs for authentication issues