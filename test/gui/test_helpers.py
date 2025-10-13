#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for GUI helper functions.

Non-blocking tests for all helper utilities.
"""

import pytest
from datetime import datetime, timedelta
from gui.helpers import (
    clean_email_formatting,
    create_display_url,
    create_descriptive_link_text,
    format_task_dates,
    calculate_task_age,
    find_urls_in_text,
    truncate_text
)


class TestEmailFormatting:
    """Tests for email formatting functions."""
    
    def test_clean_email_formatting_removes_excessive_newlines(self):
        """Test that excessive newlines are reduced to double newlines."""
        body = "Line 1\n\n\n\n\nLine 2"
        result = clean_email_formatting(body)
        assert result == "Line 1\n\nLine 2"
    
    def test_clean_email_formatting_replaces_underscores(self):
        """Test that long underscores are replaced with nice separators."""
        body = "Header\n______________\nContent"
        result = clean_email_formatting(body)
        assert "─" in result
        assert "_______" not in result
    
    def test_clean_email_formatting_handles_empty_string(self):
        """Test empty string handling."""
        result = clean_email_formatting("")
        assert result == ""


class TestURLHandling:
    """Tests for URL parsing and display functions."""
    
    def test_create_display_url_short_url(self):
        """Test short URLs are unchanged."""
        url = "https://example.com/short"
        result = create_display_url(url)
        assert result == url
    
    def test_create_display_url_long_url(self):
        """Test long URLs are truncated sensibly."""
        url = "https://example.com/" + "a" * 100
        result = create_display_url(url)
        assert len(result) < len(url)
        assert "example.com" in result
    
    def test_create_descriptive_link_text_job_context(self):
        """Test job-related link descriptions."""
        url = "https://careers.company.com/apply"
        result = create_descriptive_link_text(url, 'job')
        assert 'Apply' in result or 'Job' in result
    
    def test_create_descriptive_link_text_event_context(self):
        """Test event-related link descriptions."""
        url = "https://events.company.com/register"
        result = create_descriptive_link_text(url, 'event')
        assert 'Register' in result or 'Event' in result
    
    def test_create_descriptive_link_text_newsletter_unsubscribe(self):
        """Test newsletter unsubscribe links."""
        url = "https://newsletter.com/unsubscribe"
        result = create_descriptive_link_text(url, 'newsletter')
        assert result == 'Unsubscribe'
    
    def test_find_urls_in_text(self):
        """Test URL extraction from text."""
        text = "Check out https://example.com and http://test.org"
        urls = find_urls_in_text(text)
        assert len(urls) == 2
        assert urls[0]['url'] == 'https://example.com'
        assert urls[1]['url'] == 'http://test.org'
    
    def test_find_urls_in_text_no_urls(self):
        """Test text without URLs returns empty list."""
        text = "No URLs here"
        urls = find_urls_in_text(text)
        assert urls == []


class TestTextFormatting:
    """Tests for text formatting utilities."""
    
    def test_truncate_text_short(self):
        """Test short text is not truncated."""
        text = "Short text"
        result = truncate_text(text, max_length=50)
        assert result == text
    
    def test_truncate_text_long(self):
        """Test long text is truncated with ellipsis."""
        text = "A" * 100
        result = truncate_text(text, max_length=50)
        assert len(result) == 50
        assert result.endswith("...")
    
    def test_truncate_text_custom_suffix(self):
        """Test custom suffix works."""
        text = "A" * 100
        result = truncate_text(text, max_length=20, suffix=" [more]")
        assert result.endswith(" [more]")


class TestDateFormatting:
    """Tests for date formatting functions."""
    
    def test_format_task_dates_single_email(self):
        """Test formatting for single email task."""
        item = {
            'email_date': datetime(2025, 1, 15, 10, 30)
        }
        result = format_task_dates(item)
        assert 'January 15, 2025' in result
    
    def test_format_task_dates_thread_same_day(self):
        """Test formatting for thread on same day."""
        item = {
            'thread_data': {
                'thread_count': 3,
                'all_emails_data': [
                    {'received_time': datetime(2025, 1, 15, 10, 0)},
                    {'received_time': datetime(2025, 1, 15, 11, 0)},
                    {'received_time': datetime(2025, 1, 15, 12, 0)}
                ]
            }
        }
        result = format_task_dates(item)
        assert 'Jan 15, 2025' in result
    
    def test_format_task_dates_thread_date_range(self):
        """Test formatting for thread spanning multiple days."""
        item = {
            'thread_data': {
                'thread_count': 3,
                'all_emails_data': [
                    {'received_time': datetime(2025, 1, 15, 10, 0)},
                    {'received_time': datetime(2025, 1, 20, 10, 0)}
                ]
            }
        }
        result = format_task_dates(item)
        assert 'Jan' in result
        assert '15' in result
        assert '20' in result
    
    def test_calculate_task_age(self):
        """Test task age calculation."""
        # Create a task that's 5 days old
        five_days_ago = datetime.now() - timedelta(days=5)
        task = {
            'first_seen': five_days_ago.strftime('%Y-%m-%d %H:%M:%S')
        }
        age = calculate_task_age(task)
        assert age == 5
    
    def test_calculate_task_age_invalid_date(self):
        """Test task age with invalid date returns 0."""
        task = {'first_seen': 'invalid-date'}
        age = calculate_task_age(task)
        assert age == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
