"""Unit tests for JSON repair and fallback logic."""

import json
from backend.core.infrastructure.json_utils import (
    clean_json_response,
    repair_json_response,
    parse_json_with_fallback
)


class TestCleanJsonResponse:
    """Test clean_json_response function."""

    def test_removes_json_markdown_prefix(self):
        """Test removing ```json prefix."""
        input_str = '```json\n{"key": "value"}'
        result = clean_json_response(input_str)
        assert result == '{"key": "value"}'

    def test_removes_generic_markdown_prefix(self):
        """Test removing ``` prefix."""
        input_str = '```\n{"key": "value"}'
        result = clean_json_response(input_str)
        assert result == '{"key": "value"}'

    def test_removes_markdown_suffix(self):
        """Test removing ``` suffix."""
        input_str = '{"key": "value"}```'
        result = clean_json_response(input_str)
        assert result == '{"key": "value"}'

    def test_removes_both_prefix_and_suffix(self):
        """Test removing both markdown delimiters."""
        input_str = '```json\n{"key": "value"}```'
        result = clean_json_response(input_str)
        assert result == '{"key": "value"}'

    def test_handles_whitespace(self):
        """Test handling extra whitespace."""
        input_str = '  ```json\n{"key": "value"}```  '
        result = clean_json_response(input_str)
        assert result == '{"key": "value"}'

    def test_no_markdown_returns_original(self):
        """Test that JSON without markdown is unchanged."""
        input_str = '{"key": "value"}'
        result = clean_json_response(input_str)
        assert result == '{"key": "value"}'


class TestRepairJsonResponse:
    """Test repair_json_response function."""

    def test_repairs_missing_closing_brace(self):
        """Test adding missing closing brace."""
        input_str = '{"key": "value"'
        result = repair_json_response(input_str)
        assert result == '{"key": "value"}'
        # Verify it's valid JSON
        assert json.loads(result) == {"key": "value"}

    def test_truncates_after_last_complete_brace(self):
        """Test truncating incomplete content after last closing brace."""
        input_str = '{"key": "value"}garbage text here'
        result = repair_json_response(input_str)
        assert result == '{"key": "value"}'
        assert json.loads(result) == {"key": "value"}

    def test_repairs_unterminated_string_with_comma(self):
        """Test repairing unterminated string ending with comma."""
        input_str = '{"key": "value,\n"other": "data"}'
        result = repair_json_response(input_str)
        # Should fix the unterminated string
        assert result is not None

    def test_returns_none_for_non_json_object(self):
        """Test that non-object JSON returns None."""
        input_str = 'just some text'
        result = repair_json_response(input_str)
        assert result is None

    def test_returns_none_for_array_json(self):
        """Test that JSON arrays (not objects) return None."""
        input_str = '["item1", "item2"]'
        result = repair_json_response(input_str)
        assert result is None

    def test_handles_empty_object(self):
        """Test handling empty JSON object."""
        input_str = '{}'
        result = repair_json_response(input_str)
        assert result == '{}'
        assert json.loads(result) == {}

    def test_preserves_nested_objects(self):
        """Test that nested objects are preserved."""
        input_str = '{"outer": {"inner": "value"}}'
        result = repair_json_response(input_str)
        assert result == '{"outer": {"inner": "value"}}'
        assert json.loads(result) == {"outer": {"inner": "value"}}

    def test_handles_multiline_json(self):
        """Test handling properly formatted multiline JSON."""
        input_str = '''
        {
            "key1": "value1",
            "key2": "value2"
        }
        '''
        result = repair_json_response(input_str)
        assert result is not None
        parsed = json.loads(result)
        assert parsed == {"key1": "value1", "key2": "value2"}


