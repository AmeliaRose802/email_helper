"""
Comprehensive tests for utility modules.
Tests JSON processing, text processing, date utilities, and data utilities.
"""
import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, mock_open

# Import utility modules
from src.utils.json_utils import clean_json_response, parse_json_with_fallback
from src.utils.text_utils import clean_ai_response, clean_markdown_formatting, truncate_with_ellipsis, add_bullet_if_needed
from src.utils.date_utils import parse_date_string, format_date_for_display
from src.utils.data_utils import load_csv_or_empty
from src.utils.session_tracker import SessionTracker

class TestJSONUtils:
    """Tests for JSON utility functions."""
    
    def test_clean_json_response_valid_json(self):
        """Test cleaning valid JSON response."""
        response = '{"key": "value", "number": 123}'
        result = clean_json_response(response)
        assert result == '{"key": "value", "number": 123}'
    
    def test_clean_json_response_with_markdown(self):
        """Test cleaning JSON response with markdown formatting."""
        response = '```json\n{"key": "value"}\n```'
        result = clean_json_response(response)
        assert result == '{"key": "value"}'
    
    def test_clean_json_response_with_extra_text(self):
        """Test cleaning JSON response with extra text."""
        response = 'Here is the JSON: {"key": "value"} and some other text'
        result = clean_json_response(response)
        # This function only removes markdown, not extra text
        assert '{"key": "value"}' in result
    
    def test_clean_json_response_invalid_json(self):
        """Test handling of invalid JSON."""
        response = '{"key": invalid json}'
        result = clean_json_response(response)
        # Function just cleans, doesn't validate
        assert result == '{"key": invalid json}'
    
    def test_parse_json_with_fallback_valid(self):
        """Test JSON parsing with valid input."""
        json_string = '{"action": "review", "priority": "high"}'
        fallback = {"action": "unknown", "priority": "low"}
        
        result = parse_json_with_fallback(json_string, fallback)
        assert result == {"action": "review", "priority": "high"}
    
    def test_parse_json_with_fallback_invalid(self):
        """Test JSON parsing with invalid input returns fallback."""
        json_string = 'invalid json string'
        fallback = {"action": "unknown", "priority": "low"}
        
        result = parse_json_with_fallback(json_string, fallback)
        assert result == fallback
    
    def test_parse_json_with_fallback_empty(self):
        """Test JSON parsing with empty input."""
        json_string = ''
        fallback = {"default": "value"}
        
        result = parse_json_with_fallback(json_string, fallback)
        assert result == fallback

class TestTextUtils:
    """Tests for text utility functions."""
    
    def test_clean_ai_response_basic(self):
        """Test basic AI response cleaning."""
        response = "  Here is my response with extra spaces.  \n"
        result = clean_ai_response(response)
        assert result == "Here is my response with extra spaces."
    
    def test_clean_ai_response_with_artifacts(self):
        """Test cleaning AI response with common artifacts."""
        response = "```\nSome response\n```\n\n**Bold text**"
        result = clean_ai_response(response)
        # Should remove asterisks but not code blocks
        assert "Some response" in result
        assert "**" not in result
        assert "*" not in result
    
    def test_clean_markdown_formatting(self):
        """Test markdown formatting removal."""
        text = "# Header\n\n**Bold** and *italic* text with `code`"
        result = clean_markdown_formatting(text)
        
        # This function has limited markdown removal
        assert "Bold" in result
        assert "italic" in result
        assert "Header" in result
        # The function only removes some markdown, not all
    
    def test_truncate_with_ellipsis_short_text(self):
        """Test truncation with text shorter than limit."""
        text = "Short text"
        result = truncate_with_ellipsis(text, 50)
        assert result == text
    
    def test_truncate_with_ellipsis_long_text(self):
        """Test truncation with text longer than limit."""
        text = "This is a very long text that should be truncated"
        result = truncate_with_ellipsis(text, 20)
        assert len(result) <= 23  # 20 + "..."
        assert result.endswith("...")
        assert text[:17] in result  # Some of the original text should remain
    
    def test_truncate_with_ellipsis_exact_limit(self):
        """Test truncation with text exactly at limit."""
        text = "Exactly twenty chars"
        result = truncate_with_ellipsis(text, 20)
        assert result == text
    
    def test_add_bullet_if_needed_no_bullet(self):
        """Test adding bullet to text without bullet."""
        text = "This text needs a bullet"
        result = add_bullet_if_needed(text)
        assert result.startswith("• ")
        assert "This text needs a bullet" in result
    
    def test_add_bullet_if_needed_has_bullet(self):
        """Test text that already has bullet."""
        text = "• This text already has a bullet"
        result = add_bullet_if_needed(text)
        assert result == text
    
    def test_add_bullet_if_needed_dash_bullet(self):
        """Test text with dash bullet."""
        text = "- This text has a dash bullet"
        result = add_bullet_if_needed(text)
        # Function only checks for '•', not '-'
        assert result.startswith("• ")
    
    def test_add_bullet_if_needed_empty_text(self):
        """Test adding bullet to empty text."""
        text = ""
        result = add_bullet_if_needed(text)
        assert result == "• "

class TestDateUtils:
    """Tests for date utility functions."""
    
    def test_parse_date_string_iso_format(self):
        """Test parsing ISO format date string."""
        date_string = "2025-01-15T10:30:00"
        result = parse_date_string(date_string)
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15
    
    def test_parse_date_string_simple_format(self):
        """Test parsing simple date format."""
        date_string = "2025-01-15"
        result = parse_date_string(date_string)
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15
    
    def test_parse_date_string_invalid(self):
        """Test parsing invalid date string."""
        date_string = "invalid date"
        result = parse_date_string(date_string)
        assert isinstance(result, datetime)
        # Should return current time or default
    
    def test_format_date_for_display_datetime(self):
        """Test formatting datetime for display."""
        test_date = datetime(2025, 1, 15, 14, 30, 0)
        result = format_date_for_display(test_date)
        assert "2025" in result
        assert "Jan" in result or "January" in result or "01" in result
        assert "15" in result
    
    def test_format_date_for_display_string(self):
        """Test formatting date string for display."""
        date_string = "2025-01-15"
        result = format_date_for_display(date_string)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_format_date_for_display_none(self):
        """Test formatting None date."""
        result = format_date_for_display(None)
        assert result == "No date"

class TestDataUtils:
    """Tests for data utility functions."""
    
    def test_load_csv_or_empty_existing_file(self, tmp_path):
        """Test loading existing CSV file."""
        # Create test CSV file
        csv_file = tmp_path / "test.csv"
        csv_content = "name,age,city\nJohn,30,New York\nJane,25,Boston"
        csv_file.write_text(csv_content)
        
        result = load_csv_or_empty(str(csv_file))
        assert len(result) == 2
        assert result[0]['name'] == 'John'
        assert result[0]['age'] == '30'
        assert result[1]['name'] == 'Jane'
    
    def test_load_csv_or_empty_nonexistent_file(self):
        """Test loading non-existent CSV file."""
        result = load_csv_or_empty("/nonexistent/file.csv")
        assert result == []
    
    def test_load_csv_or_empty_invalid_csv(self, tmp_path):
        """Test loading invalid CSV file."""
        csv_file = tmp_path / "invalid.csv"
        csv_file.write_text("invalid,csv\ncontent,with,too,many,columns")
        
        # Should handle gracefully and return empty list or partial data
        result = load_csv_or_empty(str(csv_file))
        assert isinstance(result, list)
    
    def test_load_csv_or_empty_empty_file(self, tmp_path):
        """Test loading empty CSV file."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        
        result = load_csv_or_empty(str(csv_file))
        assert result == []

class TestSessionTracker:
    """Tests for SessionTracker class."""
    
    @pytest.fixture
    def mock_accuracy_tracker(self):
        """Mock accuracy tracker for testing."""
        return Mock()
    
    @pytest.fixture
    def session_tracker(self, mock_accuracy_tracker):
        """Create SessionTracker instance for testing."""
        return SessionTracker(mock_accuracy_tracker)
    
    def test_session_tracker_init(self, session_tracker, mock_accuracy_tracker):
        """Test SessionTracker initialization."""
        assert session_tracker.accuracy_tracker == mock_accuracy_tracker
        assert hasattr(session_tracker, 'current_session')
    
    def test_session_tracker_start_session(self, session_tracker):
        """Test starting a new session."""
        session_id = session_tracker.start_session()
        assert isinstance(session_id, str)
        assert len(session_id) > 0
    
    def test_session_tracker_end_session(self, session_tracker):
        """Test ending a session."""
        session_id = session_tracker.start_session()
        result = session_tracker.end_session(session_id)
        assert result is True or result is None  # Depends on implementation
    
    def test_session_tracker_track_operation(self, session_tracker):
        """Test tracking an operation."""
        session_id = session_tracker.start_session()
        operation_data = {
            'operation': 'email_classification',
            'input': 'test email',
            'output': 'work_relevant',
            'timestamp': datetime.now()
        }
        
        # Should not raise an error
        session_tracker.track_operation(session_id, operation_data)
    
    def test_session_tracker_get_session_stats(self, session_tracker):
        """Test getting session statistics."""
        session_id = session_tracker.start_session()
        stats = session_tracker.get_session_stats(session_id)
        assert isinstance(stats, dict)

class TestUtilityIntegration:
    """Integration tests for utility functions working together."""
    
    def test_json_and_text_utils_integration(self):
        """Test JSON and text utilities working together."""
        # Simulate AI response with JSON and markdown
        ai_response = """
        Here's the analysis:
        
        ```json
        {
            "category": "**important**",
            "priority": "*high*",
            "summary": "This is a `critical` task"
        }
        ```
        """
        
        # First clean the AI response
        cleaned_response = clean_ai_response(ai_response)
        
        # Then extract and parse JSON
        json_data = clean_json_response(cleaned_response)
        
        # Verify we got valid data
        assert "category" in json_data
        assert "priority" in json_data
        assert "summary" in json_data
    
    def test_date_and_text_utils_integration(self):
        """Test date and text utilities working together."""
        # Simulate processing email with date information
        email_content = "**Deadline:** 2025-01-15T14:30:00 - Please complete by this date."
        
        # Clean markdown
        cleaned_content = clean_markdown_formatting(email_content)
        
        # Extract and format date
        date_obj = parse_date_string("2025-01-15T14:30:00")
        formatted_date = format_date_for_display(date_obj)
        
        assert "Deadline:" in cleaned_content
        assert "**" not in cleaned_content
        assert isinstance(date_obj, datetime)
        assert len(formatted_date) > 0
    
    def test_data_and_json_utils_integration(self, tmp_path):
        """Test data and JSON utilities working together."""
        # Create test data file with JSON-like content
        data_file = tmp_path / "test_data.csv"
        csv_content = "id,json_data\n1,\"{\"\"key\"\":\"\"value\"\"}\"\n2,\"{\"\"status\"\":\"\"complete\"\"}\""
        data_file.write_text(csv_content)
        
        # Load CSV data
        csv_data = load_csv_or_empty(str(data_file))
        
        # Process JSON in each row
        for row in csv_data:
            if 'json_data' in row:
                # Fix CSV escaping and parse JSON
                json_str = row['json_data'].replace('""', '"')
                parsed_json = parse_json_with_fallback(json_str, {})
                assert isinstance(parsed_json, dict)
    
    def test_error_handling_across_utilities(self):
        """Test error handling across different utility functions."""
        # Test with various invalid inputs
        invalid_inputs = [None, "", "invalid", 123, [], {}]
        
        for invalid_input in invalid_inputs:
            # Should not raise exceptions
            try:
                clean_ai_response(str(invalid_input) if invalid_input is not None else "")
                parse_json_with_fallback(str(invalid_input) if invalid_input is not None else "", {})
                format_date_for_display(invalid_input)
                
            except Exception as e:
                # If any exception is raised, it should be handled gracefully
                assert False, f"Utility function should handle invalid input gracefully: {e}"
    
    def test_performance_with_large_data(self):
        """Test utility performance with large data."""
        # Create large text content
        large_text = "This is a test sentence. " * 10000
        
        # Test text utilities with large content
        cleaned = clean_ai_response(large_text)
        truncated = truncate_with_ellipsis(large_text, 1000)
        
        assert len(cleaned) <= len(large_text)
        assert len(truncated) <= 1003  # 1000 + "..."
        
        # Test JSON utilities with large JSON
        large_json = {"data": ["item"] * 1000}
        json_string = json.dumps(large_json)
        parsed_back = parse_json_with_fallback(json_string, {})
        
        assert len(parsed_back["data"]) == 1000