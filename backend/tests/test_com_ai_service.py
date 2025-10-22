"""Tests for COM AI service adapter.

This test module verifies that the COMAIService correctly wraps AIProcessor
functionality and provides async FastAPI-compatible methods for COM-based
email processing.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock, Mock
import json
from backend.services.com_ai_service import COMAIService, get_com_ai_service


class TestCOMAIService:
    """Tests for COM AI service adapter functionality."""
    
    @pytest.fixture
    def com_ai_service(self):
        """Create COM AI service instance for testing."""
        return COMAIService()
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    def test_service_initialization(self, mock_config, mock_processor, com_ai_service):
        """Test COM AI service initialization."""
        # Mock the dependencies
        mock_processor.return_value = MagicMock()
        mock_config.return_value = MagicMock()
        
        # Test lazy initialization
        assert not com_ai_service._initialized
        
        com_ai_service._ensure_initialized()
        
        assert com_ai_service._initialized is True
        assert com_ai_service.ai_processor is not None
        assert com_ai_service.azure_config is not None
    
    def test_service_initialization_failure(self, com_ai_service):
        """Test service initialization with missing dependencies."""
        # Test with unavailable dependencies
        with patch('backend.services.com_ai_service.AIProcessor', None):
            with pytest.raises(RuntimeError, match="AI dependencies not available"):
                com_ai_service._ensure_initialized()
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_classify_email_success(self, mock_config, mock_processor, com_ai_service):
        """Test successful email classification."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Set confidence thresholds
        mock_ai_instance.CONFIDENCE_THRESHOLDS = {
            'required_personal_action': 1.0,
            'work_relevant': 0.8,
            'fyi': 0.9
        }
        
        # Mock the classification result
        mock_ai_instance.classify_email_with_explanation.return_value = {
            "category": "required_personal_action",
            "confidence": 0.95,
            "explanation": "Direct request requiring action",
            "alternatives": [{"category": "work_relevant", "confidence": 0.85}]
        }
        
        result = await com_ai_service.classify_email(
            email_content="Subject: Urgent Task\n\nPlease complete by EOD",
            context="Work context"
        )
        
        assert result["category"] == "required_personal_action"
        assert result["confidence"] == 0.95
        assert "reasoning" in result
        assert "Direct request" in result["reasoning"]
        assert "alternatives" in result
        assert len(result["alternatives"]) > 0
        assert "requires_review" in result
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_classify_email_failure(self, mock_config, mock_processor, com_ai_service):
        """Test email classification with AI service failure."""
        # Mock the AI processor to raise an exception
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        mock_ai_instance.classify_email_with_explanation.side_effect = Exception("AI service unavailable")
        
        result = await com_ai_service.classify_email(
            email_content="Subject: Test\n\nContent"
        )
        
        # Should return fallback result with error
        assert result["category"] == "work_relevant"
        assert result["confidence"] == 0.5
        assert "error" in result
        assert "Classification failed" in result["reasoning"]
        assert result["requires_review"] is True
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_classify_email_string_result(self, mock_config, mock_processor, com_ai_service):
        """Test classification when AI returns string instead of dict."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock the classification result as string
        mock_ai_instance.classify_email_with_explanation.return_value = "work_relevant"
        
        result = await com_ai_service.classify_email(
            email_content="Subject: Test\n\nContent"
        )
        
        assert result["category"] == "work_relevant"
        assert result["confidence"] == 0.8
        assert "Email classified successfully" in result["reasoning"]
        assert result["requires_review"] is True
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_extract_action_items_success(self, mock_config, mock_processor, com_ai_service):
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
        
        result = await com_ai_service.extract_action_items(
            email_content="Subject: Report Review\n\nPlease review the report.",
            context="Work assignment"
        )
        
        assert len(result["action_items"]) > 0
        assert result["action_required"] == "Review quarterly report"
        assert result["due_date"] == "2024-01-15"
        assert result["confidence"] == 0.8
        assert len(result["links"]) == 1
        assert "error" not in result
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_extract_action_items_json_string(self, mock_config, mock_processor, com_ai_service):
        """Test action item extraction with JSON string result."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock the prompty execution result as JSON string
        json_result = json.dumps({
            "due_date": "2024-01-20",
            "action_required": "Complete survey",
            "explanation": "Team feedback needed",
            "relevance": "Team request",
            "links": []
        })
        mock_ai_instance.execute_prompty.return_value = json_result
        
        result = await com_ai_service.extract_action_items(
            email_content="Subject: Survey\n\nPlease complete the survey."
        )
        
        assert result["action_required"] == "Complete survey"
        assert result["due_date"] == "2024-01-20"
        assert result["confidence"] == 0.8
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_extract_action_items_non_json(self, mock_config, mock_processor, com_ai_service):
        """Test action item extraction with non-JSON result."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock the prompty execution result as plain text
        mock_ai_instance.execute_prompty.return_value = "Please review the document by Friday"
        
        result = await com_ai_service.extract_action_items(
            email_content="Subject: Document Review\n\nContent"
        )
        
        # Should use fallback parsing
        assert "Please review" in result["action_required"]
        assert result["confidence"] == 0.8
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_extract_action_items_failure(self, mock_config, mock_processor, com_ai_service):
        """Test action item extraction with AI service failure."""
        # Mock the AI processor to raise an exception
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        mock_ai_instance.execute_prompty.side_effect = Exception("Prompty execution failed")
        
        result = await com_ai_service.extract_action_items(
            email_content="Test email content"
        )
        
        # Should return fallback result with error
        assert len(result["action_items"]) == 0
        assert result["confidence"] == 0.0
        assert "error" in result
        assert "Unable to extract action items" in result["action_required"]
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_generate_summary_success(self, mock_config, mock_processor, com_ai_service):
        """Test successful summary generation."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock the prompty execution result
        mock_ai_instance.execute_prompty.return_value = "Manager requests quarterly report review by Friday"
        
        result = await com_ai_service.generate_summary(
            email_content="Subject: Report Review\n\nPlease review the quarterly report by Friday.",
            summary_type="brief"
        )
        
        assert "quarterly report" in result["summary"].lower()
        assert result["confidence"] == 0.8
        assert len(result["key_points"]) > 0
        assert "error" not in result
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_generate_summary_failure(self, mock_config, mock_processor, com_ai_service):
        """Test summary generation with AI service failure."""
        # Mock the AI processor to raise an exception
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        mock_ai_instance.execute_prompty.side_effect = Exception("Summary generation failed")
        
        result = await com_ai_service.generate_summary(
            email_content="Test email content"
        )
        
        # Should return fallback result with error
        assert "Unable to generate summary" in result["summary"]
        assert result["confidence"] == 0.0
        assert "error" in result
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_generate_summary_empty_result(self, mock_config, mock_processor, com_ai_service):
        """Test summary generation with empty AI result."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock empty prompty execution result
        mock_ai_instance.execute_prompty.return_value = ""
        
        result = await com_ai_service.generate_summary(
            email_content="Test email"
        )
        
        assert result["summary"] == "Unable to generate summary"
        assert result["confidence"] == 0.5
        assert len(result["key_points"]) == 0
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_detect_duplicates_success(self, mock_config, mock_processor, com_ai_service):
        """Test successful duplicate detection."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock the prompty execution result
        mock_ai_instance.execute_prompty.return_value = {
            "duplicate_ids": ["email_2", "email_3"]
        }
        
        emails = [
            {"id": "email_1", "subject": "Test 1", "content": "Content 1"},
            {"id": "email_2", "subject": "Test 2", "content": "Duplicate content"},
            {"id": "email_3", "subject": "Test 2", "content": "Duplicate content"}
        ]
        
        result = await com_ai_service.detect_duplicates(emails)
        
        assert len(result) == 2
        assert "email_2" in result
        assert "email_3" in result
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_detect_duplicates_single_email(self, mock_config, mock_processor, com_ai_service):
        """Test duplicate detection with single email."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        emails = [
            {"id": "email_1", "subject": "Test", "content": "Content"}
        ]
        
        result = await com_ai_service.detect_duplicates(emails)
        
        # Should return empty list for single email
        assert len(result) == 0
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_detect_duplicates_failure(self, mock_config, mock_processor, com_ai_service):
        """Test duplicate detection with AI service failure."""
        # Mock the AI processor to raise an exception
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        mock_ai_instance.execute_prompty.side_effect = Exception("Duplicate detection failed")
        
        emails = [
            {"id": "email_1", "subject": "Test 1", "content": "Content 1"},
            {"id": "email_2", "subject": "Test 2", "content": "Content 2"}
        ]
        
        result = await com_ai_service.detect_duplicates(emails)
        
        # Should return empty list on error
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_available_templates(self, com_ai_service):
        """Test getting available prompty templates."""
        # Mock the prompts directory
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.glob') as mock_glob:
            
            mock_exists.return_value = True
            
            # Mock template files
            mock_template_files = [
                Mock(name="email_classifier.prompty"),
                Mock(name="action_item.prompty")
            ]
            mock_template_files[0].name = "email_classifier.prompty"
            mock_template_files[1].name = "action_item.prompty"
            mock_glob.return_value = mock_template_files
            
            # Mock file reading
            template_content = """---
description: Email classification template
---
Template content here"""
            
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = template_content
                
                result = await com_ai_service.get_available_templates()
            
            assert len(result["templates"]) == 2
            assert "email_classifier.prompty" in result["templates"]
            assert "action_item.prompty" in result["templates"]
    
    @pytest.mark.asyncio
    async def test_get_available_templates_no_directory(self, com_ai_service):
        """Test getting templates when directory doesn't exist."""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            
            result = await com_ai_service.get_available_templates()
            
            assert len(result["templates"]) == 0
            assert len(result["descriptions"]) == 0
    
    def test_get_com_ai_service_dependency(self):
        """Test FastAPI dependency function."""
        service = get_com_ai_service()
        assert isinstance(service, COMAIService)
        assert not service._initialized
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    def test_requires_review_low_confidence(self, mock_config, mock_processor, com_ai_service):
        """Test that low confidence requires review."""
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        mock_ai_instance.CONFIDENCE_THRESHOLDS = {
            'optional_action': 0.8,
            'work_relevant': 0.8
        }
        
        com_ai_service._ensure_initialized()
        
        # Test below threshold
        assert com_ai_service._requires_review('optional_action', 0.6) is True
        
        # Test above threshold
        assert com_ai_service._requires_review('optional_action', 0.9) is False
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    def test_requires_review_no_thresholds(self, mock_config, mock_processor, com_ai_service):
        """Test review requirement when thresholds unavailable."""
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Don't set CONFIDENCE_THRESHOLDS attribute
        del mock_ai_instance.CONFIDENCE_THRESHOLDS
        
        com_ai_service._ensure_initialized()
        
        # Should default to requiring review
        assert com_ai_service._requires_review('any_category', 0.95) is True