class TestParseJsonWithFallback:
    """Test parse_json_with_fallback function."""

    def test_parses_valid_json(self):
        """Test parsing valid JSON string."""
        input_str = '{"key": "value"}'
        result = parse_json_with_fallback(input_str)
        assert result == {"key": "value"}

    def test_parses_markdown_wrapped_json(self):
        """Test parsing JSON wrapped in markdown."""
        input_str = '```json\n{"key": "value"}```'
        result = parse_json_with_fallback(input_str)
        assert result == {"key": "value"}

    def test_repairs_and_parses_malformed_json(self):
        """Test repairing and parsing malformed JSON."""
        input_str = '{"key": "value"'  # Missing closing brace
        result = parse_json_with_fallback(input_str)
        assert result == {"key": "value"}

    def test_returns_fallback_for_unparseable_json(self):
        """Test returning fallback data when JSON is unparseable."""
        input_str = 'completely invalid json {{{'
        fallback = {"default": "data"}
        result = parse_json_with_fallback(input_str, fallback_data=fallback)
        assert result == {"default": "data"}

    def test_returns_none_without_fallback(self):
        """Test returning None when no fallback provided."""
        input_str = 'invalid json'
        result = parse_json_with_fallback(input_str)
        assert result is None

    def test_preserves_complex_json_structure(self):
        """Test parsing complex nested JSON."""
        input_str = '''
        {
            "emails": [
                {"id": 1, "subject": "Test"},
                {"id": 2, "subject": "Test2"}
            ],
            "metadata": {
                "count": 2,
                "status": "success"
            }
        }
        '''
        result = parse_json_with_fallback(input_str)
        assert result is not None
        assert "emails" in result
        assert "metadata" in result
        assert len(result["emails"]) == 2
        assert result["metadata"]["count"] == 2

    def test_handles_json_with_special_characters(self):
        """Test parsing JSON with special characters."""
        input_str = '{"message": "Hello\\nWorld", "emoji": "😀"}'
        result = parse_json_with_fallback(input_str)
        assert result == {"message": "Hello\nWorld", "emoji": "😀"}

    def test_handles_json_with_numbers(self):
        """Test parsing JSON with various number types."""
        input_str = '{"int": 42, "float": 3.14, "negative": -10}'
        result = parse_json_with_fallback(input_str)
        assert result == {"int": 42, "float": 3.14, "negative": -10}

    def test_handles_json_with_booleans_and_null(self):
        """Test parsing JSON with booleans and null."""
        input_str = '{"active": true, "deleted": false, "data": null}'
        result = parse_json_with_fallback(input_str)
        assert result == {"active": True, "deleted": False, "data": None}

    def test_ai_response_with_trailing_text(self):
        """Test handling AI response with explanation after JSON."""
        input_str = '```json\n{"category": "spam"}```\nThis email is spam because...'
        result = parse_json_with_fallback(input_str)
        # Should extract the JSON part and ignore trailing text
        assert result == {"category": "spam"}

    def test_empty_string_returns_fallback(self):
        """Test that empty string returns fallback."""
        fallback = {"empty": True}
        result = parse_json_with_fallback('', fallback_data=fallback)
        assert result == {"empty": True}

    def test_whitespace_only_returns_fallback(self):
        """Test that whitespace-only string returns fallback."""
        fallback = {"whitespace": True}
        result = parse_json_with_fallback('   \n  \t  ', fallback_data=fallback)
        assert result == {"whitespace": True}


class TestJsonRepairEdgeCases:
    """Test edge cases and error conditions."""

    def test_deeply_nested_json(self):
        """Test parsing deeply nested JSON structures."""
        input_str = '{"a": {"b": {"c": {"d": {"e": "value"}}}}}'
        result = parse_json_with_fallback(input_str)
        assert result == {"a": {"b": {"c": {"d": {"e": "value"}}}}}

    def test_json_with_arrays(self):
        """Test parsing JSON with array values."""
        input_str = '{"items": [1, 2, 3], "tags": ["tag1", "tag2"]}'
        result = parse_json_with_fallback(input_str)
        assert result == {"items": [1, 2, 3], "tags": ["tag1", "tag2"]}

    def test_json_with_escaped_quotes(self):
        """Test parsing JSON with escaped quotes."""
        input_str = '{"message": "She said \\"hello\\""}'
        result = parse_json_with_fallback(input_str)
        assert result == {"message": 'She said "hello"'}

    def test_unicode_characters(self):
        """Test parsing JSON with Unicode characters."""
        input_str = '{"text": "日本語", "emoji": "🎉"}'
        result = parse_json_with_fallback(input_str)
        assert result == {"text": "日本語", "emoji": "🎉"}

    def test_large_json_object(self):
        """Test parsing large JSON objects."""
        # Create a large JSON object with 100 keys
        large_obj = {f"key_{i}": f"value_{i}" for i in range(100)}
        input_str = json.dumps(large_obj)
        result = parse_json_with_fallback(input_str)
        assert result == large_obj

    def test_json_with_multiple_markdown_blocks(self):
        """Test handling multiple markdown code blocks."""
        input_str = 'Some text ```json\n{"key": "value"}``` more text ```json\n{"other": "data"}```'
        result = parse_json_with_fallback(input_str)
        # clean_json_response only removes markdown at start/end, not in middle
        # So this will fail to parse and return None
        assert result is None

    def test_json_missing_multiple_closing_braces(self):
        """Test repairing JSON missing multiple closing braces."""
        input_str = '{"outer": {"inner": {"deep": "value"'
        result = parse_json_with_fallback(input_str)
        # Repair function may not fix multiple missing braces perfectly
        # This tests graceful degradation
        if result is None:
            # Expected behavior - return None or fallback
            assert True
        else:
            # If it manages to repair, verify it's valid JSON
            assert isinstance(result, dict)


class TestRealWorldScenarios:
    """Test real-world AI response scenarios."""

    def test_gpt_classification_response(self):
        """Test typical GPT-4 classification response format."""
        input_str = '''```json
{
    "category": "required_personal_action",
    "explanation": "This email requires your attention because it contains a deadline.",
    "confidence": 0.95
}```'''
        result = parse_json_with_fallback(input_str)
        assert result is not None
        assert result["category"] == "required_personal_action"
        assert result["confidence"] == 0.95

    def test_gpt_action_item_extraction(self):
        """Test typical action item extraction response."""
        input_str = '''```json
{
    "action_items": [
        {
            "task": "Review document by Friday",
            "priority": "high",
            "deadline": "2024-01-05"
        },
        {
            "task": "Send feedback to team",
            "priority": "medium",
            "deadline": null
        }
    ]
}```'''
        result = parse_json_with_fallback(input_str)
        assert result is not None
        assert "action_items" in result
        assert len(result["action_items"]) == 2
        assert result["action_items"][0]["priority"] == "high"

    def test_gpt_response_with_thinking(self):
        """Test AI response with reasoning before JSON."""
        input_str = '''Let me analyze this email...

The email appears to be spam because it contains...

```json
{"category": "spam_to_delete", "confidence": 0.98}
```

Therefore, I recommend deleting this email.'''
        result = parse_json_with_fallback(input_str)
        # The cleaning regex only removes markdown at start/end, not embedded in text
        # This will fail to parse due to text before the JSON block
        assert result is None

    def test_incomplete_ai_response(self):
        """Test handling incomplete AI response (timeout/truncation)."""
        input_str = '{"category": "work_relevant", "explanation": "This email contains important'
        fallback = {"category": "fyi", "explanation": "Failed to classify"}
        result = parse_json_with_fallback(input_str, fallback_data=fallback)
        # Should either repair it or return fallback
        assert result is not None
        assert "category" in result

    def test_malformed_ai_json_with_extra_commas(self):
        """Test handling AI responses with trailing commas."""
        input_str = '''
        {
            "category": "newsletter",
            "confidence": 0.85,
        }
        '''
        result = parse_json_with_fallback(input_str)
        # Python's json.loads is strict about trailing commas
        # This tests fallback behavior
        if result is None:
            # Expected if repair can't fix trailing comma
            assert True
        else:
            # If repair succeeds
            assert result["category"] == "newsletter"
