"""JSON Processing Utilities for Email Helper.

This module provides robust JSON parsing, cleaning, and repair utilities
designed to handle AI-generated JSON responses and other potentially
malformed JSON data throughout the email helper application.

Key Functions:
- clean_json_response: Removes markdown formatting from JSON strings
- repair_json_response: Attempts to fix common JSON parsing errors
- parse_json_with_fallback: Comprehensive JSON parsing with error recovery

These utilities are critical for:
- Processing AI responses that may contain markdown formatting
- Handling malformed JSON from external sources
- Providing graceful fallback behavior when JSON parsing fails
- Ensuring robust data processing in production environments

The repair functions implement intelligent error recovery strategies
to maximize successful JSON parsing while maintaining data integrity.
"""

import json
import re
from typing import Any, Dict, Optional


def clean_json_response(json_str: str) -> str:
    """Clean JSON response from AI by removing markdown markers"""
    return re.sub(r'^```json\n?|^```\n?|```$', '', json_str.strip()).strip()


def repair_json_response(json_str: str) -> Optional[str]:
    """Attempt to repair common JSON parsing issues"""
    # Remove any trailing incomplete content after last complete structure
    json_str = json_str.strip()

    # Find the last complete closing brace
    last_brace = json_str.rfind('}')
    if last_brace > 0:
        json_str = json_str[:last_brace + 1]

    # Try to fix unterminated strings by adding closing quotes
    lines = json_str.split('\n')
    repaired_lines = []

    for line in lines:
        # Check if line has unmatched quotes
        quote_count = line.count('"')
        # Skip lines that are comments or contain escaped quotes
        if '//' not in line and '\\' not in line and quote_count % 2 == 1:
            # Find the last quote and see if it needs closing
            if line.rstrip().endswith(',') and line.count(':') > 0:
                # Likely a value that needs closing quote before comma
                line = line.rstrip(',') + '",'
            elif line.rstrip() and not line.rstrip().endswith('"'):
                # Add closing quote at end
                line = line.rstrip() + '"'

        repaired_lines.append(line)

    repaired_json = '\n'.join(repaired_lines)

    # Ensure proper JSON structure
    if not repaired_json.strip().startswith('{'):
        return None
    if not repaired_json.strip().endswith('}'):
        repaired_json = repaired_json.rstrip() + '}'

    return repaired_json


def parse_json_with_fallback(json_str: str, fallback_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Parse JSON string with repair attempt and fallback"""
    cleaned = clean_json_response(json_str)

    try:
        return json.loads(cleaned)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        # Try repair
        repaired = repair_json_response(cleaned)
        if repaired:
            try:
                return json.loads(repaired)  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                pass

        # Return fallback if provided
        return fallback_data
