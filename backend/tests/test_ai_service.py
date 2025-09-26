"""Tests for AI service wrapper."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.services.ai_service import AIService, get_ai_service


class TestAIService:
    """Tests for AI service wrapper functionality."""
    
    @pytest.fixture
    def ai_service(self):
        """Create AI service instance for testing."""
        return AIService()
    
    @patch('backend.services.ai_service.AIProcessor')
    @patch('backend.services.ai_service.get_azure_config')
    def test_ai_service_initialization(self, mock_config, mock_processor, ai_service):
        """Test AI service initialization."""
        # Mock the dependencies
        mock_processor.return_value = MagicMock()
        mock_config.return_value = MagicMock()
        
        # Test lazy initialization
        assert not ai_service._initialized
        
        ai_service._ensure_initialized()
        
        assert ai_service._initialized is True
        assert ai_service.ai_processor is not None
        assert ai_service.azure_config is not None
    
    def test_ai_service_initialization_failure(self, ai_service):
        """Test AI service initialization with missing dependencies."""
        # Test with unavailable dependencies
        with patch('backend.services.ai_service.AIProcessor', None):
            with pytest.raises(RuntimeError, match="AI dependencies not available"):
                ai_service._ensure_initialized()
    
    @patch('backend.services.ai_service.AIProcessor')
    @patch('backend.services.ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_classify_email_async_success(self, mock_config, mock_processor, ai_service):
        """Test successful async email classification."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock the classification result
        mock_ai_instance.classify_email_with_explanation.return_value = {
            "category": "required_personal_action",
            "confidence": 0.9,
            "explanation": "Direct request requiring action",
            "alternatives": ["team_action"]
        }
        
        result = await ai_service.classify_email_async(
            subject="Test subject",
            content="Test content",
            sender="test@example.com",
            context="Test context"
        )
        
        assert result["category"] == "required_personal_action"
        assert result["confidence"] == 0.9
        assert "reasoning" in result
        assert "alternatives" in result
    
    @patch('backend.services.ai_service.AIProcessor')
    @patch('backend.services.ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_classify_email_async_failure(self, mock_config, mock_processor, ai_service):
        """Test async email classification with AI service failure."""
        # Mock the AI processor to raise an exception
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        mock_ai_instance.classify_email_with_explanation.side_effect = Exception("AI service unavailable")
        
        result = await ai_service.classify_email_async(
            subject="Test subject",
            content="Test content",
            sender="test@example.com"
        )
        
        # Should return fallback result with error
        assert result["category"] == "work_relevant"
        assert result["confidence"] == 0.5
        assert "error" in result
        assert "Classification failed" in result["reasoning"]
    
    @patch('backend.services.ai_service.AIProcessor')
    @patch('backend.services.ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_extract_action_items_success(self, mock_config, mock_processor, ai_service):
        """Test successful action item extraction."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock the prompty execution result
        mock_ai_instance.execute_prompty.return_value = {
            "due_date": "2024-01-15",
            "action_required": "Review quarterly report",
            "explanation": "Manager has requested report review",
            "relevance": "Directly assigned task",
            "links": ["https://company.com/reports"]
        }
        
        result = await ai_service.extract_action_items(
            email_content="Subject: Report Review\nFrom: manager@company.com\n\nPlease review the report.",
            context="Work assignment"
        )
        
        assert len(result["action_items"]) > 0
        assert result["action_required"] == "Review quarterly report"
        assert result["due_date"] == "2024-01-15"
        assert result["confidence"] == 0.8
        assert len(result["links"]) == 1
    
    @patch('backend.services.ai_service.AIProcessor')
    @patch('backend.services.ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_extract_action_items_failure(self, mock_config, mock_processor, ai_service):
        """Test action item extraction with AI service failure."""
        # Mock the AI processor to raise an exception
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        mock_ai_instance.execute_prompty.side_effect = Exception("Prompty execution failed")
        
        result = await ai_service.extract_action_items(
            email_content="Test email content"
        )
        
        # Should return fallback result with error
        assert len(result["action_items"]) == 0
        assert result["confidence"] == 0.0
        assert "error" in result
        assert "Unable to extract action items" in result["action_required"]
    
    @patch('backend.services.ai_service.AIProcessor')
    @patch('backend.services.ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_generate_summary_success(self, mock_config, mock_processor, ai_service):
        """Test successful summary generation."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock the prompty execution result
        mock_ai_instance.execute_prompty.return_value = "Manager requests quarterly report review by Friday"
        
        result = await ai_service.generate_summary(
            email_content="Subject: Report Review\nFrom: manager@company.com\n\nPlease review the quarterly report by Friday.",
            summary_type="brief"
        )
        
        assert "quarterly report" in result["summary"].lower()
        assert result["confidence"] == 0.8
        assert len(result["key_points"]) > 0
    
    @patch('backend.services.ai_service.AIProcessor')
    @patch('backend.services.ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_generate_summary_failure(self, mock_config, mock_processor, ai_service):
        """Test summary generation with AI service failure."""
        # Mock the AI processor to raise an exception
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        mock_ai_instance.execute_prompty.side_effect = Exception("Summary generation failed")
        
        result = await ai_service.generate_summary(
            email_content="Test email content"
        )
        
        # Should return fallback result with error
        assert "Unable to generate summary" in result["summary"]
        assert result["confidence"] == 0.0
        assert "error" in result
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    @pytest.mark.asyncio
    async def test_get_available_templates(self, mock_glob, mock_exists, ai_service):
        """Test getting available prompt templates."""
        # Mock templates directory exists
        mock_exists.return_value = True
        
        # Mock template files
        mock_template_files = [
            MagicMock(name="email_classifier.prompty"),
            MagicMock(name="email_summary.prompty")
        ]
        mock_template_files[0].name = "email_classifier.prompty"
        mock_template_files[1].name = "email_summary.prompty"
        mock_glob.return_value = mock_template_files
        
        # Mock file reading
        template_content = """---
description: Enhanced email classifier with explanations
---
Template content here"""
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = template_content
            
            result = await ai_service.get_available_templates()
        
        assert len(result["templates"]) == 2
        assert "email_classifier.prompty" in result["templates"]
        assert "email_summary.prompty" in result["templates"]
        assert len(result["descriptions"]) >= 0
    
    @patch('pathlib.Path.exists')
    @pytest.mark.asyncio
    async def test_get_available_templates_no_directory(self, mock_exists, ai_service):
        """Test getting templates when directory doesn't exist."""
        # Mock templates directory doesn't exist
        mock_exists.return_value = False
        
        result = await ai_service.get_available_templates()
        
        assert len(result["templates"]) == 0
        assert len(result["descriptions"]) == 0
    
    def test_get_ai_service_dependency(self):
        """Test FastAPI dependency function."""
        service = get_ai_service()
        assert isinstance(service, AIService)
        assert not service._initialized


class TestAIServiceEdgeCases:
    """Tests for AI service edge cases and error handling."""
    
    @pytest.fixture
    def ai_service(self):
        """Create AI service instance for testing."""
        return AIService()
    
    @patch('backend.services.ai_service.AIProcessor')
    @patch('backend.services.ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_classify_email_with_string_result(self, mock_config, mock_processor, ai_service):
        """Test classification when AI returns string instead of dict."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock the classification result as string
        mock_ai_instance.classify_email_with_explanation.return_value = "required_personal_action"
        
        result = await ai_service.classify_email_async(
            subject="Test subject",
            content="Test content",
            sender="test@example.com"
        )
        
        assert result["category"] == "required_personal_action"
        assert result["confidence"] == 0.8
        assert "Email classified successfully" in result["reasoning"]
    
    @patch('backend.services.ai_service.AIProcessor')
    @patch('backend.services.ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_extract_action_items_with_json_string(self, mock_config, mock_processor, ai_service):
        """Test action item extraction with JSON string result."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock the prompty execution result as JSON string
        json_result = '{"due_date": "2024-01-15", "action_required": "Review report", "explanation": "Manager request", "relevance": "Work task", "links": []}'
        mock_ai_instance.execute_prompty.return_value = json_result
        
        result = await ai_service.extract_action_items(
            email_content="Subject: Report\nFrom: manager@company.com\n\nReview this."
        )
        
        assert result["action_required"] == "Review report"
        assert result["due_date"] == "2024-01-15"
        assert result["confidence"] == 0.8
    
    @patch('backend.services.ai_service.AIProcessor')
    @patch('backend.services.ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_extract_action_items_with_invalid_json(self, mock_config, mock_processor, ai_service):
        """Test action item extraction with invalid JSON result."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock the prompty execution result as invalid JSON
        mock_ai_instance.execute_prompty.return_value = "Invalid JSON response"
        
        result = await ai_service.extract_action_items(
            email_content="Test email"
        )
        
        # Should use fallback parsing
        assert result["action_required"] == "Review email content"
        assert result["explanation"] == "Unable to parse structured response"
        assert result["confidence"] == 0.8
    
    @patch('backend.services.ai_service.AIProcessor')
    @patch('backend.services.ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_generate_summary_empty_result(self, mock_config, mock_processor, ai_service):
        """Test summary generation with empty AI result."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock empty prompty execution result
        mock_ai_instance.execute_prompty.return_value = ""
        
        result = await ai_service.generate_summary(
            email_content="Test email"
        )
        
        assert result["summary"] == "Unable to generate summary"
        assert result["confidence"] == 0.5
        assert len(result["key_points"]) == 0