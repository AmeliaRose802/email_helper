"""FastAPI main application for Email Helper API.

This module creates the main FastAPI application with all necessary middleware,
routers, and configuration for the Email Helper mobile backend.
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add src to Python path for existing service imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backend.core.config import settings
from backend.database.connection import db_manager
from backend.api import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    print("🚀 Starting Email Helper API...")
    print(f"📊 Database path: {db_manager.db_path}")
    
    # Ensure database is ready
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            print(f"📋 Database initialized with {table_count} tables")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Email Helper API...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="REST API for Email Helper mobile application",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware for React Native integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent response format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        with db_manager.get_connection() as conn:
            conn.execute("SELECT 1")
        
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "service": "email-helper-api",
        "version": settings.app_version,
        "database": db_status,
        "debug": settings.debug
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Email Helper API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Import and include email router
from backend.api import emails
app.include_router(emails.router, prefix="/api", tags=["emails"])

# Import and include AI router (T3)
from backend.api import ai
app.include_router(ai.router, prefix="/api", tags=["ai"])

# Import and include task router (T4)
from backend.api import tasks
app.include_router(tasks.router, prefix="/api", tags=["tasks"])

# Import and include processing router (T9)
from backend.api import processing
app.include_router(processing.router, prefix="/api", tags=["processing"])


# Service factory integration for existing services
def get_service_factory():
    """Get service factory for existing Email Helper services."""
    try:
        from core.service_factory import ServiceFactory
        return ServiceFactory()
    except ImportError as e:
        print(f"Warning: Could not import ServiceFactory: {e}")
        return None


def get_email_processor(factory=None):
    """Get email processor service."""
    if factory is None:
        factory = get_service_factory()
    
    if factory:
        try:
            return factory.get_email_processor()
        except Exception as e:
            print(f"Warning: Could not get email processor: {e}")
    
    return None


def get_ai_processor(factory=None):
    """Get AI processor service."""
    if factory is None:
        factory = get_service_factory()
    
    if factory:
        try:
            return factory.get_ai_processor()
        except Exception as e:
            print(f"Warning: Could not get AI processor: {e}")
    
    return None


# Additional endpoints can be added here for email processing, tasks, etc.


if __name__ == "__main__":
    import uvicorn
    
    print(f"🌟 Starting {settings.app_name} v{settings.app_version}")
    print(f"🔧 Debug mode: {settings.debug}")
    print(f"🌐 Server: {settings.host}:{settings.port}")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )