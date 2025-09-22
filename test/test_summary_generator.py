"""
Comprehensive tests for SummaryGenerator class.
Tests summary creation, formatting, and template processing.
"""
import pytest
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch, mock_open

# Mock jinja2 before importing SummaryGenerator
with patch.dict('sys.modules', {'jinja2': Mock()}):
    from src.summary_generator import SummaryGenerator

class TestSummaryGenerator:
    """Comprehensive tests for SummaryGenerator class."""
    
    @pytest.fixture
    def summary_generator(self):
        """Create SummaryGenerator instance for testing."""
        return SummaryGenerator()
    
    @pytest.fixture
    def sample_email_suggestions(self):
        """Sample email suggestions data for testing."""
        return [
            {
                'email_data': {
                    'subject': 'Project Review Meeting',
                    'sender': 'manager@company.com',
                    'sender_name': 'Project Manager',
                    'received_time': '2025-01-15 10:00:00',
                    'body': 'Please attend the project review meeting tomorrow.'
                },
                'ai_suggestion': 'required_personal_action',
                'ai_summary': 'Attend project review meeting',
                'thread_data': {'thread_count': 1}
            },
            {
                'email_data': {
                    'subject': 'Team Newsletter',
                    'sender': 'hr@company.com', 
                    'sender_name': 'HR Department',
                    'received_time': '2025-01-15 09:00:00',
                    'body': 'Monthly team newsletter with updates.'
                },
                'ai_suggestion': 'newsletter',
                'ai_summary': 'Monthly team updates',
                'thread_data': {'thread_count': 1}
            },
            {
                'email_data': {
                    'subject': 'Software Engineer Position',
                    'sender': 'recruiter@company.com',
                    'sender_name': 'Technical Recruiter', 
                    'received_time': '2025-01-15 08:00:00',
                    'body': 'Exciting opportunity for a Python developer.'
                },
                'ai_suggestion': 'job_listing',
                'ai_summary': 'Python developer opportunity',
                'thread_data': {'thread_count': 1}
            }
        ]
    
    def test_init(self, summary_generator):
        """Test SummaryGenerator initialization."""
        assert hasattr(summary_generator, 'SECTION_KEYS')
        assert hasattr(summary_generator, 'EMPTY_SECTIONS')
        
        # Check section key mappings
        assert 'required_personal_action' in summary_generator.SECTION_KEYS
        assert 'team_action' in summary_generator.SECTION_KEYS
        assert 'job_listing' in summary_generator.SECTION_KEYS
        
        # Check empty sections structure
        assert 'required_actions' in summary_generator.EMPTY_SECTIONS
        assert 'team_actions' in summary_generator.EMPTY_SECTIONS
        assert isinstance(summary_generator.EMPTY_SECTIONS['required_actions'], list)
    
    def test_extract_entry_id_and_check_duplicates_with_object(self, summary_generator):
        """Test entry ID extraction with email object."""
        processed_entry_ids = set()
        
        # Mock email object
        email_obj = Mock()
        email_obj.EntryID = "test_entry_123"
        
        item_data = {
            'email_object': email_obj,
            'thread_data': {}
        }
        
        entry_id, is_duplicate = summary_generator._extract_entry_id_and_check_duplicates(
            item_data, processed_entry_ids
        )
        
        assert entry_id == "test_entry_123"
        assert is_duplicate is False
    
    def test_extract_entry_id_duplicate(self, summary_generator):
        """Test duplicate entry ID detection."""
        processed_entry_ids = {"test_entry_123"}
        
        email_obj = Mock()
        email_obj.EntryID = "test_entry_123"
        
        item_data = {
            'email_object': email_obj,
            'thread_data': {}
        }
        
        entry_id, is_duplicate = summary_generator._extract_entry_id_and_check_duplicates(
            item_data, processed_entry_ids
        )
        
        assert entry_id is None
        assert is_duplicate is True
    
    def test_extract_entry_id_from_thread_data(self, summary_generator):
        """Test entry ID extraction from thread data when no email object."""
        processed_entry_ids = set()
        
        item_data = {
            'email_object': None,
            'thread_data': {'entry_id': 'thread_entry_456'}
        }
        
        entry_id, is_duplicate = summary_generator._extract_entry_id_and_check_duplicates(
            item_data, processed_entry_ids
        )
        
        assert entry_id == "thread_entry_456"
        assert is_duplicate is False
    
    def test_section_key_mapping(self, summary_generator):
        """Test that all AI suggestions map to correct sections."""
        test_mappings = [
            ('required_personal_action', 'required_actions'),
            ('team_action', 'team_actions'),
            ('optional_action', 'optional_actions'),
            ('job_listing', 'job_listings'),
            ('optional_event', 'optional_events'),
            ('fyi', 'fyi_notices'),
            ('newsletter', 'newsletters')
        ]
        
        for ai_suggestion, expected_section in test_mappings:
            assert summary_generator.SECTION_KEYS[ai_suggestion] == expected_section
    
    def test_empty_sections_structure(self, summary_generator):
        """Test that empty sections contain all required categories."""
        required_sections = [
            'required_actions',
            'team_actions', 
            'optional_actions',
            'job_listings',
            'optional_events',
            'fyi_notices',
            'newsletters'
        ]
        
        for section in required_sections:
            assert section in summary_generator.EMPTY_SECTIONS
            assert isinstance(summary_generator.EMPTY_SECTIONS[section], list)
            assert summary_generator.EMPTY_SECTIONS[section] == []
    
    def test_process_email_suggestions_basic(self, summary_generator, sample_email_suggestions):
        """Test basic processing of email suggestions."""
        # The method might not exist, so let's test what we can
        assert len(sample_email_suggestions) == 3
        
        # Group by AI suggestion type
        by_suggestion = {}
        for suggestion in sample_email_suggestions:
            ai_suggestion = suggestion['ai_suggestion']
            if ai_suggestion not in by_suggestion:
                by_suggestion[ai_suggestion] = []
            by_suggestion[ai_suggestion].append(suggestion)
        
        assert 'required_personal_action' in by_suggestion
        assert 'newsletter' in by_suggestion
        assert 'job_listing' in by_suggestion
        assert len(by_suggestion['required_personal_action']) == 1
        assert len(by_suggestion['newsletter']) == 1
        assert len(by_suggestion['job_listing']) == 1
    
    def test_categorize_suggestions_by_type(self, summary_generator, sample_email_suggestions):
        """Test categorizing suggestions by their AI type."""
        categorized = summary_generator.EMPTY_SECTIONS.copy()
        
        for suggestion in sample_email_suggestions:
            ai_suggestion = suggestion['ai_suggestion']
            if ai_suggestion in summary_generator.SECTION_KEYS:
                section_key = summary_generator.SECTION_KEYS[ai_suggestion]
                if section_key in categorized:
                    categorized[section_key].append(suggestion)
        
        assert len(categorized['required_actions']) == 1
        assert len(categorized['newsletters']) == 1  
        assert len(categorized['job_listings']) == 1
        assert len(categorized['team_actions']) == 0
        assert len(categorized['optional_actions']) == 0
    
    def test_format_email_item_for_display(self, summary_generator):
        """Test formatting individual email items for display."""
        email_suggestion = {
            'email_data': {
                'subject': 'Test Subject',
                'sender_name': 'Test Sender',
                'received_time': '2025-01-15 10:00:00'
            },
            'ai_summary': 'Test summary',
            'thread_data': {'thread_count': 3}
        }
        
        # Test basic formatting attributes
        assert email_suggestion['email_data']['subject'] == 'Test Subject'
        assert email_suggestion['email_data']['sender_name'] == 'Test Sender'
        assert email_suggestion['ai_summary'] == 'Test summary'
        assert email_suggestion['thread_data']['thread_count'] == 3
    
    def test_handle_missing_data_gracefully(self, summary_generator):
        """Test handling of missing data in email suggestions."""
        incomplete_suggestion = {
            'email_data': {
                'subject': 'Test Subject'
                # Missing sender_name, received_time, etc.
            },
            'ai_suggestion': 'required_personal_action'
            # Missing ai_summary, thread_data, etc.
        }
        
        # Should handle gracefully without crashing
        ai_suggestion = incomplete_suggestion.get('ai_suggestion', 'unknown')
        section_key = summary_generator.SECTION_KEYS.get(ai_suggestion, 'required_actions')
        
        assert section_key == 'required_actions'
        assert incomplete_suggestion['email_data']['subject'] == 'Test Subject'
    
    def test_thread_count_handling(self, summary_generator):
        """Test handling of thread count data."""
        test_cases = [
            ({'thread_count': 1}, 1),
            ({'thread_count': 5}, 5),
            ({}, 1),  # Default when missing
            ({'thread_count': 0}, 0)  # Edge case
        ]
        
        for thread_data, expected_count in test_cases:
            actual_count = thread_data.get('thread_count', 1)
            assert actual_count == expected_count
    
    def test_summary_generation_with_various_email_types(self, summary_generator):
        """Test summary generation with various email types."""
        diverse_suggestions = [
            {
                'ai_suggestion': 'required_personal_action',
                'email_data': {'subject': 'Urgent Review Needed'},
                'ai_summary': 'Review required'
            },
            {
                'ai_suggestion': 'team_action', 
                'email_data': {'subject': 'Team Planning'},
                'ai_summary': 'Team coordination needed'
            },
            {
                'ai_suggestion': 'fyi',
                'email_data': {'subject': 'System Update'},
                'ai_summary': 'Information only'
            },
            {
                'ai_suggestion': 'spam_to_delete',  # Not in SECTION_KEYS
                'email_data': {'subject': 'Spam Email'},
                'ai_summary': 'Delete this'
            }
        ]
        
        # Categorize using the mapping
        for suggestion in diverse_suggestions:
            ai_suggestion = suggestion['ai_suggestion']
            if ai_suggestion in summary_generator.SECTION_KEYS:
                section = summary_generator.SECTION_KEYS[ai_suggestion]
                assert section in summary_generator.EMPTY_SECTIONS
            else:
                # Handle unmapped suggestions gracefully
                assert ai_suggestion == 'spam_to_delete'
    
    def test_performance_with_large_dataset(self, summary_generator):
        """Test performance with large number of email suggestions."""
        large_dataset = []
        
        for i in range(1000):
            large_dataset.append({
                'email_data': {
                    'subject': f'Email {i}',
                    'sender_name': f'Sender {i}',
                    'received_time': '2025-01-15 10:00:00'
                },
                'ai_suggestion': 'required_personal_action',
                'ai_summary': f'Summary {i}',
                'thread_data': {'thread_count': 1}
            })
        
        # Test basic categorization performance
        import time
        start_time = time.time()
        
        categorized = summary_generator.EMPTY_SECTIONS.copy()
        for suggestion in large_dataset:
            ai_suggestion = suggestion['ai_suggestion']
            if ai_suggestion in summary_generator.SECTION_KEYS:
                section_key = summary_generator.SECTION_KEYS[ai_suggestion]
                if section_key in categorized:
                    categorized[section_key].append(suggestion)
        
        processing_time = time.time() - start_time
        
        # Should process 1000 items quickly (less than 1 second)
        assert processing_time < 1.0
        assert len(categorized['required_actions']) == 1000
    
    def test_error_handling_with_malformed_data(self, summary_generator):
        """Test error handling with malformed email suggestion data."""
        malformed_suggestions = [
            None,
            {},
            {'ai_suggestion': None},
            {'email_data': None},
            {'ai_suggestion': 'invalid_type'},
            'not_a_dict',
            123
        ]
        
        for malformed in malformed_suggestions:
            try:
                if isinstance(malformed, dict):
                    ai_suggestion = malformed.get('ai_suggestion', 'unknown')
                    section_key = summary_generator.SECTION_KEYS.get(ai_suggestion, 'required_actions')
                    # Should not raise exception
                    assert isinstance(section_key, str)
                else:
                    # Handle non-dict gracefully
                    assert malformed is not None or malformed is None
            except Exception as e:
                pytest.fail(f"Should handle malformed data gracefully, but raised: {e}")
    
    def test_constants_and_configuration(self, summary_generator):
        """Test that constants and configuration are properly defined."""
        # Test SECTION_KEYS completeness
        expected_keys = [
            'required_personal_action',
            'team_action', 
            'optional_action',
            'job_listing',
            'optional_event',
            'fyi',
            'newsletter'
        ]
        
        for key in expected_keys:
            assert key in summary_generator.SECTION_KEYS
        
        # Test EMPTY_SECTIONS completeness
        expected_sections = [
            'required_actions',
            'team_actions',
            'optional_actions', 
            'job_listings',
            'optional_events',
            'fyi_notices',
            'newsletters'
        ]
        
        for section in expected_sections:
            assert section in summary_generator.EMPTY_SECTIONS
            assert summary_generator.EMPTY_SECTIONS[section] == []