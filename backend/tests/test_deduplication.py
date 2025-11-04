"""Unit tests for action item deduplication algorithm."""

import pytest
from unittest.mock import Mock
from backend.core.business.analysis_engine import AnalysisEngine


class TestAdvancedDeduplicateActionItems:
    """Test advanced_deduplicate_action_items function."""

    @pytest.fixture
    def engine(self):
        """Create AnalysisEngine with mocked dependencies."""
        mock_prompt_executor = Mock()
        mock_context_manager = Mock()
        return AnalysisEngine(mock_prompt_executor, mock_context_manager)

    # Test 1: Empty list returns empty
    def test_empty_list_returns_empty(self, engine):
        """Test that empty action items list returns empty."""
        result = engine.advanced_deduplicate_action_items([])
        assert result == []

    # Test 2: Single item returns unchanged
    def test_single_item_returns_unchanged(self, engine):
        """Test that single action item returns unchanged."""
        items = [{'action_required': 'Review document', 'subject': 'Test'}]
        result = engine.advanced_deduplicate_action_items(items)
        assert result == items

    # Test 3: No duplicates found - AI returns empty duplicates
    def test_no_duplicates_found(self, engine):
        """Test when AI finds no duplicates."""
        items = [
            {'action_required': 'Task A', 'subject': 'Email 1'},
            {'action_required': 'Task B', 'subject': 'Email 2'}
        ]

        engine.prompt_executor.execute_prompty = Mock(return_value='{"duplicates_found": []}')

        result = engine.advanced_deduplicate_action_items(items)
        assert len(result) == 2

    # Test 4: Exact duplicates detected
    def test_exact_duplicates(self, engine):
        """Test deduplication of exact duplicate tasks."""
        items = [
            {'action_required': 'Review Q4 report', 'subject': 'Email 1', 'sender': 'boss@company.com', '_entry_id': '1'},
            {'action_required': 'Review Q4 report', 'subject': 'Email 2', 'sender': 'boss@company.com', '_entry_id': '2'}
        ]

        ai_response = '''{
            "duplicates_found": [{
                "primary_item_id": "item_1",
                "duplicate_item_ids": ["item_2"],
                "merged_action": "Review Q4 report",
                "reason": "Exact duplicate task",
                "confidence": 1.0
            }]
        }'''

        engine.prompt_executor.execute_prompty = Mock(return_value=ai_response)

        result = engine.advanced_deduplicate_action_items(items)
        assert len(result) == 1
        assert 'AI merged 1 related reminder' in result[0]['explanation']
        assert len(result[0]['contributing_emails']) == 1

    # Test 5: Semantic duplicates (different wording, same task)
    def test_semantic_duplicates(self, engine):
        """Test deduplication of semantically similar tasks."""
        items = [
            {'action_required': 'Submit expense report by Friday', 'subject': 'Reminder 1', 'sender': 'hr@company.com', '_entry_id': '1'},
            {'action_required': 'Please turn in your expenses before end of week', 'subject': 'Reminder 2', 'sender': 'finance@company.com', '_entry_id': '2'},
            {'action_required': 'Expense report due EOW', 'subject': 'Reminder 3', 'sender': 'manager@company.com', '_entry_id': '3'}
        ]

        ai_response = '''{
            "duplicates_found": [{
                "primary_item_id": "item_1",
                "duplicate_item_ids": ["item_2", "item_3"],
                "merged_action": "Submit expense report by end of week",
                "reason": "Same task expressed differently",
                "confidence": 0.9
            }]
        }'''

        engine.prompt_executor.execute_prompty = Mock(return_value=ai_response)

        result = engine.advanced_deduplicate_action_items(items)
        assert len(result) == 1
        assert result[0]['action_required'] == "Submit expense report by end of week"
        assert len(result[0]['contributing_emails']) == 2

    # Test 6: False positives - similar but different tasks should NOT be merged
    def test_false_positives_not_merged(self, engine):
        """Test that similar but different tasks are not incorrectly merged."""
        items = [
            {'action_required': 'Review Q1 budget', 'subject': 'Budget Review', '_entry_id': '1'},
            {'action_required': 'Review Q2 budget', 'subject': 'Budget Review', '_entry_id': '2'}
        ]

        # AI correctly identifies these as different
        ai_response = '{"duplicates_found": []}'

        engine.prompt_executor.execute_prompty = Mock(return_value=ai_response)

        result = engine.advanced_deduplicate_action_items(items)
        assert len(result) == 2  # Both items preserved

    # Test 7: Multiple duplicate groups
    def test_multiple_duplicate_groups(self, engine):
        """Test handling multiple separate groups of duplicates."""
        items = [
            {'action_required': 'Review document A', 'subject': 'Doc A', '_entry_id': '1'},
            {'action_required': 'Please review document A', 'subject': 'Doc A reminder', '_entry_id': '2'},
            {'action_required': 'Attend meeting B', 'subject': 'Meeting B', '_entry_id': '3'},
            {'action_required': 'Don\'t forget meeting B', 'subject': 'Meeting B reminder', '_entry_id': '4'},
            {'action_required': 'Unique task C', 'subject': 'Task C', '_entry_id': '5'}
        ]

        ai_response = '''{
            "duplicates_found": [
                {
                    "primary_item_id": "item_1",
                    "duplicate_item_ids": ["item_2"],
                    "merged_action": "Review document A",
                    "reason": "Same document review",
                    "confidence": 0.95
                },
                {
                    "primary_item_id": "item_3",
                    "duplicate_item_ids": ["item_4"],
                    "merged_action": "Attend meeting B",
                    "reason": "Same meeting reminder",
                    "confidence": 0.95
                }
            ]
        }'''

        engine.prompt_executor.execute_prompty = Mock(return_value=ai_response)

        result = engine.advanced_deduplicate_action_items(items)
        assert len(result) == 3  # 2 merged groups + 1 unique = 3 items

    # Test 8: Deadline merging - earliest deadline preserved
    def test_earliest_deadline_preserved(self, engine):
        """Test that earliest deadline is preserved when merging."""
        items = [
            {'action_required': 'Submit report', 'subject': 'Report 1', 'due_date': '2024-01-15', '_entry_id': '1'},
            {'action_required': 'Submit report', 'subject': 'Report 2', 'due_date': '2024-01-10', '_entry_id': '2'},
            {'action_required': 'Submit report', 'subject': 'Report 3', 'due_date': '2024-01-20', '_entry_id': '3'}
        ]

        ai_response = '''{
            "duplicates_found": [{
                "primary_item_id": "item_1",
                "duplicate_item_ids": ["item_2", "item_3"],
                "merged_action": "Submit report",
                "merged_due_date": "earliest_deadline_from_group",
                "reason": "Same report submission",
                "confidence": 1.0
            }]
        }'''

        engine.prompt_executor.execute_prompty = Mock(return_value=ai_response)

        result = engine.advanced_deduplicate_action_items(items)
        assert len(result) == 1
        assert result[0]['due_date'] == '2024-01-10'  # Earliest deadline

    # Test 9: AI error handling - returns original items on failure
    def test_ai_failure_returns_original(self, engine):
        """Test that AI failure returns original items unchanged."""
        items = [
            {'action_required': 'Task A', 'subject': 'Email 1'},
            {'action_required': 'Task B', 'subject': 'Email 2'}
        ]

        # Simulate AI failure
        engine.prompt_executor.execute_prompty = Mock(return_value=None)

        result = engine.advanced_deduplicate_action_items(items)
        assert result == items

    # Test 10: Invalid AI response format - returns original items
    def test_invalid_ai_response_returns_original(self, engine):
        """Test that invalid AI response returns original items."""
        items = [
            {'action_required': 'Task A', 'subject': 'Email 1'},
            {'action_required': 'Task B', 'subject': 'Email 2'}
        ]

        # Invalid JSON response
        engine.prompt_executor.execute_prompty = Mock(return_value='invalid json {{')

        result = engine.advanced_deduplicate_action_items(items)
        assert result == items

    # Test 11: Performance test - 50+ items
    def test_performance_many_items(self, engine):
        """Test deduplication with 50+ items."""
        # Create 60 items (20 groups of 3 duplicates each)
        items = []
        for group in range(20):
            for i in range(3):
                items.append({
                    'action_required': f'Task group {group}',
                    'subject': f'Email {group}_{i}',
                    '_entry_id': f'{group}_{i}'
                })

        # AI finds all duplicate groups
        duplicates = []
        for group in range(20):
            base_idx = group * 3 + 1
            duplicates.append({
                "primary_item_id": f"item_{base_idx}",
                "duplicate_item_ids": [f"item_{base_idx+1}", f"item_{base_idx+2}"],
                "merged_action": f"Task group {group}",
                "reason": "Duplicate task group",
                "confidence": 0.9
            })

        ai_response = f'{{"duplicates_found": {duplicates}}}'.replace("'", '"')
        engine.prompt_executor.execute_prompty = Mock(return_value=ai_response)

        result = engine.advanced_deduplicate_action_items(items)
        assert len(result) == 20  # 60 items → 20 merged items


