"""Date and Time Processing Utilities for Email Helper.

This module provides comprehensive date and time processing functions
for parsing, formatting, and manipulating temporal data throughout
the email helper application. It handles various date formats and
provides consistent timestamp generation.

Key Functions:
- parse_date_string: Parses various date string formats
- format_datetime_for_storage: Formats datetime for CSV/database storage
- format_date_for_display: Formats datetime for user-friendly display
- get_timestamp: Generates current timestamp strings
- get_run_id: Creates unique run identifier timestamps

These utilities handle:
- Multiple date format parsing with fallback strategies
- Consistent datetime formatting across storage systems
- User-friendly date display formatting
- Unique identifier generation for processing runs
- Cross-platform date handling compatibility

All functions are designed to handle edge cases and provide
graceful fallback behavior for invalid or missing date information.
"""

from datetime import datetime


def format_datetime_for_storage(dt):
    """Format datetime object for CSV storage"""
    if hasattr(dt, 'strftime'):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)


def format_date_for_display(dt):
    """Format datetime for display"""
    if hasattr(dt, 'strftime'):
        return dt.strftime('%Y-%m-%d %H:%M')
    return str(dt)


def parse_date_string(date_str):
    """Parse various date string formats"""
    if not date_str or date_str == "No specific deadline":
        return None
        
    # Common date formats
    date_formats = [
        '%Y-%m-%d',
        '%m/%d/%Y', 
        '%d/%m/%Y',
        '%B %d, %Y',
        '%b %d, %Y',
        '%Y-%m-%d %H:%M',
        '%m/%d/%Y %H:%M'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # If no format matches, return None
    return None


def get_timestamp():
    """Get current timestamp string"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_run_id():
    """Generate a run ID timestamp"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
