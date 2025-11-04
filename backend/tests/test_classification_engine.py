"""Unit tests for ClassificationEngine confidence threshold logic."""

import pytest
from unittest.mock import Mock
from backend.core.business.classification_engine import ClassificationEngine


class TestApplyConfidenceThresholds:
    """Test apply_confidence_thresholds() function."""

    @pytest.fixture
    def engine(self):
        """Create ClassificationEngine instance with mocked dependencies."""
        mock_prompt_executor = Mock()
        mock_context_manager = Mock()
        return ClassificationEngine(mock_prompt_executor, mock_context_manager)

    # Test 1: Each category at threshold boundary
    @pytest.mark.parametrize("category,threshold", [
        ('fyi', 0.9),
        ('required_personal_action', 1.0),
        ('team_action', 1.0),
        ('optional_action', 0.8),
        ('work_relevant', 0.8),
        ('newsletter', 0.7),
        ('spam_to_delete', 0.7),
        ('job_listing', 0.8),
        ('optional_event', 0.8)
    ])
    def test_category_at_exact_threshold(self, engine, category, threshold):
        """Test each category at exact threshold (should auto-approve)."""
        classification_result = {
            'category': category,
            'explanation': 'Test classification'
        }

        result = engine.apply_confidence_thresholds(
            classification_result,
            confidence_score=threshold
        )

        assert result['category'] == category
        assert result['confidence'] == threshold
        assert result['threshold'] == threshold
        assert result['auto_approve'] is True
        assert 'Auto-approved' in result['review_reason']

    # Test 2: Just above threshold
    @pytest.mark.parametrize("category,threshold", [
        ('fyi', 0.9),
        ('optional_action', 0.8),
        ('newsletter', 0.7),
        ('spam_to_delete', 0.7)
    ])
    def test_category_just_above_threshold(self, engine, category, threshold):
        """Test category just above threshold (should auto-approve)."""
        classification_result = {
            'category': category,
            'explanation': 'Test classification'
        }

        result = engine.apply_confidence_thresholds(
            classification_result,
            confidence_score=threshold + 0.01
        )

        assert result['auto_approve'] is True
        assert 'Auto-approved' in result['review_reason']

    # Test 3: Just below threshold
    @pytest.mark.parametrize("category,threshold", [
        ('fyi', 0.9),
        ('optional_action', 0.8),
        ('newsletter', 0.7),
        ('spam_to_delete', 0.7)
    ])
    def test_category_just_below_threshold(self, engine, category, threshold):
        """Test category just below threshold (should NOT auto-approve)."""
        classification_result = {
            'category': category,
            'explanation': 'Test classification'
        }

        result = engine.apply_confidence_thresholds(
            classification_result,
            confidence_score=threshold - 0.01
        )

        assert result['auto_approve'] is False
        assert 'Low confidence' in result['review_reason']

    # Test 4: High priority categories (required_personal_action, team_action)
    def test_high_priority_category_high_confidence(self, engine):
        """Test required_personal_action with 100% confidence (threshold 1.0)."""
        classification_result = {
            'category': 'required_personal_action',
            'explanation': 'Critical action required'
        }

        result = engine.apply_confidence_thresholds(
            classification_result,
            confidence_score=1.0
        )

        assert result['auto_approve'] is True
        assert result['threshold'] == 1.0
        assert 'Auto-approved' in result['review_reason']

    def test_high_priority_category_below_threshold(self, engine):
        """Test required_personal_action below 100% confidence (should not auto-approve)."""
        classification_result = {
            'category': 'required_personal_action',
            'explanation': 'Possible action required'
        }

        result = engine.apply_confidence_thresholds(
            classification_result,
            confidence_score=0.95
        )

        assert result['auto_approve'] is False
        assert result['threshold'] == 1.0
        assert 'High priority category' in result['review_reason']

    def test_team_action_below_threshold(self, engine):
        """Test team_action below 100% confidence (should not auto-approve)."""
        classification_result = {
            'category': 'team_action',
            'explanation': 'Team coordination needed'
        }

        result = engine.apply_confidence_thresholds(
            classification_result,
            confidence_score=0.9
        )

        assert result['auto_approve'] is False
        assert 'High priority category' in result['review_reason']

    # Test 5: Edge case - confidence_score=None
    def test_confidence_none_uses_estimation(self, engine):
        """Test that confidence_score=None estimates confidence from explanation length."""
        short_explanation = {
            'category': 'fyi',
            'explanation': 'Short'  # 1 word = 0.3 + 0.05 = 0.35
        }

        result = engine.apply_confidence_thresholds(short_explanation, confidence_score=None)

        # Estimation formula: min(0.8, 0.3 + len(explanation.split()) * 0.05)
        # 1 word: 0.3 + 1*0.05 = 0.35
        assert result['confidence'] == 0.35
        assert result['auto_approve'] is False  # 0.35 < 0.9 threshold for 'fyi'

    def test_confidence_none_with_long_explanation(self, engine):
        """Test confidence estimation caps at 0.8 for long explanations."""
        long_explanation = {
            'category': 'newsletter',
            'explanation': ' '.join(['word'] * 20)  # 20 words
        }

        result = engine.apply_confidence_thresholds(long_explanation, confidence_score=None)

        # Estimation: 0.3 + 20*0.05 = 1.3, but capped at 0.8
        assert result['confidence'] == 0.8
        assert result['auto_approve'] is True  # 0.8 > 0.7 threshold for 'newsletter'

    # Test 6: Multiple emails with mixed confidence
    def test_mixed_confidence_scenarios(self, engine):
        """Test batch processing with varying confidence levels."""
        emails = [
            {'category': 'spam_to_delete', 'explanation': 'Obvious spam', 'confidence': 0.95},
            {'category': 'fyi', 'explanation': 'Informational', 'confidence': 0.85},
            {'category': 'required_personal_action', 'explanation': 'Urgent action', 'confidence': 0.98},
        ]

        results = []
        for email in emails:
            result = engine.apply_confidence_thresholds(
                {'category': email['category'], 'explanation': email['explanation']},
                confidence_score=email['confidence']
            )
            results.append(result)

        # spam_to_delete: 0.95 > 0.7 → auto-approve
        assert results[0]['auto_approve'] is True

        # fyi: 0.85 < 0.9 → do NOT auto-approve
        assert results[1]['auto_approve'] is False

        # required_personal_action: 0.98 < 1.0 → do NOT auto-approve (high priority)
        assert results[2]['auto_approve'] is False
        assert 'High priority category' in results[2]['review_reason']

    # Test 7: Unknown category uses default threshold
    def test_unknown_category_uses_default_threshold(self, engine):
        """Test that unknown categories use default threshold of 0.8."""
        classification_result = {
            'category': 'unknown_category',
            'explanation': 'Unknown type'
        }

        result = engine.apply_confidence_thresholds(
            classification_result,
            confidence_score=0.85
        )

        assert result['threshold'] == 0.8  # Default threshold
        assert result['auto_approve'] is True  # 0.85 > 0.8

    # Test 8: Edge cases - extreme confidence values
    def test_zero_confidence(self, engine):
        """Test with 0% confidence."""
        classification_result = {
            'category': 'newsletter',
            'explanation': 'Test'
        }

        result = engine.apply_confidence_thresholds(
            classification_result,
            confidence_score=0.0
        )

        assert result['confidence'] == 0.0
        assert result['auto_approve'] is False

    def test_max_confidence(self, engine):
        """Test with 100% confidence."""
        classification_result = {
            'category': 'newsletter',
            'explanation': 'Definitely a newsletter'
        }

        result = engine.apply_confidence_thresholds(
            classification_result,
            confidence_score=1.0
        )

        assert result['confidence'] == 1.0
        assert result['auto_approve'] is True  # 1.0 > 0.7 threshold

    # Test 9: Result structure validation
    def test_result_contains_all_required_fields(self, engine):
        """Test that result contains all required fields."""
        classification_result = {
            'category': 'work_relevant',
            'explanation': 'Important work email'
        }

        result = engine.apply_confidence_thresholds(
            classification_result,
            confidence_score=0.85
        )

        # Check all required fields are present
        assert 'category' in result
        assert 'explanation' in result
        assert 'confidence' in result
        assert 'auto_approve' in result
        assert 'review_reason' in result
        assert 'threshold' in result

        # Check types
        assert isinstance(result['category'], str)
        assert isinstance(result['explanation'], str)
        assert isinstance(result['confidence'], float)
        assert isinstance(result['auto_approve'], bool)
        assert isinstance(result['review_reason'], str)
        assert isinstance(result['threshold'], float)

    # Test 10: Empty/missing explanation
    def test_empty_explanation(self, engine):
        """Test with empty explanation string."""
        classification_result = {
            'category': 'fyi',
            'explanation': ''
        }

        result = engine.apply_confidence_thresholds(
            classification_result,
            confidence_score=0.95
        )

        assert result['explanation'] == ''
        assert result['auto_approve'] is True  # 0.95 > 0.9

    def test_missing_explanation_uses_default(self, engine):
        """Test with missing explanation field."""
        classification_result = {
            'category': 'newsletter'
        }

        result = engine.apply_confidence_thresholds(
            classification_result,
            confidence_score=0.8
        )

        assert result['explanation'] == ''
        assert result['auto_approve'] is True  # 0.8 > 0.7