class TestCOMAIServiceEdgeCases:
    """Tests for COM AI service edge cases and error handling."""
    
    @pytest.fixture
    def com_ai_service(self):
        """Create COM AI service instance for testing."""
        return COMAIService()
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_extract_action_items_dict_result(self, mock_config, mock_processor, com_ai_service):
        """Test action item extraction with dict result."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock the prompty execution result as dict
        mock_ai_instance.execute_prompty.return_value = {
            "due_date": "2024-02-01",
            "action_required": "Submit proposal",
            "explanation": "Proposal due date approaching",
            "relevance": "Project requirement",
            "links": ["http://project.com"]
        }
        
        result = await com_ai_service.extract_action_items(
            email_content="Subject: Proposal\n\nSubmit by Feb 1"
        )
        
        assert result["action_required"] == "Submit proposal"
        assert result["due_date"] == "2024-02-01"
        assert len(result["action_items"]) == 1
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_detect_duplicates_list_result(self, mock_config, mock_processor, com_ai_service):
        """Test duplicate detection with list result."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock the prompty execution result as list
        mock_ai_instance.execute_prompty.return_value = ["email_1", "email_3"]
        
        emails = [
            {"id": "email_1", "subject": "Dup", "content": "Content"},
            {"id": "email_2", "subject": "Unique", "content": "Different"},
            {"id": "email_3", "subject": "Dup", "content": "Content"}
        ]
        
        result = await com_ai_service.detect_duplicates(emails)
        
        assert len(result) == 2
        assert "email_1" in result
        assert "email_3" in result
    
    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_generate_summary_with_long_text(self, mock_config, mock_processor, com_ai_service):
        """Test summary generation with long summary text."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        
        # Mock long summary with multiple sentences
        long_summary = "First key point about the meeting. Second important detail about the project. Third critical deadline for completion."
        mock_ai_instance.execute_prompty.return_value = long_summary
        
        result = await com_ai_service.generate_summary(
            email_content="Subject: Project Update\n\nDetailed content"
        )
        
        assert result["summary"] == long_summary

    @patch('backend.services.com_ai_service.AIProcessor')
    @patch('backend.services.com_ai_service.get_azure_config')
    @pytest.mark.asyncio
    async def test_extract_action_items_input_format(self, mock_config, mock_processor, com_ai_service):
        """Test that action item extraction passes correct input format to prompty."""
        # Mock the AI processor
        mock_ai_instance = MagicMock()
        mock_processor.return_value = mock_ai_instance
        mock_config.return_value = MagicMock()
        mock_ai_instance.get_username.return_value = "TestUser"
        
        # Mock the prompty execution result
        mock_ai_instance.execute_prompty.return_value = {
            "due_date": "2024-01-15",
            "action_required": "Complete code review",
            "explanation": "PR needs approval",
            "relevance": "Blocking team",
            "links": ["https://github.com/pr/123"]
        }
        
        # Call with formatted email text
        email_text = "Subject: Code Review Needed\nFrom: john@example.com\nDate: 2024-01-10\n\nPlease review PR #123 by Friday."
        result = await com_ai_service.extract_action_items(
            email_content=email_text,
            context="Work assignment"
        )
        
        # Verify prompty was called with correct inputs
        mock_ai_instance.execute_prompty.assert_called_once()
        call_args = mock_ai_instance.execute_prompty.call_args
        
        # Verify prompty file name
        assert call_args[0][0] == "summerize_action_item.prompty"
        
        # Verify inputs contain all required fields
        inputs = call_args[1]['inputs']
        assert 'context' in inputs
        assert 'username' in inputs
        assert 'subject' in inputs
        assert 'sender' in inputs
        assert 'date' in inputs
        assert 'body' in inputs
        
        # Verify parsed values are correct
        assert inputs['subject'] == "Code Review Needed"
        assert inputs['sender'] == "john@example.com"
        assert inputs['date'] == "2024-01-10"
        assert "Please review PR #123" in inputs['body']
        
        # Verify result structure
        assert result["action_required"] == "Complete code review"
        assert "https://github.com/pr/123" in result["links"]
        assert result["confidence"] == 0.8
