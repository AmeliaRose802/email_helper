"""Text Processing Utilities for Email Helper.

This module provides comprehensive text cleaning, formatting, and processing
utilities used throughout the email helper application. These functions
handle various text transformation needs for AI processing, display formatting,
and content normalization.

Key Functions:
- clean_markdown_formatting: Removes markdown syntax from text
- clean_ai_response: Cleans AI-generated responses
- truncate_with_ellipsis: Safely truncates text with ellipsis
- add_bullet_if_needed: Ensures consistent bullet point formatting

These utilities are essential for:
- Preparing text for AI processing
- Formatting content for display in GUI components
- Normalizing text from various sources
- Ensuring consistent text presentation across the application

All functions are designed to handle edge cases gracefully and maintain
text integrity while applying necessary transformations.
"""

import re


def clean_markdown_formatting(text: str) -> str:
    """Remove markdown formatting from text"""
    return re.sub(r'^#+\s*|^\*+\s*|^-\s*|\*\*(.*?)\*\*|\*(.*?)\*', r'\1\2', text)


def clean_ai_response(text: str) -> str:
    """Clean AI response by removing markdown asterisks"""
    return text.strip().replace('**', '').replace('*', '')


def truncate_with_ellipsis(text: str, max_length: int) -> str:
    """Truncate text with ellipsis if too long"""
    return text[:max_length] + "..." if len(text) > max_length else text


def add_bullet_if_needed(text: str) -> str:
    """Add bullet point if text doesn't start with one"""
    return f"• {text}" if not text.startswith('•') else text
