"""Backend configuration for FastAPI Email Helper API."""

from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path

try:
    from backend.core.infrastructure.azure_config import get_azure_config as get_azure_config_instance
except ImportError:
    get_azure_config_instance = None

def _is_com_available() -> bool:
    """Check if COM email provider is available on this system."""
    try:
        import importlib.util
        return (
            importlib.util.find_spec("pythoncom") is not None and
            importlib.util.find_spec("backend.services.outlook.adapters.outlook_email_adapter") is not None
        )
    except (ImportError, ModuleNotFoundError):
        return False

class Settings(BaseSettings):
    """FastAPI application settings."""

    # App settings
    app_name: str = "Email Helper API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # CORS - Allow all origins for development
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])

    # Database
    database_url: Optional[str] = None

    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-02-01"

    # COM Adapter (Windows + Outlook) - Auto-detect availability
    use_com_backend: bool = Field(default_factory=_is_com_available)
    com_connection_timeout: int = 30
    com_retry_attempts: int = 3
    email_provider: Optional[str] = None

    # Development
    require_authentication: bool = False
    email_processing_limit: int = 100

    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


def get_settings() -> Settings:
    return Settings()

def get_database_path() -> str:
    """Get database path."""
    project_root = Path(__file__).parent.parent.parent
    runtime_data_dir = project_root / "runtime_data" / "database"
    runtime_data_dir.mkdir(parents=True, exist_ok=True)
    return str(runtime_data_dir / "email_helper_history.db")

def get_azure_config() -> dict:
    """Get Azure configuration."""
    settings = get_settings()

    if get_azure_config_instance:
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

    return {
        "endpoint": settings.azure_openai_endpoint,
        "api_key": settings.azure_openai_api_key,
        "deployment": settings.azure_openai_deployment,
        "api_version": settings.azure_openai_api_version,
    }

settings = get_settings()
