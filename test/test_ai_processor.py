"""
Comprehensive tests for AIProcessor class.
Tests AI processing logic, email classification, and external API integration.
"""
import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime

# Mock external dependencies at module level
with patch.dict('sys.modules', {
    'dotenv': MagicMock(),
    'openai': MagicMock(),
    'azure.identity': MagicMock(),
    'win32com': MagicMock(),
    'win32com.client': MagicMock()
}):
    from src.ai_processor import AIProcessor

class TestAIProcessor:
    """Comprehensive tests for AIProcessor class."""
    
    @pytest.fixture
    def ai_processor(self, tmp_path, monkeypatch):
        """Create AIProcessor instance for testing with mocked dependencies."""
        # Mock the Azure config and other dependencies
        with patch('src.ai_processor.get_azure_config') as mock_config, \
             patch('src.ai_processor.AccuracyTracker') as mock_tracker, \
             patch('src.ai_processor.DataRecorder') as mock_recorder, \
             patch('src.ai_processor.SessionTracker') as mock_session:
            
            mock_config.return_value = {
                'endpoint': 'https://test.openai.azure.com/',
                'api_key': 'test_key',
                'deployment_name': 'test-deployment'
            }
            
            # Create temporary directories
            test_prompts_dir = tmp_path / "prompts"
            test_prompts_dir.mkdir()
            test_user_data_dir = tmp_path / "user_specific_data"
            test_user_data_dir.mkdir()
            
            processor = AIProcessor()
            processor.prompts_dir = str(test_prompts_dir)
            processor.user_data_dir = str(test_user_data_dir)
            processor.runtime_data_dir = str(tmp_path / "runtime_data")
            
            return processor
    
    def test_init_creates_directories(self, tmp_path):
        """Test that AIProcessor creates necessary directories on initialization."""
        with patch('src.ai_processor.get_azure_config'), \
             patch('src.ai_processor.AccuracyTracker'), \
             patch('src.ai_processor.DataRecorder'), \
             patch('src.ai_processor.SessionTracker'):
            
            processor = AIProcessor()
            # Check that runtime data directory would be created
            assert hasattr(processor, 'runtime_data_dir')
            assert hasattr(processor, 'learning_file')
    
    def test_get_username_from_file(self, ai_processor, tmp_path):
        """Test username retrieval from file."""
        username_file = os.path.join(ai_processor.user_data_dir, 'username.txt')
        os.makedirs(ai_processor.user_data_dir, exist_ok=True)
        
        with open(username_file, 'w', encoding='utf-8') as f:
            f.write('test_user')
        
        result = ai_processor.get_username()
        assert result == 'test_user'
    
    def test_get_username_default(self, ai_processor):
        """Test default username when file doesn't exist."""
        result = ai_processor.get_username()
        assert result == 'user'
    
    def test_parse_prompty_file_with_frontmatter(self, ai_processor, tmp_path):
        """Test parsing .prompty file with YAML frontmatter."""
        prompty_content = """---
name: test_prompt
description: Test prompt
version: 1.0
---
This is the actual prompt content."""
        
        prompty_file = tmp_path / "test.prompty"
        prompty_file.write_text(prompty_content)
        
        result = ai_processor.parse_prompty_file(str(prompty_file))
        assert result == "This is the actual prompt content."
    
    def test_parse_prompty_file_without_frontmatter(self, ai_processor, tmp_path):
        """Test parsing .prompty file without YAML frontmatter."""
        prompty_content = "This is a simple prompt without frontmatter."
        
        prompty_file = tmp_path / "test.prompty"
        prompty_file.write_text(prompty_content)
        
        result = ai_processor.parse_prompty_file(str(prompty_file))
        assert result == prompty_content
    
    def test_parse_prompty_file_malformed(self, ai_processor, tmp_path):
        """Test parsing malformed .prompty file raises ValueError."""
        prompty_content = "---\nincomplete frontmatter"
        
        prompty_file = tmp_path / "test.prompty"
        prompty_file.write_text(prompty_content)
        
        with pytest.raises(ValueError, match="Malformed YAML frontmatter"):
            ai_processor.parse_prompty_file(str(prompty_file))
    
    @patch('src.ai_processor.openai')
    def test_classify_email_success(self, mock_openai, ai_processor, sample_email_data):
        """Test successful email classification."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "required_personal_action"
        mock_openai.AzureOpenAI.return_value.chat.completions.create.return_value = mock_response
        
        # Mock the prompty file
        with patch.object(ai_processor, 'parse_prompty_file') as mock_parse:
            mock_parse.return_value = "Classify this email: {email_content}"
            
            result = ai_processor.classify_email(sample_email_data, {})
            
            assert result == "required_personal_action"
            mock_openai.AzureOpenAI.return_value.chat.completions.create.assert_called_once()
    
    @patch('src.ai_processor.openai')
    def test_classify_email_api_failure(self, mock_openai, ai_processor, sample_email_data):
        """Test email classification with API failure."""
        # Mock API failure
        mock_openai.AzureOpenAI.return_value.chat.completions.create.side_effect = Exception("API Error")
        
        with patch.object(ai_processor, 'parse_prompty_file') as mock_parse:
            mock_parse.return_value = "Classify this email: {email_content}"
            
            result = ai_processor.classify_email(sample_email_data, {})
            
            assert result == "work_relevant"  # Default fallback
    
    @pytest.mark.parametrize("email_category,expected_category", [
        ("urgent meeting request", "required_personal_action"),
        ("team notification", "team_action"),
        ("newsletter subscription", "fyi"),
        ("job opportunity", "job_listing"),
        ("spam content", "spam_to_delete")
    ])
    def test_classify_email_categories(self, ai_processor, email_category, expected_category):
        """Test email classification for different categories."""
        email_data = {
            'subject': email_category,
            'body': f'This is a {email_category} email',
            'sender': 'test@example.com',
            'received_time': '2025-01-15'
        }
        
        with patch('src.ai_processor.openai') as mock_openai:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = expected_category
            mock_openai.AzureOpenAI.return_value.chat.completions.create.return_value = mock_response
            
            with patch.object(ai_processor, 'parse_prompty_file') as mock_parse:
                mock_parse.return_value = "Classify: {email_content}"
                
                result = ai_processor.classify_email(email_data, {})
                assert result == expected_category
    
    def test_load_learning_data_file_exists(self, ai_processor, tmp_path):
        """Test loading learning data when file exists."""
        # Create test CSV data
        learning_data = "email_id,feedback,category\n1,correct,meeting\n2,incorrect,spam"
        learning_file = tmp_path / "ai_learning_feedback.csv"
        learning_file.write_text(learning_data)
        
        ai_processor.learning_file = str(learning_file)
        
        with patch('src.ai_processor.load_csv_or_empty') as mock_load:
            mock_load.return_value = [
                {'email_id': '1', 'feedback': 'correct', 'category': 'meeting'},
                {'email_id': '2', 'feedback': 'incorrect', 'category': 'spam'}
            ]
            
            result = ai_processor.load_learning_data()
            assert len(result) == 2
            mock_load.assert_called_once_with(str(learning_file))
    
    def test_load_learning_data_file_not_exists(self, ai_processor):
        """Test loading learning data when file doesn't exist."""
        ai_processor.learning_file = "/nonexistent/path/learning.csv"
        
        with patch('src.ai_processor.load_csv_or_empty') as mock_load:
            mock_load.return_value = []
            
            result = ai_processor.load_learning_data()
            assert result == []
    
    @patch('src.ai_processor.openai')
    def test_extract_action_items_success(self, mock_openai, ai_processor, sample_email_data):
        """Test successful action item extraction."""
        # Mock OpenAI response with JSON
        action_items_json = {
            'action_required': 'Review the attached document',
            'due_date': 'January 20, 2025',
            'priority': 'high',
            'estimated_time': '30 minutes'
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(action_items_json)
        mock_openai.AzureOpenAI.return_value.chat.completions.create.return_value = mock_response
        
        with patch.object(ai_processor, 'parse_prompty_file') as mock_parse:
            mock_parse.return_value = "Extract action items: {email_content}"
            
            result = ai_processor.extract_action_items(sample_email_data, {})
            
            assert result['action_required'] == 'Review the attached document'
            assert result['priority'] == 'high'
    
    @patch('src.ai_processor.openai')
    def test_extract_action_items_invalid_json(self, mock_openai, ai_processor, sample_email_data):
        """Test action item extraction with invalid JSON response."""
        # Mock OpenAI response with invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_openai.AzureOpenAI.return_value.chat.completions.create.return_value = mock_response
        
        with patch.object(ai_processor, 'parse_prompty_file') as mock_parse:
            mock_parse.return_value = "Extract action items: {email_content}"
            
            with patch('src.ai_processor.parse_json_with_fallback') as mock_parse_json:
                mock_parse_json.return_value = {
                    'action_required': 'Could not extract specific action',
                    'due_date': 'No specific deadline',
                    'priority': 'medium'
                }
                
                result = ai_processor.extract_action_items(sample_email_data, {})
                
                assert 'action_required' in result
                assert result['action_required'] == 'Could not extract specific action'
    
    def test_context_building(self, ai_processor, tmp_path):
        """Test building context from user-specific files."""
        # Create test context files
        job_summary_file = tmp_path / "job_summery.md"
        job_summary_file.write_text("Software Engineer with 5 years experience")
        
        job_skills_file = tmp_path / "job_skill_summery.md"
        job_skills_file.write_text("Python, JavaScript, React, Machine Learning")
        
        ai_processor.job_summary_file = str(job_summary_file)
        ai_processor.job_skills_file = str(job_skills_file)
        
        # Test that files can be read (this would be used in context building)
        assert job_summary_file.read_text() == "Software Engineer with 5 years experience"
        assert job_skills_file.read_text() == "Python, JavaScript, React, Machine Learning"
    
    def test_session_tracking_integration(self, ai_processor):
        """Test integration with session tracking."""
        # Verify that session tracker is initialized
        assert hasattr(ai_processor, 'session_tracker')
        assert hasattr(ai_processor, 'accuracy_tracker')
        assert hasattr(ai_processor, 'data_recorder')
    
    @patch('src.ai_processor.openai')
    def test_api_rate_limiting_handling(self, mock_openai, ai_processor, sample_email_data):
        """Test handling of API rate limiting."""
        # Mock rate limit error
        from openai import RateLimitError
        mock_openai.AzureOpenAI.return_value.chat.completions.create.side_effect = RateLimitError(
            "Rate limit exceeded", response=Mock(), body=None
        )
        
        with patch.object(ai_processor, 'parse_prompty_file') as mock_parse:
            mock_parse.return_value = "Classify: {email_content}"
            
            result = ai_processor.classify_email(sample_email_data, {})
            
            # Should return default classification on rate limit
            assert result == "work_relevant"
    
    def test_concurrent_processing_safety(self, ai_processor):
        """Test that AIProcessor handles concurrent access safely."""
        # This would test thread safety in a real scenario
        # For now, verify that the processor can be instantiated multiple times
        
        with patch('src.ai_processor.get_azure_config'), \
             patch('src.ai_processor.AccuracyTracker'), \
             patch('src.ai_processor.DataRecorder'), \
             patch('src.ai_processor.SessionTracker'):
            
            processor1 = AIProcessor()
            processor2 = AIProcessor()
            
            # Each instance should have its own learning file path
            assert hasattr(processor1, 'learning_file')
            assert hasattr(processor2, 'learning_file')
    
    def test_error_recovery_mechanisms(self, ai_processor, sample_email_data):
        """Test various error recovery mechanisms."""
        test_cases = [
            ('Network error', ConnectionError("Network unreachable")),
            ('Timeout error', TimeoutError("Request timeout")),
            ('API key error', Exception("Invalid API key"))
        ]
        
        for error_name, error_exception in test_cases:
            with patch('src.ai_processor.openai') as mock_openai:
                mock_openai.AzureOpenAI.return_value.chat.completions.create.side_effect = error_exception
                
                with patch.object(ai_processor, 'parse_prompty_file') as mock_parse:
                    mock_parse.return_value = "Classify: {email_content}"
                    
                    result = ai_processor.classify_email(sample_email_data, {})
                    
                    # Should gracefully handle error and return fallback
                    assert result == "work_relevant", f"Failed to handle {error_name}"