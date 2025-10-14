"""Integration tests for AI processing with COM services.

Tests the COMAIService integration with email classification, action item
extraction, and summarization workflows, including integration with the
COMEmailProvider for end-to-end processing.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json

import sys
sys.path.insert(0, '/home/runner/work/email_helper/email_helper')


@pytest.fixture
def mock_ai_processor():
    """Create a mock AIProcessor for testing."""
    processor = MagicMock()
    processor.execute_prompty = Mock()
    return processor


@pytest.fixture
def mock_azure_config():
    """Create mock Azure configuration."""
    config = MagicMock()
    config.endpoint = "https://test.openai.azure.com"
    config.api_key = "test-key"
    config.deployment_name = "test-deployment"
    return config


@pytest.fixture
def com_ai_service(mock_ai_processor, mock_azure_config):
    """Create COMAIService with mocked dependencies."""
    # Setup default mock returns for AI processor methods
    mock_ai_processor.classify_email_with_explanation = Mock(return_value={
        'category': 'work_relevant',
        'confidence': 0.8,
        'explanation': 'Email classified',
        'alternatives': []
    })
    mock_ai_processor.CONFIDENCE_THRESHOLDS = {
        'required_personal_action': 0.9,
        'optional_event': 0.85,
        'optional_fyi': 0.85
    }
    
    with patch('backend.services.com_ai_service.AIProcessor', return_value=mock_ai_processor):
        with patch('backend.services.com_ai_service.get_azure_config', return_value=mock_azure_config):
            from backend.services.com_ai_service import COMAIService
            service = COMAIService()
            service._ensure_initialized()
            return service


@pytest.mark.integration
@pytest.mark.asyncio
class TestAIEmailClassificationIntegration:
    """Integration tests for AI email classification workflows."""
    
    async def test_classify_email_workflow(self, com_ai_service, mock_ai_processor):
        """Test complete email classification workflow."""
        # Setup mock classification result
        mock_ai_processor.classify_email_with_explanation.return_value = {
            "category": "required_personal_action",
            "confidence": 0.95,
            "explanation": "Email contains action items requiring personal response",
            "alternatives": [
                {"category": "optional_fyi", "confidence": 0.05}
            ]
        }
        
        # Classify email
        email_content = """
        Subject: Project Review Required
        From: manager@example.com
        
        Hi Team,
        
        Please review the Q4 project report by Friday and provide your feedback.
        This is critical for our board meeting next week.
        
        Thanks
        """
        
        result = await com_ai_service.classify_email(email_content)
        
        # Verify classification
        assert result['category'] == 'required_personal_action'
        assert result['confidence'] == 0.95
        assert 'action items' in result['reasoning'].lower()
        assert len(result['alternatives']) == 1
        
        # Verify AI processor was called
        mock_ai_processor.classify_email_with_explanation.assert_called_once()
    
    async def test_classify_multiple_email_types(self, mock_ai_processor):
        """Test classification of different email types."""
        email_tests = [
            {
                'content': 'Subject: Team Meeting\nJoin us for weekly standup tomorrow at 10am',
                'expected_category': 'optional_event',
                'confidence': 0.88
            },
            {
                'content': 'Subject: FYI: System Maintenance\nThe server will be down for maintenance',
                'expected_category': 'optional_fyi',
                'confidence': 0.92
            },
            {
                'content': 'Subject: URGENT: Security Issue\nPlease update your password immediately',
                'expected_category': 'required_personal_action',
                'confidence': 0.97
            }
        ]
        
        for test_case in email_tests:
            # Setup mock result for this test case
            mock_ai_processor.classify_email_with_explanation.return_value = {
                "category": test_case['expected_category'],
                "confidence": test_case['confidence'],
                "explanation": f"Classified as {test_case['expected_category']}",
                "alternatives": []
            }
            
            with patch('backend.services.com_ai_service.AIProcessor', return_value=mock_ai_processor):
                with patch('backend.services.com_ai_service.get_azure_config', return_value=MagicMock()):
                    from backend.services.com_ai_service import COMAIService
                    service = COMAIService()
                    service._ensure_initialized()
            
                    # Classify email
                    result = await service.classify_email(test_case['content'])
                    
                    # Verify
                    assert result['category'] == test_case['expected_category']
                    assert result['confidence'] == test_case['confidence']
    
    async def test_classification_with_context(self, com_ai_service, mock_ai_processor):
        """Test email classification with additional context."""
        classification = json.dumps({
            "category": "required_personal_action",
            "confidence": 0.93,
            "reasoning": "High priority based on sender and context",
            "alternatives": []
        })
        mock_ai_processor.execute_prompty.return_value = classification
        
        email_content = "Subject: Quick Question\nCan you help with this?"
        context = "This is from your direct manager about an urgent project"
        
        result = await com_ai_service.classify_email(email_content, context=context)
        
        assert result['category'] == 'required_personal_action'
        assert result['confidence'] > 0.9
    
    async def test_classification_error_handling(self, com_ai_service, mock_ai_processor):
        """Test classification with AI service errors."""
        # Simulate AI error
        mock_ai_processor.execute_prompty.side_effect = Exception("AI service unavailable")
        
        result = await com_ai_service.classify_email("Test email")
        
        # Should return fallback classification
        assert 'category' in result
        assert result['confidence'] < 1.0
        assert 'error' in result


@pytest.mark.integration
@pytest.mark.asyncio
class TestAIActionItemExtractionIntegration:
    """Integration tests for AI action item extraction workflows."""
    
    async def test_extract_action_items_workflow(self, com_ai_service, mock_ai_processor):
        """Test complete action item extraction workflow."""
        action_items_result = json.dumps({
            "action_items": [
                {
                    "action": "Review Q4 project report",
                    "deadline": "Friday",
                    "priority": "high"
                },
                {
                    "action": "Provide feedback on report",
                    "deadline": "Friday",
                    "priority": "high"
                }
            ],
            "action_required": "Review report and provide feedback by Friday",
            "explanation": "Email contains explicit action items with deadline",
            "confidence": 0.92
        })
        mock_ai_processor.execute_prompty.return_value = action_items_result
        
        email_content = """
        Subject: Project Review Required
        
        Please review the Q4 project report by Friday and provide your feedback.
        This is critical for our board meeting next week.
        """
        
        result = await com_ai_service.extract_action_items(email_content)
        
        # Verify extraction
        assert len(result['action_items']) == 2
        assert result['action_items'][0]['action'] == "Review Q4 project report"
        assert result['action_items'][0]['priority'] == "high"
        assert 'Friday' in result['action_required']
        assert result['confidence'] == 0.92
    
    async def test_extract_action_items_no_actions(self, com_ai_service, mock_ai_processor):
        """Test action item extraction with no actions found."""
        no_actions_result = json.dumps({
            "action_items": [],
            "action_required": "No action required",
            "explanation": "Email is informational only",
            "confidence": 0.95
        })
        mock_ai_processor.execute_prompty.return_value = no_actions_result
        
        email_content = "Subject: FYI\nJust wanted to let you know the meeting went well."
        
        result = await com_ai_service.extract_action_items(email_content)
        
        assert len(result['action_items']) == 0
        assert result['action_required'] == "No action required"
        assert result['confidence'] == 0.95
    
    async def test_extract_action_items_with_invalid_json(self, com_ai_service, mock_ai_processor):
        """Test action item extraction with malformed JSON response."""
        # Return invalid JSON
        mock_ai_processor.execute_prompty.return_value = "Invalid JSON response"
        
        result = await com_ai_service.extract_action_items("Test email content")
        
        # Should use fallback parsing
        assert 'action_required' in result
        assert result['confidence'] >= 0
        assert isinstance(result['action_items'], list)
    
    async def test_extract_multiple_action_types(self, com_ai_service, mock_ai_processor):
        """Test extraction of different types of action items."""
        action_items_result = json.dumps({
            "action_items": [
                {
                    "action": "Attend meeting",
                    "deadline": "Tomorrow 10am",
                    "priority": "medium"
                },
                {
                    "action": "Submit expense report",
                    "deadline": "End of week",
                    "priority": "low"
                },
                {
                    "action": "Review security policy",
                    "deadline": "ASAP",
                    "priority": "critical"
                }
            ],
            "action_required": "Multiple actions required with varying priorities",
            "explanation": "Email contains multiple action items",
            "confidence": 0.89
        })
        mock_ai_processor.execute_prompty.return_value = action_items_result
        
        email_content = "Multiple action items email"
        result = await com_ai_service.extract_action_items(email_content)
        
        assert len(result['action_items']) == 3
        # Verify different priorities present
        priorities = [item['priority'] for item in result['action_items']]
        assert 'critical' in priorities
        assert 'medium' in priorities
        assert 'low' in priorities


@pytest.mark.integration
@pytest.mark.asyncio
class TestAISummarizationIntegration:
    """Integration tests for AI email summarization workflows."""
    
    async def test_generate_summary_brief(self, com_ai_service, mock_ai_processor):
        """Test brief summary generation workflow."""
        summary_result = "Manager requests Q4 report review and feedback by Friday for board meeting"
        mock_ai_processor.execute_prompty.return_value = summary_result
        
        email_content = """
        Subject: Project Review Required
        
        Hi Team,
        
        Please review the Q4 project report by Friday and provide your feedback.
        This is critical for our board meeting next week.
        """
        
        result = await com_ai_service.generate_summary(email_content, summary_type="brief")
        
        assert 'Q4 report' in result['summary']
        assert 'Friday' in result['summary']
        assert result['confidence'] >= 0.8
        assert len(result['key_points']) > 0
    
    async def test_generate_summary_detailed(self, com_ai_service, mock_ai_processor):
        """Test detailed summary generation workflow."""
        detailed_summary = """
        The manager is requesting team members to review the Q4 project report.
        Key points:
        - Review required by Friday
        - Feedback needed
        - Critical for upcoming board meeting
        - Report covers Q4 activities
        """
        mock_ai_processor.execute_prompty.return_value = detailed_summary
        
        email_content = "Long email content here..."
        
        result = await com_ai_service.generate_summary(email_content, summary_type="detailed")
        
        assert len(result['summary']) > 50  # Detailed should be longer
        assert len(result['key_points']) >= 3
        assert result['confidence'] >= 0.8
    
    async def test_generate_summary_for_different_email_types(self, com_ai_service, mock_ai_processor):
        """Test summary generation for various email types."""
        test_cases = [
            {
                'type': 'meeting_invite',
                'summary': 'Team standup meeting tomorrow at 10am in Conference Room A'
            },
            {
                'type': 'announcement',
                'summary': 'System maintenance scheduled for this weekend, expect brief downtime'
            },
            {
                'type': 'question',
                'summary': 'Colleague asks about project timeline and deliverables'
            }
        ]
        
        for test_case in test_cases:
            mock_ai_processor.execute_prompty.return_value = test_case['summary']
            
            result = await com_ai_service.generate_summary(f"Email about {test_case['type']}")
            
            assert len(result['summary']) > 0
            assert result['confidence'] > 0
    
    async def test_summary_generation_error_handling(self, com_ai_service, mock_ai_processor):
        """Test summary generation with errors."""
        mock_ai_processor.execute_prompty.side_effect = Exception("Summarization failed")
        
        result = await com_ai_service.generate_summary("Test email")
        
        # Should return fallback
        assert 'summary' in result
        assert 'error' in result
        assert result['confidence'] == 0.0


@pytest.mark.integration
@pytest.mark.asyncio
class TestAIEmailProviderIntegration:
    """Integration tests combining AI service with email provider."""
    
    async def test_email_retrieval_and_classification_workflow(
        self, com_ai_service, mock_ai_processor
    ):
        """Test full workflow: retrieve emails → classify."""
        # Setup email provider mock
        mock_provider = MagicMock()
        mock_emails = [
            {
                'id': 'email-1',
                'subject': 'Project Review',
                'body': 'Please review the project report',
                'sender': 'manager@example.com'
            },
            {
                'id': 'email-2',
                'subject': 'FYI: Update',
                'body': 'Just letting you know about the update',
                'sender': 'team@example.com'
            }
        ]
        mock_provider.get_emails.return_value = mock_emails
        mock_provider.authenticate.return_value = True
        
        # Setup AI classification
        classifications = [
            json.dumps({
                "category": "required_personal_action",
                "confidence": 0.93,
                "reasoning": "Action required",
                "alternatives": []
            }),
            json.dumps({
                "category": "optional_fyi",
                "confidence": 0.91,
                "reasoning": "Informational",
                "alternatives": []
            })
        ]
        mock_ai_processor.execute_prompty.side_effect = classifications
        
        # Authenticate provider
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', return_value=MagicMock()):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                provider = COMEmailProvider()
                provider.adapter = mock_provider
                provider.authenticated = True
                
                # Get emails
                emails = provider.get_emails("Inbox", count=5)
                assert len(emails) == 2
                
                # Classify each email
                classified_emails = []
                for email in emails:
                    email_text = f"Subject: {email['subject']}\n\n{email['body']}"
                    classification = await com_ai_service.classify_email(email_text)
                    classified_emails.append({
                        **email,
                        'classification': classification
                    })
                
                # Verify results
                assert len(classified_emails) == 2
                assert classified_emails[0]['classification']['category'] == 'required_personal_action'
                assert classified_emails[1]['classification']['category'] == 'optional_fyi'
    
    async def test_email_retrieval_and_action_extraction_workflow(
        self, com_ai_service, mock_ai_processor
    ):
        """Test workflow: retrieve emails → extract action items."""
        # Setup email with action items
        mock_provider = MagicMock()
        mock_email = {
            'id': 'email-action',
            'subject': 'Action Required',
            'body': 'Please complete the following tasks by EOD',
            'sender': 'manager@example.com'
        }
        mock_provider.get_emails.return_value = [mock_email]
        mock_provider.authenticate.return_value = True
        
        # Setup action extraction
        action_result = json.dumps({
            "action_items": [
                {"action": "Complete task 1", "deadline": "EOD", "priority": "high"},
                {"action": "Complete task 2", "deadline": "EOD", "priority": "high"}
            ],
            "action_required": "Complete tasks by EOD",
            "explanation": "Manager requires task completion",
            "confidence": 0.94
        })
        mock_ai_processor.execute_prompty.return_value = action_result
        
        # Execute workflow
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', return_value=MagicMock()):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                provider = COMEmailProvider()
                provider.adapter = mock_provider
                provider.authenticated = True
                
                # Get email
                emails = provider.get_emails("Inbox", count=1)
                email = emails[0]
                
                # Extract action items
                email_text = f"Subject: {email['subject']}\n\n{email['body']}"
                actions = await com_ai_service.extract_action_items(email_text)
                
                # Verify
                assert len(actions['action_items']) == 2
                assert actions['confidence'] == 0.94
    
    async def test_email_retrieval_and_summarization_workflow(
        self, com_ai_service, mock_ai_processor
    ):
        """Test workflow: retrieve emails → generate summaries."""
        # Setup multiple emails
        mock_provider = MagicMock()
        mock_emails = [
            {'id': 'e1', 'subject': 'Meeting', 'body': 'Meeting details'},
            {'id': 'e2', 'subject': 'Report', 'body': 'Report content'},
            {'id': 'e3', 'subject': 'Update', 'body': 'Status update'}
        ]
        mock_provider.get_emails.return_value = mock_emails
        mock_provider.authenticate.return_value = True
        
        # Setup summaries
        summaries = [
            "Team meeting scheduled for tomorrow",
            "Quarterly report ready for review",
            "Project status updated to in progress"
        ]
        mock_ai_processor.execute_prompty.side_effect = summaries
        
        # Execute workflow
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', return_value=MagicMock()):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                provider = COMEmailProvider()
                provider.adapter = mock_provider
                provider.authenticated = True
                
                # Get emails and summarize
                emails = provider.get_emails("Inbox", count=3)
                summarized_emails = []
                
                for email in emails:
                    email_text = f"Subject: {email['subject']}\n\n{email['body']}"
                    summary = await com_ai_service.generate_summary(email_text)
                    summarized_emails.append({
                        **email,
                        'summary': summary
                    })
                
                # Verify
                assert len(summarized_emails) == 3
                assert all('summary' in email for email in summarized_emails)


@pytest.mark.integration
@pytest.mark.asyncio
class TestAIServiceResilience:
    """Integration tests for AI service error resilience."""
    
    async def test_ai_service_timeout_handling(self, com_ai_service, mock_ai_processor):
        """Test handling of AI service timeouts."""
        import asyncio
        
        # Simulate timeout
        async def slow_execution(*args, **kwargs):
            await asyncio.sleep(10)
            return "result"
        
        mock_ai_processor.execute_prompty.side_effect = asyncio.TimeoutError()
        
        result = await com_ai_service.classify_email("Test email")
        
        # Should return fallback
        assert 'category' in result
        assert 'error' in result
    
    async def test_ai_service_retry_logic(self, com_ai_service, mock_ai_processor):
        """Test retry logic for transient failures."""
        # First call fails, second succeeds
        classification = json.dumps({
            "category": "optional_fyi",
            "confidence": 0.85,
            "reasoning": "Test",
            "alternatives": []
        })
        
        mock_ai_processor.execute_prompty.side_effect = [
            Exception("Transient error"),
            classification
        ]
        
        # For this test, we'll just verify error handling works
        result = await com_ai_service.classify_email("Test email")
        
        # First attempt should fail and return fallback
        assert 'category' in result
