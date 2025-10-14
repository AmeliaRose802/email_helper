"""Unit tests for AIProcessorAdapter.

This test module verifies that the AIProcessorAdapter correctly wraps
AIProcessor functionality and implements the AIProvider interface.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adapters.ai_processor_adapter import AIProcessorAdapter
from core.interfaces import AIProvider


class TestAIProcessorAdapter(unittest.TestCase):
    """Test cases for AIProcessorAdapter."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock AIProcessor
        self.mock_ai_processor = Mock()
        self.mock_ai_processor.CONFIDENCE_THRESHOLDS = {
            'fyi': 0.9,
            'required_personal_action': 1.0,
            'team_action': 1.0,
            'optional_action': 0.8,
            'work_relevant': 0.8,
            'newsletter': 0.7,
            'spam_to_delete': 0.7,
            'job_listing': 0.8,
            'optional_event': 0.8
        }
        
        # Create adapter with mocked processor
        self.adapter = AIProcessorAdapter(ai_processor=self.mock_ai_processor)
    
    def test_implements_ai_provider_interface(self):
        """Test that adapter implements AIProvider interface."""
        self.assertIsInstance(self.adapter, AIProvider)
        
        # Check required methods exist
        self.assertTrue(hasattr(self.adapter, 'classify_email'))
        self.assertTrue(hasattr(self.adapter, 'analyze_batch'))
    
    def test_classify_email_success(self):
        """Test successful email classification."""
        # Mock classification result
        self.mock_ai_processor.classify_email_with_explanation = Mock(
            return_value={
                'category': 'required_personal_action',
                'confidence': 0.95,
                'explanation': 'Email requires your immediate attention',
                'alternatives': [
                    {'category': 'work_relevant', 'confidence': 0.85}
                ]
            }
        )
        
        result = self.adapter.classify_email(
            "Subject: Urgent Task\n\nPlease complete this by EOD"
        )
        
        self.assertEqual(result['category'], 'required_personal_action')
        self.assertEqual(result['confidence'], 0.95)
        self.assertIn('reasoning', result)
        self.assertIn('alternatives', result)
        self.assertIn('requires_review', result)
    
    def test_classify_email_requires_review_low_confidence(self):
        """Test that low confidence requires review."""
        self.mock_ai_processor.classify_email_with_explanation = Mock(
            return_value={
                'category': 'optional_action',
                'confidence': 0.6,  # Below 0.8 threshold
                'explanation': 'Uncertain classification',
                'alternatives': []
            }
        )
        
        result = self.adapter.classify_email("Test email")
        
        self.assertTrue(result['requires_review'])
    
    def test_classify_email_no_review_high_confidence(self):
        """Test that high confidence doesn't require review."""
        self.mock_ai_processor.classify_email_with_explanation = Mock(
            return_value={
                'category': 'newsletter',
                'confidence': 0.95,  # Above 0.7 threshold
                'explanation': 'Clearly a newsletter',
                'alternatives': []
            }
        )
        
        result = self.adapter.classify_email("Test email")
        
        self.assertFalse(result['requires_review'])
    
    def test_classify_email_always_review_critical_categories(self):
        """Test that critical categories always require review."""
        self.mock_ai_processor.classify_email_with_explanation = Mock(
            return_value={
                'category': 'required_personal_action',
                'confidence': 0.99,  # Even high confidence
                'explanation': 'Critical action required',
                'alternatives': []
            }
        )
        
        result = self.adapter.classify_email("Test email")
        
        # required_personal_action has 1.0 threshold, always requires review
        self.assertTrue(result['requires_review'])
    
    def test_classify_email_error_handling(self):
        """Test error handling in classification."""
        self.mock_ai_processor.classify_email_with_explanation = Mock(
            side_effect=Exception("API Error")
        )
        
        result = self.adapter.classify_email("Test email")
        
        # Should return safe fallback
        self.assertEqual(result['category'], 'work_relevant')
        self.assertLess(result['confidence'], 0.8)
        self.assertTrue(result['requires_review'])
        self.assertIn('error', result)
    
    def test_classify_email_string_result(self):
        """Test handling of string classification result."""
        self.mock_ai_processor.classify_email_with_explanation = Mock(
            return_value="fyi"
        )
        
        result = self.adapter.classify_email("Test email")
        
        self.assertEqual(result['category'], "fyi")
        self.assertIn('confidence', result)
        self.assertIn('requires_review', result)
    
    def test_analyze_batch_success(self):
        """Test successful batch analysis."""
        emails = [
            {'subject': 'Urgent Task', 'sender': 'boss@example.com', 'body': 'Please do this'},
            {'subject': 'FYI Update', 'sender': 'team@example.com', 'body': 'Just FYI'},
        ]
        
        self.mock_ai_processor.holistic_inbox_analysis = Mock(
            return_value={
                'high_priority_count': 1,
                'action_required_count': 1,
                'conversation_threads': [
                    {'thread_id': 'thread1', 'emails': ['email1', 'email2']}
                ],
                'recommendations': [
                    'Focus on urgent task first',
                    'Review FYI items at end of day'
                ],
                'summary': 'You have 1 urgent task and 1 FYI item'
            }
        )
        
        result = self.adapter.analyze_batch(emails)
        
        self.assertEqual(result['total_emails'], 2)
        self.assertEqual(result['high_priority'], 1)
        self.assertEqual(result['action_required'], 1)
        self.assertEqual(len(result['threads']), 1)
        self.assertEqual(len(result['recommendations']), 2)
        self.assertIn('summary', result)
    
    def test_analyze_batch_string_result(self):
        """Test handling of string batch analysis result."""
        emails = [
            {'subject': 'Test', 'sender': 'test@example.com', 'body': 'Test body'},
        ]
        
        self.mock_ai_processor.holistic_inbox_analysis = Mock(
            return_value="Overall inbox looks good"
        )
        
        result = self.adapter.analyze_batch(emails)
        
        self.assertEqual(result['total_emails'], 1)
        self.assertEqual(result['summary'], "Overall inbox looks good")
        self.assertIn('recommendations', result)
    
    def test_analyze_batch_error_handling(self):
        """Test error handling in batch analysis."""
        emails = [{'subject': 'Test', 'sender': 'test@example.com', 'body': 'Test'}]
        
        self.mock_ai_processor.holistic_inbox_analysis = Mock(
            side_effect=Exception("Analysis failed")
        )
        
        result = self.adapter.analyze_batch(emails)
        
        self.assertEqual(result['total_emails'], 1)
        self.assertIn('error', result)
        self.assertIn('recommendations', result)
    
    def test_extract_action_items_success(self):
        """Test successful action item extraction."""
        email_content = "Subject: Complete Report\nFrom: manager@example.com\n\nPlease complete the quarterly report by Friday."
        
        self.mock_ai_processor.execute_prompty = Mock(
            return_value={
                'due_date': 'Friday',
                'action_required': 'Complete quarterly report',
                'explanation': 'Manager requests report completion',
                'relevance': 'High priority work task',
                'links': ['https://reports.example.com']
            }
        )
        
        result = self.adapter.extract_action_items(email_content)
        
        self.assertIn('action_items', result)
        self.assertEqual(len(result['action_items']), 1)
        self.assertEqual(result['due_date'], 'Friday')
        self.assertEqual(result['action_required'], 'Complete quarterly report')
        self.assertIn('explanation', result)
        self.assertIn('relevance', result)
        self.assertIn('links', result)
    
    def test_extract_action_items_error_handling(self):
        """Test error handling in action item extraction."""
        self.mock_ai_processor.execute_prompty = Mock(
            side_effect=Exception("Extraction failed")
        )
        
        result = self.adapter.extract_action_items("Test email")
        
        self.assertEqual(len(result['action_items']), 0)
        self.assertIn('error', result)
    
    def test_generate_summary_success(self):
        """Test successful summary generation."""
        email_content = "Subject: Project Update\nFrom: team@example.com\n\nThe project is on track and meeting all milestones."
        
        self.mock_ai_processor.execute_prompty = Mock(
            return_value="Project is on track and meeting milestones"
        )
        
        result = self.adapter.generate_summary(email_content)
        
        self.assertIn('summary', result)
        self.assertIn('key_points', result)
        self.assertIn('confidence', result)
        self.assertGreater(len(result['summary']), 0)
    
    def test_generate_summary_error_handling(self):
        """Test error handling in summary generation."""
        self.mock_ai_processor.execute_prompty = Mock(
            side_effect=Exception("Summary failed")
        )
        
        result = self.adapter.generate_summary("Test email")
        
        self.assertIn('error', result)
        self.assertEqual(result['confidence'], 0.0)
    
    def test_requires_review_logic(self):
        """Test the requires_review logic."""
        # Test below threshold
        self.assertTrue(
            self.adapter._requires_review('optional_action', 0.7)  # Below 0.8
        )
        
        # Test above threshold
        self.assertFalse(
            self.adapter._requires_review('optional_action', 0.9)  # Above 0.8
        )
        
        # Test critical category (always requires review)
        self.assertTrue(
            self.adapter._requires_review('required_personal_action', 0.99)  # Below 1.0
        )
        
        # Test unknown category (should default to always review)
        self.assertTrue(
            self.adapter._requires_review('unknown_category', 0.95)
        )


if __name__ == '__main__':
    unittest.main()
