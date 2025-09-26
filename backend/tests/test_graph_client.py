"""Tests for Microsoft Graph API client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from backend.clients.graph_client import GraphClient, GraphAPIError


class TestGraphClient:
    """Test GraphClient functionality."""
    
    @pytest.fixture
    def graph_client(self):
        """Create GraphClient instance for testing."""
        return GraphClient(
            client_id="test-client-id",
            client_secret="test-client-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:8000/test"
        )
    
    def test_initialization(self, graph_client):
        """Test GraphClient initialization."""
        assert graph_client.client_id == "test-client-id"
        assert graph_client.client_secret == "test-client-secret"
        assert graph_client.tenant_id == "test-tenant-id"
        assert graph_client.redirect_uri == "http://localhost:8000/test"
        assert graph_client.graph_base_url == "https://graph.microsoft.com/v1.0"
        assert graph_client.authority == "https://login.microsoftonline.com/test-tenant-id"
        assert graph_client.access_token is None
        assert graph_client.refresh_token is None
    
    def test_get_authorization_url(self, graph_client):
        """Test getting authorization URL."""
        with patch.object(graph_client.app, 'get_authorization_request_url') as mock_get_url:
            mock_get_url.return_value = "https://login.microsoftonline.com/auth"
            
            url = graph_client.get_authorization_url()
            
            assert url == "https://login.microsoftonline.com/auth"
            mock_get_url.assert_called_once_with(
                scopes=graph_client.scopes,
                redirect_uri=graph_client.redirect_uri
            )
    
    def test_authenticate_with_code_success(self, graph_client):
        """Test successful authentication with authorization code."""
        mock_result = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600
        }
        
        with patch.object(graph_client.app, 'acquire_token_by_authorization_code') as mock_acquire:
            mock_acquire.return_value = mock_result
            
            result = graph_client.authenticate_with_code("test-auth-code")
            
            assert result == mock_result
            assert graph_client.access_token == "test-access-token"
            assert graph_client.refresh_token == "test-refresh-token"
            assert graph_client.token_expires_at is not None
            
            mock_acquire.assert_called_once_with(
                "test-auth-code",
                scopes=graph_client.scopes,
                redirect_uri=graph_client.redirect_uri
            )
    
    def test_authenticate_with_code_failure(self, graph_client):
        """Test failed authentication with authorization code."""
        mock_result = {
            "error": "invalid_grant",
            "error_description": "Authorization code expired"
        }
        
        with patch.object(graph_client.app, 'acquire_token_by_authorization_code') as mock_acquire:
            mock_acquire.return_value = mock_result
            
            with pytest.raises(GraphAPIError, match="Authentication failed"):
                graph_client.authenticate_with_code("invalid-code")
    
    def test_authenticate_with_credentials_success(self, graph_client):
        """Test successful authentication with username/password."""
        mock_result = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600
        }
        
        with patch.object(graph_client.app, 'acquire_token_by_username_password') as mock_acquire:
            mock_acquire.return_value = mock_result
            
            result = graph_client.authenticate_with_credentials("test@example.com", "password")
            
            assert result == mock_result
            assert graph_client.access_token == "test-access-token"
            
            mock_acquire.assert_called_once_with(
                username="test@example.com",
                password="password",
                scopes=graph_client.scopes
            )
    
    def test_refresh_access_token_success(self, graph_client):
        """Test successful token refresh."""
        graph_client.refresh_token = "test-refresh-token"
        
        mock_result = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600
        }
        
        with patch.object(graph_client.app, 'acquire_token_by_refresh_token') as mock_refresh:
            mock_refresh.return_value = mock_result
            
            success = graph_client.refresh_access_token()
            
            assert success is True
            assert graph_client.access_token == "new-access-token"
            assert graph_client.refresh_token == "new-refresh-token"
            
            mock_refresh.assert_called_once_with(
                "test-refresh-token",
                scopes=graph_client.scopes
            )
    
    def test_refresh_access_token_failure(self, graph_client):
        """Test failed token refresh."""
        graph_client.refresh_token = "invalid-refresh-token"
        
        mock_result = {
            "error": "invalid_grant",
            "error_description": "Refresh token expired"
        }
        
        with patch.object(graph_client.app, 'acquire_token_by_refresh_token') as mock_refresh:
            mock_refresh.return_value = mock_result
            
            success = graph_client.refresh_access_token()
            
            assert success is False
    
    def test_ensure_valid_token_with_valid_token(self, graph_client):
        """Test ensure_valid_token with valid token."""
        from datetime import datetime, timedelta
        
        graph_client.access_token = "valid-token"
        graph_client.token_expires_at = datetime.now() + timedelta(hours=1)
        
        result = graph_client.ensure_valid_token()
        assert result is True
    
    def test_ensure_valid_token_with_expired_token(self, graph_client):
        """Test ensure_valid_token with expired token."""
        from datetime import datetime, timedelta
        
        graph_client.access_token = "expired-token"
        graph_client.token_expires_at = datetime.now() - timedelta(hours=1)
        
        with patch.object(graph_client, 'refresh_access_token') as mock_refresh:
            mock_refresh.return_value = True
            
            result = graph_client.ensure_valid_token()
            assert result is True
            mock_refresh.assert_called_once()
    
    def test_make_graph_request_success(self, graph_client):
        """Test successful Graph API request."""
        graph_client.access_token = "valid-token"
        graph_client.token_expires_at = None  # Mock as never expires
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"value": "test-data"}
        mock_response.headers.get.return_value = "application/json"
        
        with patch.object(graph_client.session, 'request') as mock_request:
            mock_request.return_value = mock_response
            
            result = graph_client._make_graph_request("GET", "/me")
            
            assert result == {"value": "test-data"}
            mock_request.assert_called_once()
    
    def test_make_graph_request_rate_limiting(self, graph_client):
        """Test Graph API request with rate limiting."""
        graph_client.access_token = "valid-token"
        graph_client.token_expires_at = None
        
        # First response: rate limited
        rate_limited_response = Mock()
        rate_limited_response.status_code = 429
        rate_limited_response.headers.get.return_value = "1"  # Retry-After: 1 second
        
        # Second response: success
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"success": True}
        success_response.headers.get.return_value = "application/json"
        
        with patch.object(graph_client.session, 'request') as mock_request:
            mock_request.side_effect = [rate_limited_response, success_response]
            
            with patch('time.sleep') as mock_sleep:
                result = graph_client._make_graph_request("GET", "/me")
                
                assert result == {"success": True}
                assert mock_request.call_count == 2
                mock_sleep.assert_called_once_with(1)
    
    def test_make_graph_request_error(self, graph_client):
        """Test Graph API request error handling."""
        graph_client.access_token = "valid-token"
        graph_client.token_expires_at = None
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.headers.get.return_value = "application/json"
        mock_response.json.return_value = {
            "error": {
                "code": "BadRequest",
                "message": "Invalid request"
            }
        }
        
        with patch.object(graph_client.session, 'request') as mock_request:
            mock_request.return_value = mock_response
            
            with pytest.raises(GraphAPIError, match="Invalid request"):
                graph_client._make_graph_request("GET", "/me")
    
    def test_get_user_profile(self, graph_client):
        """Test getting user profile."""
        with patch.object(graph_client, '_make_graph_request') as mock_request:
            mock_request.return_value = {"userPrincipalName": "test@example.com"}
            
            result = graph_client.get_user_profile()
            
            assert result == {"userPrincipalName": "test@example.com"}
            mock_request.assert_called_once_with("GET", "/me")
    
    def test_get_messages(self, graph_client):
        """Test getting messages."""
        with patch.object(graph_client, '_make_graph_request') as mock_request:
            mock_request.return_value = {
                "value": [
                    {"id": "msg1", "subject": "Test 1"},
                    {"id": "msg2", "subject": "Test 2"}
                ]
            }
            
            result = graph_client.get_messages("inbox", count=2, offset=0)
            
            assert len(result) == 2
            assert result[0]["id"] == "msg1"
            mock_request.assert_called_once_with(
                "GET", 
                "/me/mailFolders/inbox/messages",
                params={
                    "$top": 2,
                    "$skip": 0,
                    "$orderby": "receivedDateTime desc",
                    "$select": "id,subject,from,toRecipients,receivedDateTime,hasAttachments,isRead,conversationId,categories,importance,bodyPreview"
                }
            )
    
    def test_get_message_content(self, graph_client):
        """Test getting message content."""
        with patch.object(graph_client, '_make_graph_request') as mock_request:
            mock_request.return_value = {"id": "msg1", "subject": "Test", "body": {"content": "Test body"}}
            
            result = graph_client.get_message_content("msg1")
            
            assert result["id"] == "msg1"
            assert result["body"]["content"] == "Test body"
            mock_request.assert_called_once_with(
                "GET", 
                "/me/messages/msg1",
                params={"$select": "id,subject,from,toRecipients,receivedDateTime,hasAttachments,isRead,conversationId,categories,importance,body,bodyPreview"}
            )
    
    def test_get_folders(self, graph_client):
        """Test getting folders."""
        with patch.object(graph_client, '_make_graph_request') as mock_request:
            mock_request.return_value = {
                "value": [
                    {"id": "inbox", "displayName": "Inbox"},
                    {"id": "sentitems", "displayName": "Sent Items"}
                ]
            }
            
            result = graph_client.get_folders()
            
            assert len(result) == 2
            assert result[0]["displayName"] == "Inbox"
    
    def test_mark_as_read_success(self, graph_client):
        """Test marking message as read."""
        with patch.object(graph_client, '_make_graph_request') as mock_request:
            mock_request.return_value = {}
            
            result = graph_client.mark_as_read("msg1")
            
            assert result is True
            mock_request.assert_called_once_with(
                "PATCH", 
                "/me/messages/msg1",
                data={"isRead": True}
            )
    
    def test_mark_as_read_failure(self, graph_client):
        """Test failed marking message as read."""
        with patch.object(graph_client, '_make_graph_request') as mock_request:
            mock_request.side_effect = GraphAPIError("Not found", 404)
            
            result = graph_client.mark_as_read("msg1")
            
            assert result is False
    
    def test_move_message_success(self, graph_client):
        """Test moving message."""
        with patch.object(graph_client, '_make_graph_request') as mock_request:
            mock_request.return_value = {}
            
            result = graph_client.move_message("msg1", "sentitems")
            
            assert result is True
            mock_request.assert_called_once_with(
                "POST", 
                "/me/messages/msg1/move",
                data={"destinationId": "sentitems"}
            )
    
    def test_get_conversation_messages(self, graph_client):
        """Test getting conversation messages."""
        with patch.object(graph_client, '_make_graph_request') as mock_request:
            mock_request.return_value = {
                "value": [
                    {"id": "msg1", "conversationId": "conv1"},
                    {"id": "msg2", "conversationId": "conv1"}
                ]
            }
            
            result = graph_client.get_conversation_messages("conv1")
            
            assert len(result) == 2
            assert all(msg["conversationId"] == "conv1" for msg in result)
            mock_request.assert_called_once_with(
                "GET", 
                "/me/messages",
                params={
                    "$filter": "conversationId eq 'conv1'",
                    "$orderby": "receivedDateTime asc",
                    "$select": "id,subject,from,toRecipients,receivedDateTime,hasAttachments,isRead,conversationId,categories,importance,bodyPreview"
                }
            )