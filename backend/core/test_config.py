"""Test-specific configuration for backend tests.

This module provides test-specific settings that override production settings
to prevent database conflicts, side effects, and ensure tests run in isolation.

PORT ALLOCATION NOTES:
- Production Backend: 8000
- Production Frontend (Vite dev): 5173  
- Test Backend: 58000 (configured but not used - see below)
- Test Frontend: Uses same 5173 (Playwright E2E tests)

IMPORTANT: FastAPI TestClient doesn't actually start a server - it simulates
HTTP requests directly to the app object. The test port 58000 is configured
for completeness but isn't actively used since no server starts.

The REAL value of test settings:
✓ Separate test database (:memory: or temp file) - no production data pollution
✓ Disabled COM backend - tests use mocks instead
✓ Shorter timeouts - tests run faster
✓ Test-specific Azure config - no real API calls
✓ Clear test mode detection via is_test_mode()

This prevents the zombie process issue mentioned in email_helper-42 by ensuring
tests use isolated resources and don't interfere with development servers.
"""

import os
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    """Test-specific FastAPI application settings.
    
    These settings are used exclusively during testing and override
    production settings to prevent port conflicts and side effects.
    """
    
    # App settings
    app_name: str = "Email Helper API - TEST MODE"
    app_version: str = "1.0.0-test"
    debug: bool = True
    
    # Test server settings - Use different ports from production
    # Production uses: 8000 (backend), 3001 (frontend)
    # Tests use: 58000 (if needed), 53001 (if needed)
    host: str = "127.0.0.1"  # Localhost only for tests
    port: int = 58000  # Different from production (8000)
    
    # CORS settings - Restricted for tests
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:53001", "http://127.0.0.1:53001"])
    cors_allow_credentials: bool = False
    cors_allow_methods: List[str] = Field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])
    
    # Test database - Always use in-memory or temp file
    database_url: str = "sqlite:///:memory:"
    
    # Azure OpenAI - Mock settings for tests
    azure_openai_endpoint: str = "https://test.openai.azure.com/"
    azure_openai_api_key: str = "test-api-key-not-real"
    azure_openai_deployment: str = "test-deployment"
    azure_openai_api_version: str = "2024-02-01"
    
    # COM Adapter - Disabled for tests by default
    use_com_backend: bool = False
    com_connection_timeout: int = 5  # Shorter timeout for tests
    com_retry_attempts: int = 1  # Fewer retries for tests
    email_provider: str = "mock"  # Always use mock in tests
    
    # Email processing - Smaller limits for tests
    email_processing_limit: int = 10
    
    model_config = {
        "env_prefix": "TEST_",  # Only load TEST_* environment variables
        "case_sensitive": False
    }


def get_test_settings() -> TestSettings:
    """Get test-specific application settings."""
    return TestSettings()


def get_test_database_path() -> str:
    """Get test database path - always use a temp location."""
    project_root = Path(__file__).parent.parent.parent
    test_data_dir = project_root / "runtime_data" / "test_data"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Use unique database file for each test run to avoid conflicts
    import uuid
    db_file = test_data_dir / f"test_db_{uuid.uuid4().hex[:8]}.db"
    return str(db_file)


# Test settings instance
test_settings = get_test_settings()


# Environment marker to detect if we're running in test mode
def is_test_mode() -> bool:
    """Check if we're running in test mode.
    
    Returns:
        bool: True if running tests, False otherwise
    """
    return (
        os.environ.get("PYTEST_CURRENT_TEST") is not None or
        os.environ.get("TEST_MODE") == "true" or
        "pytest" in os.environ.get("_", "")
    )