class TestApplyDeduplicationResults:
    """Test _apply_deduplication_results function."""

    @pytest.fixture
    def engine(self):
        """Create AnalysisEngine with mocked dependencies."""
        mock_prompt_executor = Mock()
        mock_context_manager = Mock()
        return AnalysisEngine(mock_prompt_executor, mock_context_manager)

    def test_contributing_emails_tracked(self, engine):
        """Test that contributing emails are tracked."""
        items = [
            {'subject': 'Email 1', 'sender': 'user1@example.com', '_entry_id': '1', 'action_required': 'Task'},
            {'subject': 'Email 2', 'sender': 'user2@example.com', '_entry_id': '2', 'action_required': 'Task'}
        ]

        dedup_result = {
            'duplicates_found': [{
                'primary_item_id': 'item_1',
                'duplicate_item_ids': ['item_2'],
                'merged_action': 'Task',
                'reason': 'Same task',
                'confidence': 0.9
            }]
        }

        result = engine._apply_deduplication_results(items, dedup_result)

        assert 'contributing_emails' in result[0]
        assert len(result[0]['contributing_emails']) == 1
        assert result[0]['contributing_emails'][0]['subject'] == 'Email 2'
        assert result[0]['contributing_emails'][0]['merge_reason'] == 'Same task'

    def test_invalid_indices_skipped(self, engine):
        """Test that invalid item indices are skipped."""
        items = [
            {'action_required': 'Task A', '_entry_id': '1'},
            {'action_required': 'Task B', '_entry_id': '2'}
        ]

        dedup_result = {
            'duplicates_found': [{
                'primary_item_id': 'item_99',  # Invalid index
                'duplicate_item_ids': ['item_2'],
                'merged_action': 'Task'
            }]
        }

        result = engine._apply_deduplication_results(items, dedup_result)
        assert len(result) == 2  # All items preserved

    def test_exception_returns_original(self, engine):
        """Test that exceptions return original items."""
        items = [{'action_required': 'Task', '_entry_id': '1'}]

        # Malformed dedup result
        dedup_result = {'duplicates_found': 'not a list'}

        result = engine._apply_deduplication_results(items, dedup_result)
        assert result == items
