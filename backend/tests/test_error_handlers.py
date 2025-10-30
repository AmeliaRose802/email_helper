"""
Tests for FastAPI error handlers.
"""

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from unittest.mock import Mock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.exceptions import (
    EmailHelperError,
    AIServiceUnavailableError,
    EmailNotFoundError,
    ValidationError,
    AuthenticationError,
    RateLimitError
)
from backend.core.error_handlers import register_error_handlers


@pytest.fixture
def app():
    """Create test FastAPI app."""
    test_app = FastAPI()
    test_app.state.debug = False
    register_error_handlers(test_app)
    
    # Add test routes
    @test_app.get("/test/success")
    async def success():
        return {"status": "ok"}
    
    @test_app.get("/test/email-not-found")
    async def email_not_found():
        raise EmailNotFoundError(
            message="Email abc123 not found",
            details={'email_id': 'abc123'}
        )
    
    @test_app.get("/test/ai-unavailable")
    async def ai_unavailable():
        raise AIServiceUnavailableError()
    
    @test_app.get("/test/authentication-error")
    async def authentication_error():
        raise AuthenticationError(
            message="Invalid credentials"
        )
    
    @test_app.get("/test/rate-limit")
    async def rate_limit():
        raise RateLimitError(retry_after=60)
    
    @test_app.get("/test/http-404")
    async def http_404():
        raise HTTPException(status_code=404, detail="Not found")
    
    @test_app.get("/test/unexpected-error")
    async def unexpected_error():
        raise RuntimeError("Unexpected error")
    
    return test_app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app, raise_server_exceptions=False)


class TestErrorHandlers:
    """Test FastAPI error handlers."""
    
    def test_success_response(self, client):
        """Test successful request."""
        response = client.get("/test/success")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_email_not_found_error(self, client):
        """Test EmailNotFoundError handling."""
        response = client.get("/test/email-not-found")
        
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
        assert data['error'] == "Email not found."
        assert data['error_type'] == "EmailNotFoundError"
        assert data['recoverable'] is False
    
    def test_ai_service_unavailable_error(self, client):
        """Test AIServiceUnavailableError handling."""
        response = client.get("/test/ai-unavailable")
        
        assert response.status_code == 503
        data = response.json()
        assert data['success'] is False
        assert "unavailable" in data['error'].lower()
        assert data['recoverable'] is True
    
    def test_authentication_error(self, client):
        """Test AuthenticationError handling."""
        response = client.get("/test/authentication-error")
        
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert "authentication" in data['error'].lower()
    
    def test_rate_limit_error(self, client):
        """Test RateLimitError handling."""
        response = client.get("/test/rate-limit")
        
        assert response.status_code == 429
        data = response.json()
        assert data['success'] is False
        assert data['recoverable'] is True
    
    def test_http_exception(self, client):
        """Test HTTPException handling."""
        response = client.get("/test/http-404")
        
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
        assert data['error'] == "Not found"
    
    def test_unexpected_error(self, client):
        """Test unexpected error handling."""
        response = client.get("/test/unexpected-error")
        
        assert response.status_code == 500
        data = response.json()
        assert data['success'] is False
        assert "unexpected error" in data['error'].lower() or "internal" in data['error'].lower()
        assert data['recoverable'] is True
    
    def test_nonexistent_route(self, client):
        """Test 404 for nonexistent route."""
        response = client.get("/test/nonexistent")
        
        assert response.status_code == 404


class TestErrorHandlersDebugMode:
    """Test error handlers in debug mode."""
    
    @pytest.fixture
    def debug_app(self):
        """Create test app with debug mode enabled."""
        test_app = FastAPI()
        test_app.state.debug = True
        register_error_handlers(test_app)
        
        @test_app.get("/test/error")
        async def error():
            raise EmailNotFoundError(
                message="Email not found",
                details={'email_id': '123'}
            )
        
        return test_app
    
    @pytest.fixture
    def debug_client(self, debug_app):
        """Create test client for debug app."""
        return TestClient(debug_app, raise_server_exceptions=False)
    
    def test_debug_mode_includes_details(self, debug_client):
        """Test that debug mode includes error details."""
        response = debug_client.get("/test/error")
        
        data = response.json()
        assert 'details' in data
        assert data['details']['error_type'] == 'EmailNotFoundError'
        assert 'email_id' in data['details']['details']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
