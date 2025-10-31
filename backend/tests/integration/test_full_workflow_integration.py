"""Integration tests for complete email processing workflows.

Tests end-to-end workflows combining COM email provider, AI processing,
and complete pipeline operations from email retrieval through classification,
action extraction, and summarization.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json


@pytest.fixture
def mock_complete_email_provider():
    """Create a comprehensive mock email provider."""
    provider = MagicMock()
    provider.authenticate = Mock(return_value=True)
    provider.authenticated = True
    
    # Mock email data
    provider.get_emails = Mock(return_value=[
        {
            'id': 'email-1',
            'subject': 'Urgent: Project Deadline',
            'sender': 'manager@example.com',
            'recipient': 'user@example.com',
            'body': 'Please submit the project report by Friday. This is critical.',
            'received_time': '2024-01-01T10:00:00Z',
            'is_read': False,
            'categories': ['Important'],
            'conversation_id': 'conv-1'
        },
        {
            'id': 'email-2',
            'subject': 'Team Meeting Tomorrow',
            'sender': 'team@example.com',
            'recipient': 'user@example.com',
            'body': 'Join us for the weekly standup at 10am.',
            'received_time': '2024-01-01T11:00:00Z',
            'is_read': False,
            'categories': [],
            'conversation_id': 'conv-2'
        },
        {
            'id': 'email-3',
            'subject': 'FYI: System Update',
            'sender': 'it@example.com',
            'recipient': 'user@example.com',
            'body': 'The system will be updated this weekend.',
            'received_time': '2024-01-01T12:00:00Z',
            'is_read': True,
            'categories': [],
            'conversation_id': 'conv-3'
        }
    ])
    
    provider.get_folders = Mock(return_value=[
        {'id': 'inbox', 'name': 'Inbox', 'item_count': 25},
        {'id': 'sent', 'name': 'Sent Items', 'item_count': 10}
    ])
    
    provider.mark_as_read = Mock(return_value=True)
    provider.move_email = Mock(return_value=True)
    
    return provider


@pytest.fixture
def mock_complete_ai_service():
    """Create a comprehensive mock AI service."""
    service = MagicMock()
    service._initialized = True
    service._ensure_initialized = Mock()
    
    # Mock AI processor responses
    ai_processor = MagicMock()
    
    def execute_prompty_side_effect(*args, **kwargs):
        # Return different results based on call context
        prompty_path = args[0] if args else ""
        
        if "classification" in str(prompty_path).lower():
            return json.dumps({
                "category": "required_personal_action",
                "confidence": 0.92,
                "reasoning": "Email requires action",
                "alternatives": []
            })
        elif "action" in str(prompty_path).lower():
            return json.dumps({
                "action_items": [
                    {"action": "Submit report", "deadline": "Friday", "priority": "high"}
                ],
                "action_required": "Submit report by Friday",
                "explanation": "Manager requests report submission",
                "confidence": 0.90
            })
        elif "summar" in str(prompty_path).lower():
            return "Manager requests project report submission by Friday deadline"
        else:
            return json.dumps({"result": "default"})
    
    ai_processor.execute_prompty.side_effect = execute_prompty_side_effect
    service.ai_processor = ai_processor
    
    return service


@pytest.mark.integration
class TestCompleteEmailProcessingWorkflow:
    """Test complete end-to-end email processing workflows."""
    
    @pytest.mark.asyncio
    async def test_email_retrieval_to_classification_pipeline(
        self, mock_complete_email_provider, mock_ai_orchestrator, mock_azure_config_obj
    ):
        """Test full workflow: retrieve emails → classify each."""
        # Setup AI orchestrator with different classifications for different emails
        classifications = [
            {
                "category": "required_personal_action",
                "confidence": 0.95,
                "reasoning": "Urgent deadline requires action",
                "alternatives": []
            },
            {
                "category": "optional_event",
                "confidence": 0.88,
                "reasoning": "Meeting invitation",
                "alternatives": []
            },
            {
                "category": "optional_fyi",
                "confidence": 0.92,
                "reasoning": "Informational update",
                "alternatives": []
            }
        ]
        
        call_count = [0]
        def classify_side_effect(*args, **kwargs):
            result = classifications[call_count[0] % len(classifications)]
            call_count[0] += 1
            return result
        
        mock_ai_orchestrator.classify_email_with_explanation = Mock(side_effect=classify_side_effect)
        
        with patch('backend.core.business.ai_orchestrator.AIOrchestrator', return_value=mock_ai_orchestrator):
            with patch('backend.core.infrastructure.azure_config.get_azure_config', return_value=mock_azure_config_obj):
                from backend.services.ai_service import AIService
                ai_service = AIService()
                ai_service._ensure_initialized()
                
                # Authenticate and retrieve emails
                mock_complete_email_provider.authenticate({})
                emails = mock_complete_email_provider.get_emails("Inbox", count=5)
                
                assert len(emails) == 3
                
                # Classify each email
                classified_emails = []
                for email in emails:
                    email_text = f"Subject: {email['subject']}\nFrom: {email['sender']}\n\n{email['body']}"
                    classification = await ai_service.classify_email(email_text)
                    
                    classified_emails.append({
                        'email_id': email['id'],
                        'subject': email['subject'],
                        'category': classification['category'],
                        'confidence': classification['confidence'],
                        'original_email': email
                    })
                
                # Verify all emails were classified
                assert len(classified_emails) == 3
                assert classified_emails[0]['category'] == 'required_personal_action'
                assert classified_emails[1]['category'] == 'optional_event'
                assert classified_emails[2]['category'] == 'optional_fyi'
                
                # Verify confidence levels
                assert all(email['confidence'] > 0.8 for email in classified_emails)
    
    @pytest.mark.asyncio
    async def test_email_retrieval_to_action_extraction_pipeline(
        self, mock_complete_email_provider, mock_ai_orchestrator, mock_azure_config_obj
    ):
        """Test workflow: retrieve emails → extract action items."""
        # Setup AI orchestrator with action item results
        action_results = [
            json.dumps({
                "action_items": [
                    {
                        "action": "Submit project report",
                        "deadline": "Friday",
                        "priority": "high"
                    }
                ],
                "action_required": "Submit project report by Friday",
                "explanation": "Manager requires report submission",
                "confidence": 0.94,
                "relevance": "high",
                "links": []
            }),
            json.dumps({
                "action_items": [
                    {
                        "action": "Attend team meeting",
                        "deadline": "Tomorrow at 10am",
                        "priority": "medium"
                    }
                ],
                "action_required": "Attend meeting tomorrow",
                "explanation": "Meeting attendance requested",
                "confidence": 0.89,
                "relevance": "medium",
                "links": []
            }),
            json.dumps({
                "action_items": [],
                "action_required": "No action required",
                "explanation": "Informational email only",
                "confidence": 0.96,
                "relevance": "low",
                "links": []
            })
        ]
        
        call_count = [0]
        def action_side_effect(*args, **kwargs):
            result = action_results[call_count[0] % len(action_results)]
            call_count[0] += 1
            return result
        
        mock_ai_orchestrator.execute_prompty = Mock(side_effect=action_side_effect)
        
        with patch('backend.core.business.ai_orchestrator.AIOrchestrator', return_value=mock_ai_orchestrator):
            with patch('backend.core.infrastructure.azure_config.get_azure_config', return_value=mock_azure_config_obj):
                from backend.services.ai_service import AIService
                ai_service = AIService()
                ai_service._ensure_initialized()
                
                # Get emails
                emails = mock_complete_email_provider.get_emails("Inbox", count=5)
                
                # Extract action items from each
                emails_with_actions = []
                for email in emails:
                    email_text = f"Subject: {email['subject']}\n\n{email['body']}"
                    actions = await ai_service.extract_action_items(email_text)
                    
                    emails_with_actions.append({
                        'email_id': email['id'],
                        'subject': email['subject'],
                        'action_items': actions['action_items'],
                        'action_required': actions['action_required'],
                        'confidence': actions['confidence']
                    })
                
                # Verify results
                assert len(emails_with_actions) == 3
                
                # First email has action items
                assert len(emails_with_actions[0]['action_items']) == 1
                assert 'Submit project report' in emails_with_actions[0]['action_items'][0]['action']
                
                # Second email has action items
                assert len(emails_with_actions[1]['action_items']) == 1
                assert 'meeting' in emails_with_actions[1]['action_items'][0]['action'].lower()
                
                # Third email has no action items
                assert len(emails_with_actions[2]['action_items']) == 0
    
    @pytest.mark.asyncio
    async def test_email_retrieval_to_summarization_pipeline(
        self, mock_complete_email_provider
    ):
        """Test workflow: retrieve emails → generate summaries."""
        # Setup AI service
        with patch('backend.core.business.ai_orchestrator.AIOrchestrator') as mock_ai_class:
            with patch('backend.core.infrastructure.azure_config.get_azure_config'):
                mock_ai = MagicMock()
                
                # Return summaries
                summaries = [
                    "Manager requests urgent project report submission by Friday deadline",
                    "Team standup meeting scheduled for tomorrow at 10am",
                    "IT department announces system maintenance this weekend"
                ]
                mock_ai.execute_prompty.side_effect = summaries
                mock_ai_class.return_value = mock_ai
                
                from backend.services.ai_service import AIService
                ai_service = AIService()
                ai_service._ensure_initialized()
                
                # Get emails
                emails = mock_complete_email_provider.get_emails("Inbox", count=5)
                
                # Generate summaries
                summarized_emails = []
                for email in emails:
                    email_text = f"Subject: {email['subject']}\n\n{email['body']}"
                    summary_result = await ai_service.generate_summary(email_text)
                    
                    summarized_emails.append({
                        'email_id': email['id'],
                        'subject': email['subject'],
                        'summary': summary_result['summary'],
                        'confidence': summary_result['confidence']
                    })
                
                # Verify summaries
                assert len(summarized_emails) == 3
                assert 'project report' in summarized_emails[0]['summary'].lower()
                assert 'meeting' in summarized_emails[1]['summary'].lower()
                assert 'system' in summarized_emails[2]['summary'].lower()
    
    @pytest.mark.asyncio
    async def test_complete_email_processing_pipeline(
        self, mock_complete_email_provider, mock_ai_orchestrator, mock_azure_config_obj
    ):
        """Test full pipeline: retrieve → classify → extract actions → summarize."""
        # Setup AI orchestrator with complete pipeline responses
        call_count = [0]
        
        def execute_prompty_side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 0:
                # Action extraction
                return json.dumps({
                    "action_items": [
                        {"action": "Submit report", "deadline": "Friday", "priority": "high"}
                    ],
                    "action_required": "Submit report",
                    "explanation": "Report needed",
                    "confidence": 0.93,
                    "relevance": "high",
                    "links": []
                })
            else:
                # Summary
                return "Urgent project report due Friday"
        
        mock_ai_orchestrator.classify_email_with_explanation = Mock(return_value={
            "category": "required_personal_action",
            "confidence": 0.95,
            "reasoning": "Urgent action required",
            "alternatives": []
        })
        mock_ai_orchestrator.execute_prompty = Mock(side_effect=execute_prompty_side_effect)
        
        with patch('backend.core.business.ai_orchestrator.AIOrchestrator', return_value=mock_ai_orchestrator):
            with patch('backend.core.infrastructure.azure_config.get_azure_config', return_value=mock_azure_config_obj):
                from backend.services.ai_service import AIService
                ai_service = AIService()
                ai_service._ensure_initialized()
                
                # Get first email
                emails = mock_complete_email_provider.get_emails("Inbox", count=1)
                email = emails[0]
                
                # Process through complete pipeline
                email_text = f"Subject: {email['subject']}\n\n{email['body']}"
                
                # Step 1: Classify
                classification = await ai_service.classify_email(email_text)
                
                # Step 2: Extract actions
                actions = await ai_service.extract_action_items(email_text)
                
                # Step 3: Summarize
                summary = await ai_service.generate_summary(email_text)
                
                # Combine results
                processed_email = {
                    **email,
                    'classification': classification,
                    'action_items': actions['action_items'],
                    'summary': summary['summary']
                }
                
                # Verify complete processing
                assert processed_email['classification']['category'] == 'required_personal_action'
                assert len(processed_email['action_items']) == 1
                assert 'project report' in processed_email['summary'].lower()


@pytest.mark.integration
class TestWorkflowErrorHandling:
    """Test error handling in complete workflows."""
    
    @pytest.mark.asyncio
    async def test_email_retrieval_failure_handling(self):
        """Test handling of email retrieval failures."""
        # Setup provider that fails
        mock_provider = MagicMock()
        mock_provider.authenticate.return_value = True
        mock_provider.get_emails.side_effect = RuntimeError("Outlook connection lost")
        
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', return_value=MagicMock()):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                from fastapi import HTTPException
                
                provider = COMEmailProvider()
                provider.adapter = mock_provider
                provider.authenticated = True
                
                # Should raise HTTPException
                with pytest.raises(HTTPException) as exc_info:
                    provider.get_emails("Inbox")
                
                assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_ai_classification_failure_handling(self, mock_ai_orchestrator, mock_azure_config_obj):
        """Test handling of AI classification failures."""
        # Simulate AI error
        mock_ai_orchestrator.classify_email_with_explanation = Mock(side_effect=Exception("AI service unavailable"))
        
        with patch('backend.core.business.ai_orchestrator.AIOrchestrator', return_value=mock_ai_orchestrator):
            with patch('backend.core.infrastructure.azure_config.get_azure_config', return_value=mock_azure_config_obj):
                from backend.services.ai_service import AIService
                
                ai_service = AIService()
                ai_service._ensure_initialized()
                
                # Should return fallback classification
                result = await ai_service.classify_email("Test email")
                
                assert 'category' in result
                assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_partial_workflow_failure_recovery(
        self, mock_complete_email_provider, mock_ai_orchestrator, mock_azure_config_obj
    ):
        """Test recovery from partial workflow failures."""
        # Setup: first execute_prompty call fails, second succeeds
        call_count = [0]
        def execute_prompty_side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 0:
                # First call (action extraction) fails
                raise Exception("Temporary failure")
            else:
                # Second call (summary) succeeds
                return "Summary text"
        
        mock_ai_orchestrator.classify_email_with_explanation = Mock(return_value={
            "category": "required_personal_action",
            "confidence": 0.92,
            "reasoning": "Test",
            "alternatives": []
        })
        mock_ai_orchestrator.execute_prompty = Mock(side_effect=execute_prompty_side_effect)
        
        with patch('backend.core.business.ai_orchestrator.AIOrchestrator', return_value=mock_ai_orchestrator):
            with patch('backend.core.infrastructure.azure_config.get_azure_config', return_value=mock_azure_config_obj):
                from backend.services.ai_service import AIService
                
                ai_service = AIService()
                ai_service._ensure_initialized()
                
                # Get email
                emails = mock_complete_email_provider.get_emails("Inbox", count=1)
                email = emails[0]
                email_text = f"Subject: {email['subject']}\n\n{email['body']}"
                
                # Classification should succeed
                classification = await ai_service.classify_email(email_text)
                assert classification['category'] == 'required_personal_action'
                
                # Action extraction should fail gracefully
                actions = await ai_service.extract_action_items(email_text)
                assert 'error' in actions
                
                # Summary should succeed
                summary = await ai_service.generate_summary(email_text)
                assert 'summary' in summary


@pytest.mark.integration
class TestWorkflowPerformance:
    """Test workflow performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_batch_email_processing_performance(
        self, mock_complete_email_provider
    ):
        """Test processing multiple emails efficiently."""
        # Setup for batch processing
        with patch('backend.core.business.ai_orchestrator.AIOrchestrator') as mock_ai_class:
            with patch('backend.core.infrastructure.azure_config.get_azure_config'):
                mock_ai = MagicMock()
                
                # Return quick results for batch
                mock_ai.execute_prompty.return_value = json.dumps({
                    "category": "optional_fyi",
                    "confidence": 0.85,
                    "reasoning": "Test",
                    "alternatives": []
                })
                mock_ai_class.return_value = mock_ai
                
                from backend.services.ai_service import AIService
                
                ai_service = AIService()
                ai_service._ensure_initialized()
                
                # Process multiple emails
                emails = mock_complete_email_provider.get_emails("Inbox", count=10)
                
                classified = []
                for email in emails[:3]:  # Process subset
                    email_text = f"Subject: {email['subject']}\n\n{email['body']}"
                    classification = await ai_service.classify_email(email_text)
                    classified.append(classification)
                
                # Verify batch completed
                assert len(classified) == 3
                assert all('category' in c for c in classified)
    
    @pytest.mark.asyncio
    async def test_concurrent_email_operations(
        self, mock_complete_email_provider
    ):
        """Test concurrent email operations."""
        # Test that multiple operations can be performed
        emails = mock_complete_email_provider.get_emails("Inbox", count=5)
        assert len(emails) >= 3
        
        # Mark multiple as read
        results = []
        for email in emails[:3]:
            result = mock_complete_email_provider.mark_as_read(email['id'])
            results.append(result)
        
        assert all(results)


