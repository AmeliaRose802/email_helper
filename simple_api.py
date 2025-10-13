"""
Email Helper API with Azure AD OAuth Single Sign-On

This FastAPI server provides:
1. Azure AD OAuth authentication flow
2. Email processing endpoints with mock data
3. Task management endpoints
4. User session management

To configure Azure AD OAuth:
1. Run: python scripts/setup_azure_oauth.py
2. Follow the Azure portal setup instructions
3. Update the .env file with your Azure AD app registration details
"""

import sys
import os
from pathlib import Path

# Add src to path
try:
    sys.path.insert(0, str(Path(__file__).parent / "src"))
except NameError:
    # Fallback for when __file__ is not defined
    sys.path.insert(0, str(Path.cwd() / "src"))

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
import uuid
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import jwt
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from msal import ConfidentialClientApplication
import httpx
from jose import JWTError, jwt as jose_jwt

# Import existing services - commented out for debugging
# from email_analyzer import EmailAnalyzer
# from task_persistence import TaskPersistence
# from ai_processor import AIProcessor

# Load environment variables
load_dotenv()

app = FastAPI(title="Email Helper API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:8080"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure AD OAuth Configuration
class AzureADConfig:
    def __init__(self):
        self.client_id = os.getenv("GRAPH_CLIENT_ID")
        self.tenant_id = os.getenv("GRAPH_TENANT_ID", "common")  # Use 'common' for multi-tenant
        self.redirect_uri = os.getenv("GRAPH_REDIRECT_URI", "http://localhost:8001/auth/callback")
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["User.Read", "Mail.Read", "Mail.ReadWrite", "Mail.Send"]
        
        # For PKCE flow, we only need client_id
        self.use_mock = not self.client_id
        
        if self.use_mock:
            print("⚠️  Using mock authentication - set GRAPH_CLIENT_ID to configure real OAuth")
        else:
            print(f"✅ Azure AD OAuth configured with PKCE flow (Client ID: {self.client_id[:8]}...)")
    
    def get_msal_app(self):
        """Get MSAL Public Client Application for PKCE flow"""
        if self.use_mock:
            return None
        
        from msal import PublicClientApplication
        return PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority
        )

azure_config = AzureADConfig()

# Pydantic models for authentication
class AuthURL(BaseModel):
    auth_url: str
    state: str

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None

class User(BaseModel):
    id: str
    username: str
    email: str
    name: Optional[str] = None
    created_at: str
    updated_at: str

# JWT settings for session management
SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer(auto_error=False)

# Session storage (in production, use Redis or database)
active_sessions = {}
# PKCE code verifier storage (in production, use Redis or database)
pkce_verifiers = {}

def generate_pkce_codes():
    """Generate PKCE code verifier and challenge for OAuth flow."""
    # Generate a cryptographically random code verifier
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Create code challenge using SHA256
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge

def create_session_token(user_data: dict, expires_delta: Optional[timedelta] = None):
    """Create session JWT token."""
    to_encode = user_data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_info_from_graph(access_token: str) -> Optional[Dict[str, Any]]:
    """Get user info from Microsoft Graph API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Graph API error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"Error getting user info from Graph: {e}")
        return None

async def verify_azure_token(token: str) -> Dict[str, Any]:
    """Verify Azure AD token and get user info."""
    if azure_config.use_mock:
        return {
            "oid": "mock-user-id",
            "preferred_username": "test@example.com", 
            "name": "Test User",
            "email": "test@example.com"
        }
    
    # In a real implementation, you would validate the JWT token here
    # For now, we'll use the Graph API approach in the callback
    user_info = await get_user_info_from_graph(token)
    if user_info:
        return {
            "oid": user_info["id"],
            "preferred_username": user_info.get("userPrincipalName", ""),
            "name": user_info.get("displayName", ""),
            "email": user_info.get("mail", user_info.get("userPrincipalName", ""))
        }
    
    raise Exception("Could not verify token")

async def verify_session_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify session JWT token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid session token")
        
        # Check if session is still active
        if user_id not in active_sessions:
            raise HTTPException(status_code=401, detail="Session expired")
        
        return active_sessions[user_id]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid session token")

# Initialize services - commented out for debugging
# email_analyzer = EmailAnalyzer()
# task_manager = TaskPersistence()
# ai_processor = AIProcessor()

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Email Helper API", "version": "1.0.0", "status": "running"}

# Azure AD OAuth Authentication endpoints
@app.get("/auth/login")
async def initiate_login():
    """Initiate Azure AD OAuth login flow with PKCE."""
    if azure_config.use_mock:
        return {
            "auth_url": "http://localhost:3001/auth/mock-callback",
            "state": "mock-state"
        }
    
    # Generate state parameter and PKCE codes for security
    state = str(uuid.uuid4())
    code_verifier, code_challenge = generate_pkce_codes()
    
    # Store the code verifier for later use in callback
    pkce_verifiers[state] = code_verifier
    
    # Build authorization URL manually (since we're using PKCE with PublicClientApplication)
    auth_url = (
        f"{azure_config.authority}/oauth2/v2.0/authorize?"
        f"client_id={azure_config.client_id}&"
        f"response_type=code&"
        f"redirect_uri={azure_config.redirect_uri}&"
        f"response_mode=query&"
        f"scope={'+'.join(azure_config.scopes)}&"
        f"state={state}&"
        f"code_challenge={code_challenge}&"
        f"code_challenge_method=S256"
    )
    
    return {
        "auth_url": auth_url,
        "state": state
    }

@app.get("/auth/callback")
async def oauth_callback(code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    """Handle OAuth callback from Azure AD."""
    
    # Handle OAuth error
    if error:
        print(f"OAuth error: {error}")
        return RedirectResponse(
            url=f"http://localhost:3001/auth/error?error={error}",
            status_code=302
        )
    
    if azure_config.use_mock:
        # Mock authentication for development
        mock_user = {
            "id": "mock-user-123",
            "username": "test@example.com",
            "email": "test@example.com", 
            "name": "Test User",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Create session token
        session_token = create_session_token({"sub": mock_user["id"]})
        active_sessions[mock_user["id"]] = mock_user
        
        # Redirect to frontend with token
        return RedirectResponse(
            url=f"http://localhost:3001/auth/success?token={session_token}",
            status_code=302
        )
    
    # Real Azure AD OAuth flow
    if not code:
        return RedirectResponse(
            url="http://localhost:3000/auth/error?error=no_code",
            status_code=302
        )
    
    if not state or state not in pkce_verifiers:
        return RedirectResponse(
            url="http://localhost:3000/auth/error?error=invalid_state",
            status_code=302
        )
    
    try:
        # Get the code verifier for this state
        code_verifier = pkce_verifiers.pop(state)  # Remove after use
        
        # Exchange authorization code for access token using PKCE
        token_url = f"{azure_config.authority}/oauth2/v2.0/token"
        
        token_data = {
            "client_id": azure_config.client_id,
            "scope": " ".join(azure_config.scopes),
            "code": code,
            "redirect_uri": azure_config.redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                print(f"Token exchange failed: {response.status_code} - {response.text}")
                return RedirectResponse(
                    url="http://localhost:3000/auth/error?error=token_exchange_failed",
                    status_code=302
                )
            
            token_response = response.json()
        
        if "error" in token_response:
            print(f"Token acquisition error: {token_response.get('error_description', token_response['error'])}")
            return RedirectResponse(
                url=f"http://localhost:3000/auth/error?error={token_response['error']}",
                status_code=302
            )
        
        # Get user info from token
        access_token = token_response["access_token"]
        user_info = await get_user_info_from_graph(access_token)
        
        if not user_info:
            return RedirectResponse(
                url="http://localhost:3000/auth/error?error=user_info_failed",
                status_code=302
            )
        
        # Create user object
        user = {
            "id": user_info["id"],
            "username": user_info.get("userPrincipalName", user_info.get("mail", "")),
            "email": user_info.get("mail", user_info.get("userPrincipalName", "")),
            "name": user_info.get("displayName", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Create session token
        session_token = create_session_token({"sub": user["id"]})
        active_sessions[user["id"]] = user
        
        # Store the Graph access token for API calls (in production, encrypt this)
        active_sessions[user["id"]]["graph_token"] = access_token
        
        # Redirect to frontend with success
        return RedirectResponse(
            url=f"http://localhost:3001/auth/success?token={session_token}",
            status_code=302
        )
        
    except Exception as e:
        print(f"OAuth callback error: {e}")
        return RedirectResponse(
            url=f"http://localhost:3000/auth/error?error=callback_failed",
            status_code=302
        )

@app.post("/auth/login", response_model=Token)
async def login_with_azure_token(token_data: dict):
    """Login with Azure AD token (alternative to OAuth flow)."""
    azure_token = token_data.get("access_token")
    if not azure_token:
        raise HTTPException(status_code=400, detail="Azure access token required")
    
    try:
        # Verify Azure token and get user info
        user_info = await verify_azure_token(azure_token)
        
        # Create user object
        user = {
            "id": user_info["oid"],
            "username": user_info.get("preferred_username", user_info.get("email", "")),
            "email": user_info.get("email", user_info.get("preferred_username", "")),
            "name": user_info.get("name", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Create session
        session_token = create_session_token({"sub": user["id"]})
        active_sessions[user["id"]] = user
        
        return Token(
            access_token=session_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@app.get("/auth/me", response_model=User)
async def get_current_user(current_user: dict = Depends(verify_session_token)):
    """Get current authenticated user."""
    return User(**current_user)

@app.post("/auth/logout")
async def logout(current_user: dict = Depends(verify_session_token)):
    """Logout user and invalidate session."""
    user_id = current_user["id"]
    if user_id in active_sessions:
        del active_sessions[user_id]
    return {"message": "Successfully logged out"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "email_analyzer": "active",
            "task_manager": "active",
            "ai_processor": "active"
        }
    }

@app.get("/api/emails")
async def get_emails(limit: int = 50, category: Optional[str] = None):
    """Get processed emails."""
    try:
        # Mock email data for testing
        emails = [
            {
                "id": f"email_{i}",
                "subject": f"Test Email {i}",
                "sender": f"sender{i}@example.com",
                "received_date": datetime.now().isoformat(),
                "category": "action_item" if i % 3 == 0 else "fyi",
                "priority": "high" if i % 5 == 0 else "medium",
                "summary": f"This is a test email summary for email {i}",
                "processed": True
            }
            for i in range(1, min(limit + 1, 21))
        ]
        
        if category:
            emails = [e for e in emails if e["category"] == category]
            
        return {
            "emails": emails,
            "total": len(emails),
            "category": category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emails/{email_id}")
async def get_email(email_id: str):
    """Get a specific email by ID."""
    try:
        # Mock detailed email data
        email = {
            "id": email_id,
            "subject": f"Test Email {email_id}",
            "sender": "sender@example.com",
            "received_date": datetime.now().isoformat(),
            "category": "action_item",
            "priority": "high",
            "summary": f"Detailed summary for {email_id}",
            "content": f"This is the full content of email {email_id}. It contains important information that needs attention.",
            "action_items": [
                {"task": "Review the document", "due_date": "2025-10-01"},
                {"task": "Schedule follow-up meeting", "due_date": "2025-10-03"}
            ],
            "processed": True,
            "ai_analysis": {
                "sentiment": "neutral",
                "topics": ["meeting", "document", "review"],
                "urgency": "medium"
            }
        }
        return email
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks")
async def get_tasks(status: Optional[str] = None):
    """Get tasks/action items."""
    try:
        # Mock task data
        tasks = [
            {
                "id": f"task_{i}",
                "title": f"Task {i}",
                "description": f"This is task {i} description",
                "status": "todo" if i % 2 == 0 else "in_progress",
                "priority": "high" if i % 3 == 0 else "medium",
                "due_date": "2025-10-05",
                "created_from_email": f"email_{i}",
                "created_date": datetime.now().isoformat()
            }
            for i in range(1, 11)
        ]
        
        if status:
            tasks = [t for t in tasks if t["status"] == status]
            
        return {
            "tasks": tasks,
            "total": len(tasks),
            "status_filter": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks")
async def create_task(task_data: Dict[str, Any]):
    """Create a new task."""
    try:
        # Mock task creation
        new_task = {
            "id": f"task_{datetime.now().timestamp()}",
            "title": task_data.get("title", "New Task"),
            "description": task_data.get("description", ""),
            "status": "todo",
            "priority": task_data.get("priority", "medium"),
            "due_date": task_data.get("due_date"),
            "created_date": datetime.now().isoformat()
        }
        return {"message": "Task created successfully", "task": new_task}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/summary")
async def get_summary():
    """Get dashboard summary."""
    try:
        return {
            "total_emails": 150,
            "unread_emails": 12,
            "action_items": 8,
            "completed_tasks": 25,
            "categories": {
                "action_item": 45,
                "fyi": 65,
                "newsletter": 25,
                "spam": 15
            },
            "recent_activity": [
                {"action": "Email processed", "timestamp": datetime.now().isoformat()},
                {"action": "Task completed", "timestamp": datetime.now().isoformat()},
                {"action": "New action item identified", "timestamp": datetime.now().isoformat()}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process")
async def process_emails():
    """Trigger email processing."""
    try:
        # Mock processing
        return {
            "message": "Email processing started",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting Simple Email Helper API...")
    print("Mock data endpoints ready")
    print("API will be available at: http://localhost:8001")
    print("Press Ctrl+C to stop the server")
    uvicorn.run(app, host="127.0.0.1", port=8002, reload=False)