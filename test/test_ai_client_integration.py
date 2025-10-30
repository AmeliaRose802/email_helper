#!/usr/bin/env python3
"""
Tests for AIProcessor integration with AIClient abstraction.
Verifies dependency injection and mock client usage.
"""

import sys
import os
import pytest

# Add parent directory to path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

from ai_processor import AIProcessor
from core.ai_client import MockAIClient, AIClient


def test_ai_processor_with_mock_client():
    """Test that AIProcessor can be instantiated with a mock AI client"""
    # Create a mock client with predefined responses
    mock_responses = {
        'email_classifier': {
            'category': 'work_relevant',
            'confidence': 0.95,
            'explanation': 'Test classification',
            'alternatives': []
        }
    }
    mock_client = MockAIClient(responses=mock_responses)
    
    # Create AIProcessor with mock client
    processor = AIProcessor(ai_client=mock_client)
    
    # Verify the client was injected
    assert processor.ai_client is mock_client
    assert isinstance(processor.ai_client, AIClient)
    
    # Verify we can execute a prompt through the mock
    result = processor.execute_prompty('email_classifier.prompty', {'test': 'data'})
    
    # Should return our mock response
    assert result['category'] == 'work_relevant'
    assert result['confidence'] == 0.95
    
    # Verify the call was recorded
    assert mock_client.get_call_count('email_classifier') == 1


def test_ai_processor_default_client():
    """Test that AIProcessor creates AzureOpenAIClient by default"""
    processor = AIProcessor()
    
    # Should have an AI client
    assert hasattr(processor, 'ai_client')
    assert processor.ai_client is not None
    assert isinstance(processor.ai_client, AIClient)


def test_mock_client_call_history():
    """Test that MockAIClient tracks call history correctly"""
    mock_client = MockAIClient()
    processor = AIProcessor(ai_client=mock_client)
    
    # Execute a few different prompts
    processor.execute_prompty('email_classifier.prompty', {'subject': 'Test'})
    processor.execute_prompty('summarize_action_item.prompty', {'body': 'Do something'})
    processor.execute_prompty('email_classifier.prompty', {'subject': 'Test 2'})
    
    # Verify call counts
    assert mock_client.get_call_count() == 3
    assert mock_client.get_call_count('email_classifier') == 2
    assert mock_client.get_call_count('summarize_action_item') == 1


def test_mock_client_default_responses():
    """Test that MockAIClient provides sensible default responses"""
    mock_client = MockAIClient()
    processor = AIProcessor(ai_client=mock_client)
    
    # Test classifier default
    result = processor.execute_prompty('email_classifier.prompty', {})
    assert 'category' in result
    assert 'confidence' in result
    
    # Test action item default
    result = processor.execute_prompty('summarize_action_item.prompty', {})
    assert 'due_date' in result
    assert 'action_required' in result
    
    # Test summary default
    result = processor.execute_prompty('email_one_line_summary.prompty', {})
    assert isinstance(result, str)


def test_mock_client_isolation():
    """Test that different mock clients are independent"""
    mock1 = MockAIClient(responses={'test': 'response1'})
    mock2 = MockAIClient(responses={'test': 'response2'})
    
    processor1 = AIProcessor(ai_client=mock1)
    processor2 = AIProcessor(ai_client=mock2)
    
    result1 = processor1.execute_prompty('test.prompty', {})
    result2 = processor2.execute_prompty('test.prompty', {})
    
    # Different responses
    assert result1 == 'response1'
    assert result2 == 'response2'
    
    # Different call histories
    assert mock1.get_call_count() == 1
    assert mock2.get_call_count() == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