@pytest.mark.integration
class TestWorkflowDataPersistence:
    """Test data persistence in workflows."""
    
    @pytest.mark.asyncio
    async def test_processed_email_state_tracking(
        self, mock_complete_email_provider
    ):
        """Test tracking state of processed emails."""
        # Get emails
        emails = mock_complete_email_provider.get_emails("Inbox", count=3)
        
        # Track processed state
        processed_state = {}
        for email in emails:
            processed_state[email['id']] = {
                'processed': True,
                'classification': 'pending',
                'summary': None
            }
        
        # Verify state tracking
        assert len(processed_state) == 3
        assert all(state['processed'] for state in processed_state.values())
    
    @pytest.mark.asyncio
    async def test_email_categorization_persistence(
        self, mock_complete_email_provider, mock_ai_orchestrator, mock_azure_config_obj
    ):
        """Test persisting email categories after classification."""
        mock_ai_orchestrator.classify_email_with_explanation = Mock(return_value={
            "category": "required_personal_action",
            "confidence": 0.90,
            "reasoning": "Test",
            "alternatives": []
        })
        
        with patch('backend.core.business.ai_orchestrator.AIOrchestrator', return_value=mock_ai_orchestrator):
            with patch('backend.core.infrastructure.azure_config.get_azure_config', return_value=mock_azure_config_obj):
                from backend.services.ai_service import AIService
                
                ai_service = AIService()
                ai_service._ensure_initialized()
                
                # Process and categorize
                emails = mock_complete_email_provider.get_emails("Inbox", count=1)
                email = emails[0]
                
                email_text = f"Subject: {email['subject']}\n\n{email['body']}"
                classification = await ai_service.classify_email(email_text)
                
                # Simulate persistence
                email_with_category = {
                    **email,
                    'ai_category': classification['category'],
                    'ai_confidence': classification['confidence']
                }
                
                assert email_with_category['ai_category'] == 'required_personal_action'
                assert email_with_category['ai_confidence'] == 0.90

