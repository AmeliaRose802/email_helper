"""Unit tests for holistic inbox analysis."""

import pytest
from unittest.mock import Mock
from datetime import datetime
from backend.core.business.analysis_engine import AnalysisEngine


class TestAnalyzeInboxHolistically:
    """Test analyze_inbox_holistically function."""

    @pytest.fixture
    def engine(self):
        """Create AnalysisEngine with mocked dependencies."""
        mock_prompt_executor = Mock()
        mock_context_manager = Mock()
        mock_context_manager.get_standard_context = Mock(return_value="User context")
        mock_context_manager.get_job_role_context = Mock(return_value="Job role")
        mock_context_manager.get_username = Mock(return_value="testuser")
        return AnalysisEngine(mock_prompt_executor, mock_context_manager)

    # Test 1: Empty inbox
    def test_empty_inbox(self, engine):
        """Test analyzing empty inbox."""
        # Mock empty response
        engine.prompt_executor.execute_prompty = Mock(return_value='{"truly_relevant_actions": [], "superseded_actions": [], "duplicate_groups": [], "expired_items": []}')

        result, status = engine.analyze_inbox_holistically([])

        # Should return empty analysis structure
        assert result is not None
        assert "truly_relevant_actions" in result
        assert len(result["truly_relevant_actions"]) == 0

    # Test 2: Single category emails
    def test_single_category_inbox(self, engine):
        """Test inbox with only one category of emails."""
        emails = [
            {'subject': 'Newsletter 1', 'sender': 'news@site.com', 'body': 'News content', 'entry_id': '1'},
            {'subject': 'Newsletter 2', 'sender': 'updates@site.com', 'body': 'Update content', 'entry_id': '2'}
        ]

        # Return a non-fallback response (with at least one item to differentiate from fallback)
        ai_response = '''{
            "truly_relevant_actions": [
                {"email_id": "1", "action": "Review newsletter"}
            ],
            "superseded_actions": [],
            "duplicate_groups": [],
            "expired_items": []
        }'''

        engine.prompt_executor.execute_prompty = Mock(return_value=ai_response)

        result, status = engine.analyze_inbox_holistically(emails)

        assert result is not None
        assert status == "Holistic analysis completed successfully"
        assert "truly_relevant_actions" in result
        assert len(result["truly_relevant_actions"]) == 1

    # Test 3: Mixed priorities
    def test_mixed_priorities(self, engine):
        """Test inbox with mixed priority emails."""
        emails = [
            {'subject': 'URGENT: Action required', 'sender': 'boss@company.com', 'body': 'Critical task', 'entry_id': '1'},
            {'subject': 'FYI: Meeting notes', 'sender': 'colleague@company.com', 'body': 'Meeting summary', 'entry_id': '2'},
            {'subject': 'Optional: Team lunch', 'sender': 'team@company.com', 'body': 'Lunch invitation', 'entry_id': '3'}
        ]

        ai_response = '''{
            "truly_relevant_actions": [
                {"email_id": "1", "priority": "high", "action": "Complete critical task"}
            ],
            "superseded_actions": [],
            "duplicate_groups": [],
            "expired_items": [
                {"email_id": "3", "reason": "Past deadline"}
            ]
        }'''

        engine.prompt_executor.execute_prompty = Mock(return_value=ai_response)

        result, status = engine.analyze_inbox_holistically(emails)

        assert len(result["truly_relevant_actions"]) == 1
        assert len(result["expired_items"]) == 1
        assert result["truly_relevant_actions"][0]["priority"] == "high"

    # Test 4: Related email chains
    def test_related_email_chains(self, engine):
        """Test detection of related email threads."""
        emails = [
            {'subject': 'Project X - Initial proposal', 'sender': 'manager@company.com', 'body': 'Proposal details', 'entry_id': '1'},
            {'subject': 'Re: Project X - Feedback', 'sender': 'team@company.com', 'body': 'Feedback on proposal', 'entry_id': '2'},
            {'subject': 'Re: Project X - Final decision', 'sender': 'manager@company.com', 'body': 'Approved', 'entry_id': '3'}
        ]

        ai_response = '''{
            "truly_relevant_actions": [
                {"email_id": "3", "action": "Start Project X implementation"}
            ],
            "superseded_actions": [
                {"email_id": "1", "superseded_by": "3", "reason": "Proposal approved"}
            ],
            "duplicate_groups": [],
            "expired_items": []
        }'''

        engine.prompt_executor.execute_prompty = Mock(return_value=ai_response)

        result, status = engine.analyze_inbox_holistically(emails)

        assert len(result["truly_relevant_actions"]) == 1
        assert len(result["superseded_actions"]) == 1
        assert result["superseded_actions"][0]["superseded_by"] == "3"

    # Test 5: Performance with 100+ emails
    def test_performance_large_inbox(self, engine):
        """Test analyzing inbox with 100+ emails."""
        # Create 150 emails
        emails = []
        for i in range(150):
            emails.append({
                'subject': f'Email {i}',
                'sender': f'sender{i}@example.com',
                'body': f'Email body {i}',
                'entry_id': str(i)
            })

        ai_response = '''{
            "truly_relevant_actions": [
                {"email_id": "5", "action": "Important task"}
            ],
            "superseded_actions": [],
            "duplicate_groups": [],
            "expired_items": []
        }'''

        engine.prompt_executor.execute_prompty = Mock(return_value=ai_response)

        result, status = engine.analyze_inbox_holistically(emails)

        # Should complete successfully even with large inbox
        assert result is not None
        assert status == "Holistic analysis completed successfully"

    # Test 6: AI failure handling
    def test_ai_failure_returns_fallback(self, engine):
        """Test that AI failure returns fallback structure."""
        emails = [
            {'subject': 'Test email', 'sender': 'test@example.com', 'body': 'Test', 'entry_id': '1'}
        ]

        # Simulate AI failure
        engine.prompt_executor.execute_prompty = Mock(return_value=None)

        result, status = engine.analyze_inbox_holistically(emails)

        # analyze_inbox_holistically returns (None, status) when result is None
        assert result is None
        assert status == "Holistic analysis unavailable"

    # Test 7: Invalid AI response
    def test_invalid_ai_response_uses_fallback(self, engine):
        """Test that invalid AI response uses fallback data."""
        emails = [
            {'subject': 'Test email', 'sender': 'test@example.com', 'body': 'Test', 'entry_id': '1'}
        ]

        # Invalid JSON
        engine.prompt_executor.execute_prompty = Mock(return_value='invalid json {{')

        result, status = engine.analyze_inbox_holistically(emails)

        assert result is not None
        assert "truly_relevant_actions" in result
        assert status == "Analysis completed with parsing issues"

    # Test 8: Duplicate groups detected
    def test_duplicate_groups_detection(self, engine):
        """Test detection of duplicate email groups."""
        emails = [
            {'subject': 'Submit report by Friday', 'sender': 'manager@company.com', 'body': 'Report due', 'entry_id': '1'},
            {'subject': 'Reminder: Report deadline', 'sender': 'hr@company.com', 'body': 'Don\'t forget report', 'entry_id': '2'},
            {'subject': 'Final reminder: Report', 'sender': 'manager@company.com', 'body': 'Last chance', 'entry_id': '3'}
        ]

        ai_response = '''{
            "truly_relevant_actions": [
                {"email_id": "3", "action": "Submit report", "deadline": "Friday"}
            ],
            "superseded_actions": [],
            "duplicate_groups": [
                {"primary_email": "3", "duplicates": ["1", "2"], "reason": "Same report deadline"}
            ],
            "expired_items": []
        }'''

        engine.prompt_executor.execute_prompty = Mock(return_value=ai_response)

        result, status = engine.analyze_inbox_holistically(emails)

        assert len(result["duplicate_groups"]) == 1
        assert result["duplicate_groups"][0]["primary_email"] == "3"
        assert len(result["duplicate_groups"][0]["duplicates"]) == 2


