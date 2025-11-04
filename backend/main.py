"""FastAPI main application for Email Helper API."""

from contextlib import asynccontextmanager
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.database.connection import db_manager

# Configure console encoding FIRST to prevent Unicode errors
try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass  # Ignore if reconfigure not available

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info(f"Starting Email Helper API v{settings.app_version}")
    logger.info(f"Database: {db_manager.db_path}")

    try:
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            logger.info(f"Database ready with {table_count} tables")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down Email Helper API...")
    try:
        # Close database connections gracefully
        if hasattr(db_manager, 'close_all_connections'):
            db_manager.close_all_connections()
            logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="REST API for Email Helper mobile application",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        with db_manager.get_connection() as conn:
            conn.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy",
        "service": "email-helper-api",
        "version": settings.app_version,
        "database": db_status
    }

@app.get("/")
async def root():
    return {
        "message": "Email Helper API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
from backend.api import emails, ai, tasks, processing, email_analysis
from backend.api import settings as settings_api

app.include_router(emails.router, prefix="/api", tags=["emails"])
app.include_router(email_analysis.router, prefix="/api", tags=["email-analysis"])
app.include_router(ai.router, prefix="/api", tags=["ai"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(processing.router, prefix="/api", tags=["processing"])
app.include_router(settings_api.router, prefix="/api", tags=["settings"])



if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting {settings.app_name} v{settings.app_version} on {settings.host}:{settings.port}")

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )

