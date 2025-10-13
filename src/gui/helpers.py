#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Helper functions for GUI operations.

This module provides utility functions for:
- Text formatting and cleaning
- Date and time formatting
- URL parsing and display name generation
- Link text creation based on context
"""

import re
import webbrowser
from datetime import datetime
from urllib.parse import urlparse
from tkinter import messagebox


def clean_email_formatting(body):
    """Clean up common email formatting issues for better readability.
    
    Args:
        body (str): Raw email body text
        
    Returns:
        str: Cleaned and formatted email body
    """
    # Remove excessive blank lines
    body = re.sub(r'\n{3,}', '\n\n', body)
    
    # Clean up outlook-style forwarded/reply headers
    body = re.sub(r'_{10,}', '\n' + '─' * 40 + '\n', body)
    
    # Clean up common email signatures separators
    body = re.sub(r'-{5,}', '─' * 25, body)
    
    # Remove excessive spaces while preserving intentional formatting
    lines = body.split('\n')
    cleaned_lines = []
    for line in lines:
        # Clean up excessive spaces but preserve indentation
        cleaned_line = re.sub(r'[ \t]{2,}', ' ', line.rstrip())
        cleaned_lines.append(cleaned_line)
    
    return '\n'.join(cleaned_lines)


def create_display_url(url):
    """Create a more readable display version of the URL.
    
    Args:
        url (str): Full URL to display
        
    Returns:
        str: Shortened, more readable version of the URL
    """
    # Truncate very long URLs for better readability
    if len(url) > 60:
        # Try to show meaningful part of URL
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            path = parsed.path[:30] + '...' if len(parsed.path) > 30 else parsed.path
            return f"{domain}{path}"
        except:
            # Fallback: simple truncation
            return url[:50] + "..."
    return url


def create_descriptive_link_text(url, context='general'):
    """Create descriptive text for a URL based on context.
    
    Args:
        url (str): URL to create description for
        context (str): Context hint ('job', 'event', 'newsletter', 'general')
        
    Returns:
        str: Human-readable description of what the link does
    """
    try:
        parsed = urlparse(url.lower())
        domain = parsed.netloc
        path = parsed.path
        
        # Context-specific link descriptions
        if context == 'job':
            if 'apply' in url.lower() or 'application' in url.lower():
                return 'Apply Now'
            elif 'career' in domain or 'jobs' in domain:
                return 'Job Details'
            else:
                return 'View Job'
        
        elif context == 'event':
            if 'register' in url.lower() or 'signup' in url.lower():
                return 'Register'
            elif 'calendar' in url.lower() or 'event' in url.lower():
                return 'Event Details'
            else:
                return 'View Event'
        
        elif context == 'newsletter':
            if 'unsubscribe' in url.lower():
                return 'Unsubscribe'
            elif 'archive' in url.lower():
                return 'View Archive'
            else:
                return 'Read More'
        
        # Domain-based descriptions (check more specific patterns first)
        if 'forms.' in domain or 'survey' in url.lower():
            return 'Complete Survey'
        elif 'github.com' in domain:
            return 'View on GitHub'
        elif 'linkedin.com' in domain:
            return 'View on LinkedIn'
        elif 'teams.microsoft.com' in domain:
            return 'Join Teams Meeting'
        elif 'docs.' in domain or 'documentation' in url.lower():
            return 'View Documentation'
        elif any(word in domain for word in ['zoom', 'meet', 'webex']):
            return 'Join Meeting'
        elif 'calendar' in url.lower():
            return 'Add to Calendar'
        elif 'outlook.com' in domain or (domain.endswith('office.com') and not domain.startswith('forms.')):
            return 'View in Outlook'
        
        # Fallback to generic but still descriptive
        if len(domain) > 30:
            return f"Visit {domain[:25]}..."
        else:
            return f"Visit {domain}"
            
    except:
        return 'View Link'


def format_task_dates(item):
    """Format date(s) for task listing - single date or range for multi-email tasks.
    
    Args:
        item (dict): Task item with thread_data and date information
        
    Returns:
        str: Formatted date string (single date or range)
    """
    try:
        # Check if this is a multi-email task (thread)
        thread_data = item.get('thread_data', {})
        if thread_data and thread_data.get('thread_count', 1) > 1:
            # Multi-email task - show date range
            all_emails = thread_data.get('all_emails_data', [])
            if all_emails and len(all_emails) > 1:
                dates = []
                for email_data in all_emails:
                    email_date = email_data.get('received_time')
                    if hasattr(email_date, 'strftime'):
                        dates.append(email_date)
                
                if dates:
                    dates.sort()
                    start_date = dates[0]
                    end_date = dates[-1]
                    
                    # If same day, show single date
                    if start_date.date() == end_date.date():
                        return start_date.strftime('%b %d, %Y')
                    else:
                        # Show concise range
                        if start_date.year == end_date.year:
                            if start_date.month == end_date.month:
                                return f"{start_date.strftime('%b %d')}–{end_date.strftime('%d, %Y')}"
                            else:
                                return f"{start_date.strftime('%b %d')}–{end_date.strftime('%b %d, %Y')}"
                        else:
                            return f"{start_date.strftime('%b %d, %Y')}–{end_date.strftime('%b %d, %Y')}"
        
        # Single email task - show single date
        email_date = item.get('received_time') or item.get('email_date')
        if email_date and hasattr(email_date, 'strftime'):
            return email_date.strftime('%B %d, %Y at %I:%M %p')
        
        # Fallback to first_seen or unknown
        if item.get('first_seen'):
            try:
                first_seen = datetime.strptime(item['first_seen'], '%Y-%m-%d %H:%M:%S')
                return first_seen.strftime('%B %d, %Y')
            except:
                pass
        
        return 'Unknown date'
        
    except Exception as e:
        return 'Unknown date'


def calculate_task_age(task):
    """Calculate how many days old a task is.
    
    Args:
        task (dict): Task with 'first_seen' timestamp
        
    Returns:
        int: Number of days since task was first seen
    """
    try:
        first_seen = datetime.strptime(task.get('first_seen', ''), '%Y-%m-%d %H:%M:%S')
        return (datetime.now() - first_seen).days
    except:
        return 0


def open_url(url):
    """Open URL in default browser with error handling.
    
    Args:
        url (str): URL to open
    """
    try:
        webbrowser.open(url)
    except Exception as e:
        messagebox.showwarning("Error Opening Link", f"Could not open URL: {url}\n\nError: {str(e)}")


def find_urls_in_text(text):
    """Find all URLs in a text string.
    
    Args:
        text (str): Text to search for URLs
        
    Returns:
        list: List of dicts with 'start', 'end', 'url', and 'display_url' keys
    """
    url_pattern = r'http[s]?://[^\s<>"\'\[\](){}|\\^`]+'
    urls = []
    
    # Store URLs and their positions
    for match in re.finditer(url_pattern, text):
        urls.append({
            'start': match.start(),
            'end': match.end(),
            'url': match.group(),
            'display_url': create_display_url(match.group())
        })
    
    return urls


def truncate_text(text, max_length=50, suffix="..."):
    """Truncate text to a maximum length with ellipsis.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length before truncation
        suffix (str): Suffix to add when truncated
        
    Returns:
        str: Truncated text with suffix if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