class TestBuildInboxContextSummary:
    """Test _build_inbox_context_summary function."""

    @pytest.fixture
    def engine(self):
        """Create AnalysisEngine with mocked dependencies."""
        mock_prompt_executor = Mock()
        mock_context_manager = Mock()
        return AnalysisEngine(mock_prompt_executor, mock_context_manager)

    def test_empty_inbox_summary(self, engine):
        """Test summary for empty inbox."""
        summary = engine._build_inbox_context_summary([])
        assert summary == ""

    def test_single_email_summary(self, engine):
        """Test summary for single email."""
        emails = [
            {
                'entry_id': '123',
                'subject': 'Test Email',
                'sender_name': 'John Doe',
                'received_time': '2024-01-15',
                'body': 'This is a test email body.'
            }
        ]

        summary = engine._build_inbox_context_summary(emails)

        assert 'EMAIL_ID: 123' in summary
        assert 'Subject: Test Email' in summary
        assert 'From: John Doe' in summary
        assert 'This is a test email body.' in summary

    def test_multiple_emails_summary(self, engine):
        """Test summary for multiple emails."""
        emails = [
            {'entry_id': '1', 'subject': 'Email 1', 'sender_name': 'Sender 1', 'received_time': '2024-01-15', 'body': 'Body 1'},
            {'entry_id': '2', 'subject': 'Email 2', 'sender_name': 'Sender 2', 'received_time': '2024-01-16', 'body': 'Body 2'}
        ]

        summary = engine._build_inbox_context_summary(emails)

        # Check separator
        assert '---' in summary

        # Check both emails present
        assert 'EMAIL_ID: 1' in summary
        assert 'EMAIL_ID: 2' in summary
        assert 'Subject: Email 1' in summary
        assert 'Subject: Email 2' in summary

    def test_long_body_truncation(self, engine):
        """Test that long email bodies are truncated."""
        long_body = 'A' * 500  # 500 characters
        emails = [
            {'entry_id': '1', 'subject': 'Test', 'sender_name': 'Sender', 'received_time': '2024-01-15', 'body': long_body}
        ]

        summary = engine._build_inbox_context_summary(emails)

        # Should truncate at 300 chars and add ellipsis
        assert '...' in summary
        assert len(summary) < len(long_body) + 200  # Much shorter than original

    def test_missing_fields_handled(self, engine):
        """Test handling of missing email fields."""
        emails = [
            {'entry_id': '1'}  # Missing most fields
        ]

        summary = engine._build_inbox_context_summary(emails)

        # Should use defaults
        assert 'Unknown Subject' in summary or 'EMAIL_ID: 1' in summary

    def test_sender_fallback(self, engine):
        """Test fallback from sender_name to sender."""
        emails = [
            {'entry_id': '1', 'subject': 'Test', 'sender': 'test@example.com', 'received_time': '2024-01-15', 'body': 'Test'}
        ]

        summary = engine._build_inbox_context_summary(emails)

        # Should use 'sender' field when 'sender_name' is missing
        assert 'test@example.com' in summary

    def test_datetime_formatting(self, engine):
        """Test formatting of datetime objects."""
        emails = [
            {
                'entry_id': '1',
                'subject': 'Test',
                'sender_name': 'Sender',
                'received_time': datetime(2024, 1, 15, 10, 30),
                'body': 'Test'
            }
        ]

        summary = engine._build_inbox_context_summary(emails)

        # Should format the datetime
        assert 'EMAIL_ID: 1' in summary
        # Date should be present in some format
        assert '2024' in summary or 'Jan' in summary or '15' in summary
