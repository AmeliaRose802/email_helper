"""Backend configuration management for FastAPI Email Helper API.

This module extends the existing configuration patterns to support FastAPI-specific
settings while maintaining compatibility with the existing Email Helper infrastructure.
"""

import os
import json
from typing import Optional, List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path

try:
    from backend.core.infrastructure.azure_config import get_azure_config as get_azure_config_instance
except ImportError:
    # Fallback if backend modules can't be imported
    get_azure_config_instance = None


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
    
    # CORS settings - Allow all origins for development
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])
    
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
    use_com_backend: bool = True  # Enable COM email provider and AI service for localhost
    com_connection_timeout: int = 30  # Seconds to wait for COM connection
    com_retry_attempts: int = 3  # Number of retry attempts for COM operations
    email_provider: Optional[str] = None  # Email provider: 'com' or 'graph'
    
    # Localhost development settings (disabled for desktop app)
    require_authentication: bool = False  # Set to False for localhost development without auth
    
    # Email processing settings
    email_processing_limit: int = 100  # Default number of emails to process for stats
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


def get_database_path() -> str:
    """Get database path using existing configuration patterns."""
    # Use standard path - no need for src dependency
    project_root = Path(__file__).parent.parent.parent
    runtime_data_dir = project_root / "runtime_data" / "database"
    runtime_data_dir.mkdir(parents=True, exist_ok=True)
    return str(runtime_data_dir / "email_helper_history.db")


def get_azure_config() -> dict:
    """Get Azure configuration compatible with existing systems."""
    settings = get_settings()
    
    if get_azure_config_instance:
        # Use the migrated Azure config from infrastructure
        try:
            azure_config_obj = get_azure_config_instance()
            return {
                "endpoint": azure_config_obj.endpoint,
                "api_key": azure_config_obj.get_api_key(),
                "deployment": azure_config_obj.deployment,
                "api_version": azure_config_obj.api_version,
            }
        except Exception:
            pass
    
    # Fallback to settings
    return {
        "endpoint": settings.azure_openai_endpoint,
        "api_key": settings.azure_openai_api_key,
        "deployment": settings.azure_openai_deployment,
        "api_version": settings.azure_openai_api_version,
    }


# Global settings instance
settings = get_settings()