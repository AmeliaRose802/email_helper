"""Text cleaning and formatting utilities"""

import re


def clean_markdown_formatting(text):
    """Remove markdown formatting from text"""
    return re.sub(r'^#+\s*|^\*+\s*|^-\s*|\*\*(.*?)\*\*|\*(.*?)\*', r'\1\2', text)


def clean_ai_response(text):
    """Clean AI response by removing markdown asterisks"""
    return text.strip().replace('**', '').replace('*', '')


def truncate_with_ellipsis(text, max_length):
    """Truncate text with ellipsis if too long"""
    return text[:max_length] + "..." if len(text) > max_length else text


def add_bullet_if_needed(text):
    """Add bullet point if text doesn't start with one"""
    return f"• {text}" if not text.startswith('•') else text
