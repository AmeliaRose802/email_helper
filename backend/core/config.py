"""Backend configuration management for FastAPI Email Helper API.

This module extends the existing configuration patterns to support FastAPI-specific
settings while maintaining compatibility with the existing Email Helper infrastructure.
"""

import os
import sys
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path

# Add src to Python path to import existing config
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from core.config import config as core_config
except ImportError:
    # Fallback if src modules can't be imported
    core_config = None


class Settings(BaseSettings):
    """FastAPI application settings."""
    
    # App settings
    app_name: str = "Email Helper API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    
    # CORS settings
    cors_origins: list = Field(default=["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list = Field(default=["*"])
    cors_allow_headers: list = Field(default=["*"])
    
    # Database settings
    database_url: Optional[str] = None
    
    # Azure OpenAI settings (from existing config)
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-02-01"
    
    # Microsoft Graph API settings
    graph_client_id: Optional[str] = None
    graph_client_secret: Optional[str] = None
    graph_tenant_id: Optional[str] = None
    graph_redirect_uri: str = "http://localhost:8000/auth/callback"
    
    # COM Adapter settings (for Windows + Outlook integration)
    use_com_backend: bool = False  # Enable COM email provider and AI service
    com_connection_timeout: int = 30  # Seconds to wait for COM connection
    com_retry_attempts: int = 3  # Number of retry attempts for COM operations
    email_provider: Optional[str] = None  # Email provider: 'com' or 'graph'
    
    # Localhost development settings
    require_authentication: bool = True  # Set to False for localhost development without auth
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


def get_database_path() -> str:
    """Get database path using existing configuration patterns."""
    if core_config:
        # Use existing config if available
        return core_config.get_storage_path("email_helper_history.db")
    else:
        # Fallback path
        project_root = Path(__file__).parent.parent.parent
        runtime_data_dir = project_root / "runtime_data"
        runtime_data_dir.mkdir(exist_ok=True)
        return str(runtime_data_dir / "email_helper_history.db")


def get_azure_config() -> dict:
    """Get Azure configuration compatible with existing systems."""
    settings = get_settings()
    
    if core_config:
        # Use existing Azure config if available
        azure_config = core_config.get_azure_config()
        return {
            "endpoint": azure_config.get("endpoint") or settings.azure_openai_endpoint,
            "api_key": azure_config.get("api_key") or settings.azure_openai_api_key,
            "deployment": azure_config.get("deployment_name") or settings.azure_openai_deployment,
            "api_version": azure_config.get("api_version") or settings.azure_openai_api_version,
        }
    else:
        return {
            "endpoint": settings.azure_openai_endpoint,
            "api_key": settings.azure_openai_api_key,
            "deployment": settings.azure_openai_deployment,
            "api_version": settings.azure_openai_api_version,
        }


# Global settings instance
settings = get_settings()