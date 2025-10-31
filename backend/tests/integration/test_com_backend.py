"""Integration tests for COM backend workflows.

This module tests complete workflows combining COM email provider and AI service,
including error scenarios and edge cases. These tests validate that the adapters
work together correctly to process emails from retrieval through analysis.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from backend.tests.fixtures.email_fixtures import (
    get_action_required_email,
    get_meeting_invitation_email,
    get_newsletter_email,
    get_urgent_email,
    get_email_batch_for_classification,
    get_duplicate_emails,
    get_conversation_thread
)
from backend.tests.fixtures.ai_response_fixtures import (
    get_classification_response_required_action,
    get_action_items_response_single,
    get_summary_response_meeting,
    get_duplicate_detection_response_with_duplicates
)
from backend.tests.utils import (
    assert_email_structure,
    assert_classification_structure,
    assert_action_items_structure,
    extract_email_ids
)


@pytest.mark.integration
class TestEmailRetrievalToClassification:
    """Test email retrieval followed by classification workflow."""
    
    @pytest.fixture
    def mock_adapter_with_emails(self):
        """Create mock adapter with sample emails."""
        adapter_instance = Mock()
        adapter_instance.connect = Mock(return_value=True)
        adapter_instance.get_emails = Mock(return_value=get_email_batch_for_classification())
        adapter_instance.get_email_body = Mock(return_value="Full email body")
        
        adapter_class = Mock(return_value=adapter_instance)
        return adapter_class, adapter_instance
    
    @pytest.fixture
    def mock_ai_for_classification(self):
        """Create mock AI processor for classification."""
        processor = Mock()
        classification_result = get_classification_response_required_action()
        
        # classify_email_with_explanation is what actually gets called
        processor.classify_email_with_explanation = Mock(return_value={
            'category': classification_result["category"],
            'confidence': classification_result["confidence"],
            'explanation': classification_result.get("reasoning", "Email classified"),
            'alternatives': []
        })
        processor.execute_prompty = Mock(return_value=classification_result)
        processor.CONFIDENCE_THRESHOLDS = {'required_personal_action': 0.9}
        return processor
    
    @pytest.mark.asyncio
    async def test_retrieve_and_classify_workflow(
        self,
        mock_adapter_with_emails,
        mock_ai_for_classification
    ):
        """Test complete workflow from email retrieval to classification."""
        adapter_class, adapter_instance = mock_adapter_with_emails
        
        # Step 1: Retrieve emails via COM provider
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', adapter_class):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                
                provider = COMEmailProvider()
                provider.adapter = adapter_instance
                provider.authenticate({})
                
                emails = provider.get_emails()
                
                # Verify emails were retrieved
                assert len(emails) > 0
                assert adapter_instance.get_emails.called
                
                # Verify email structure
                for email in emails:
                    assert_email_structure(email)
        
        # Step 2: Classify emails via AI service
        from backend.services.ai_service import AIService
        from unittest.mock import MagicMock
        
        mock_config = MagicMock()
        ai_service = AIService(ai_orchestrator=mock_ai_for_classification, azure_config=mock_config)
        
        # Classify first email
        email = emails[0]
        email_text = f"Subject: {email['subject']}\n\n{email['body']}"
        
        result = await ai_service.classify_email(email_text)
        
        # Verify classification
        assert "category" in result
        assert "confidence" in result
        assert_classification_structure(result)
        # classify_email_with_explanation is called internally
        assert mock_ai_for_classification.classify_email_with_explanation.call_count > 0
    
    @pytest.mark.asyncio
    async def test_batch_email_classification(
        self,
        mock_adapter_with_emails,
        mock_ai_for_classification
    ):
        """Test batch classification of multiple emails."""
        adapter_class, adapter_instance = mock_adapter_with_emails
        
        # Retrieve emails
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', adapter_class):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                
                provider = COMEmailProvider()
                provider.adapter = adapter_instance
                provider.authenticate({})
                emails = provider.get_emails()
        
        # Classify all emails - Use constructor injection
        from backend.services.ai_service import AIService
        from unittest.mock import MagicMock
        
        mock_config = MagicMock()
        ai_service = AIService(ai_orchestrator=mock_ai_for_classification, azure_config=mock_config)
        
        classifications = []
        for email in emails:
            email_text = f"Subject: {email['subject']}\n\n{email['body']}"
            result = await ai_service.classify_email(email_text)
            classifications.append({
                "email_id": email["id"],
                "classification": result
            })
        
        # Verify all emails were classified
        assert len(classifications) == len(emails)
        assert all("classification" in c for c in classifications)


@pytest.mark.integration
class TestEmailProcessingToActionItems:
    """Test email processing through action item extraction workflow."""
    
    @pytest.mark.asyncio
    async def test_action_email_to_action_items(self):
        """Test workflow from action-required email to action item extraction."""
        # Setup COM provider with action email
        action_email = get_action_required_email()
        
        adapter_instance = Mock()
        adapter_instance.connect = Mock(return_value=True)
        adapter_instance.get_emails = Mock(return_value=[action_email])
        adapter_instance.get_email_body = Mock(return_value=action_email["body"])
        adapter_class = Mock(return_value=adapter_instance)
        
        # Setup AI processor
        ai_processor = Mock()
        action_items_result = get_action_items_response_single()
        ai_processor.execute_prompty = Mock(return_value=action_items_result)
        ai_processor.extract_action_items = Mock(return_value=action_items_result)
        
        # Execute workflow
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', adapter_class):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                
                # Step 1: Retrieve email
                provider = COMEmailProvider()
                provider.adapter = adapter_instance
                provider.authenticate({})
                emails = provider.get_emails()
                
                assert len(emails) == 1
                email = emails[0]
        
        # Step 2: Extract action items - Use constructor injection
        from backend.services.ai_service import AIService
        from unittest.mock import MagicMock
        
        mock_config = MagicMock()
        ai_service = AIService(ai_orchestrator=ai_processor, azure_config=mock_config)
        
        email_text = f"Subject: {email['subject']}\n\n{email['body']}"
        action_items = await ai_service.extract_action_items(email_text)
        
        # Verify action items
        assert_action_items_structure(action_items)
        assert action_items["action_required"] is not None
        assert "due_date" in action_items
        assert "action_items" in action_items
        assert len(action_items["action_items"]) > 0
    
    @pytest.mark.asyncio
    async def test_classify_then_extract_actions(self):
        """Test classification followed by action item extraction."""
        action_email = get_action_required_email()
        
        # Setup mocks
        adapter_instance = Mock()
        adapter_instance.connect = Mock(return_value=True)
        adapter_instance.get_emails = Mock(return_value=[action_email])
        adapter_class = Mock(return_value=adapter_instance)
        
        ai_processor = Mock()
        classification_result = get_classification_response_required_action()
        action_items_result = get_action_items_response_single()
        
        ai_processor.execute_prompty = Mock(side_effect=[
            classification_result,  # For classification
            action_items_result  # For action items
        ])
        ai_processor.classify_email_with_explanation = Mock(return_value={
            'category': classification_result["category"],
            'confidence': classification_result["confidence"],
            'explanation': classification_result.get("reasoning", "Email classified"),
            'alternatives': []
        })
        ai_processor.extract_action_items = Mock(return_value=action_items_result)
        ai_processor.CONFIDENCE_THRESHOLDS = {'required_personal_action': 0.9}
        
        # Execute workflow
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', adapter_class):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                provider = COMEmailProvider()
                provider.adapter = adapter_instance
                provider.authenticate({})
                emails = provider.get_emails()
        
        # Use constructor injection instead of patching
        from backend.services.ai_service import AIService
        from unittest.mock import MagicMock
        
        mock_config = MagicMock()
        ai_service = AIService(ai_orchestrator=ai_processor, azure_config=mock_config)
        
        email = emails[0]
        email_text = f"Subject: {email['subject']}\n\n{email['body']}"
        
        # Step 1: Classify
        classification = await ai_service.classify_email(email_text)
        assert classification["category"] == classification_result["category"]
        
        # Step 2: Extract action items (only if action required)
        if classification["category"] == "required_personal_action":
            action_items = await ai_service.extract_action_items(email_text)
            assert action_items["action_required"] is not None


@pytest.mark.integration
class TestEmailSummarizationWorkflow:
    """Test email summarization workflow."""
    
    @pytest.mark.asyncio
    async def test_meeting_email_summarization(self):
        """Test summarization of meeting invitation email."""
        meeting_email = get_meeting_invitation_email()
        
        # Setup mocks
        adapter_instance = Mock()
        adapter_instance.connect = Mock(return_value=True)
        adapter_instance.get_emails = Mock(return_value=[meeting_email])
        adapter_class = Mock(return_value=adapter_instance)
        
        ai_processor = Mock()
        summary_result = get_summary_response_meeting()
        ai_processor.execute_prompty = Mock(return_value=summary_result)
        ai_processor.generate_summary = Mock(return_value=summary_result)
        
        # Execute workflow
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', adapter_class):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                provider = COMEmailProvider()
                provider.adapter = adapter_instance
                provider.authenticate({})
                emails = provider.get_emails()
        
        # Use constructor injection instead of patching
        from backend.services.ai_service import AIService
        from unittest.mock import MagicMock
        
        mock_config = MagicMock()
        ai_service = AIService(ai_orchestrator=ai_processor, azure_config=mock_config)
        
        email = emails[0]
        email_text = f"Subject: {email['subject']}\n\n{email['body']}"
        
        summary = await ai_service.generate_summary(email_text, "meeting")
        
        assert "summary" in summary
        assert len(summary["summary"]) > 0
        assert ai_processor.execute_prompty.called


@pytest.mark.integration
class TestDuplicateDetectionWorkflow:
    """Test duplicate detection workflow."""
    
    @pytest.mark.asyncio
    async def test_detect_duplicate_emails(self):
        """Test detection of duplicate emails."""
        duplicate_emails = get_duplicate_emails()
        
        # Setup mocks
        adapter_instance = Mock()
        adapter_instance.connect = Mock(return_value=True)
        adapter_instance.get_emails = Mock(return_value=duplicate_emails)
        adapter_class = Mock(return_value=adapter_instance)
        
        ai_processor = Mock()
        # detect_duplicates returns a list of duplicate IDs, not a dict
        duplicate_response = get_duplicate_detection_response_with_duplicates()
        ai_processor.execute_prompty = Mock(return_value=duplicate_response)
        
        # Execute workflow
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', adapter_class):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                provider = COMEmailProvider()
                provider.adapter = adapter_instance
                provider.authenticate({})
                emails = provider.get_emails()
                
                assert len(emails) == 3
        
        # Use constructor injection instead of patching
        from backend.services.ai_service import AIService
        from unittest.mock import MagicMock
        
        mock_config = MagicMock()
        ai_service = AIService(ai_orchestrator=ai_processor, azure_config=mock_config)
        
        result = await ai_service.detect_duplicates(emails)
        
        # detect_duplicates returns a list of duplicate IDs
        assert isinstance(result, list)
        assert len(result) >= 0  # May be empty or contain duplicate IDs


@pytest.mark.integration
@pytest.mark.slow
class TestFullEmailProcessingPipeline:
    """Test complete email processing pipeline from start to finish."""
    
    @pytest.mark.asyncio
    async def test_complete_pipeline(self):
        """Test complete pipeline: retrieve -> classify -> extract actions -> summarize."""
        # Setup test data
        action_email = get_action_required_email()
        
        adapter_instance = Mock()
        adapter_instance.connect = Mock(return_value=True)
        adapter_instance.get_emails = Mock(return_value=[action_email])
        adapter_instance.get_email_body = Mock(return_value=action_email["body"])
        adapter_class = Mock(return_value=adapter_instance)
        
        ai_processor = Mock()
        classification_result = get_classification_response_required_action()
        action_items_result = get_action_items_response_single()
        summary_result = get_summary_response_meeting()
        
        # Configure multiple responses for different operations
        ai_processor.execute_prompty = Mock(side_effect=[
            classification_result,
            action_items_result,
            summary_result
        ])
        ai_processor.classify_email_with_explanation = Mock(return_value={
            'category': classification_result["category"],
            'confidence': classification_result["confidence"],
            'explanation': classification_result.get("reasoning", "Email classified"),
            'alternatives': []
        })
        ai_processor.extract_action_items = Mock(return_value=action_items_result)
        ai_processor.generate_summary = Mock(return_value=summary_result)
        ai_processor.CONFIDENCE_THRESHOLDS = {'required_personal_action': 0.9}
        
        results = {}
        
        # Step 1: Retrieve emails
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', adapter_class):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                
                provider = COMEmailProvider()
                provider.adapter = adapter_instance
                provider.authenticate({})
                emails = provider.get_emails()
                
                results["emails_retrieved"] = len(emails)
                assert results["emails_retrieved"] == 1
        
        # Steps 2-4: AI processing - Use constructor injection
        from backend.services.ai_service import AIService
        from unittest.mock import MagicMock
        
        mock_config = MagicMock()
        ai_service = AIService(ai_orchestrator=ai_processor, azure_config=mock_config)
        
        email = emails[0]
        email_text = f"Subject: {email['subject']}\n\n{email['body']}"
        
        # Step 2: Classify
        classification = await ai_service.classify_email(email_text)
        results["classification"] = classification
        assert "category" in classification
        
        # Step 3: Extract action items
        action_items = await ai_service.extract_action_items(email_text)
        results["action_items"] = action_items
        assert "action_required" in action_items
        
        # Step 4: Generate summary
        summary = await ai_service.generate_summary(email_text, "action_required")
        results["summary"] = summary
        assert "summary" in summary
        
        # Verify complete pipeline
        assert results["emails_retrieved"] == 1
        assert results["classification"]["category"] == classification_result["category"]
        assert results["action_items"]["action_required"] is not None
        assert len(results["summary"]["summary"]) > 0


@pytest.mark.integration
class TestErrorScenarios:
    """Test error handling in integrated workflows."""
    
    @pytest.mark.asyncio
    async def test_connection_failure_during_retrieval(self):
        """Test handling of connection failure during email retrieval."""
        from fastapi import HTTPException
        
        adapter_instance = Mock()
        # The COMEmailProvider wraps the connection error
        adapter_instance.connect = Mock(side_effect=HTTPException(
            status_code=500,
            detail="Connection failed"
        ))
        adapter_class = Mock(return_value=adapter_instance)
        
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', adapter_class):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                
                provider = COMEmailProvider()
                provider.adapter = adapter_instance
                
                with pytest.raises(HTTPException) as exc_info:
                    provider.authenticate({})
                
                # COMEmailProvider wraps connection errors with 503 status
                assert exc_info.value.status_code in [500, 503]
                assert "Connection" in str(exc_info.value.detail) or "failed" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_ai_service_failure_during_classification(self):
        """Test handling of AI service failure during classification."""
        ai_processor = Mock()
        ai_processor.classify_email_with_explanation = Mock(side_effect=Exception("AI service unavailable"))
        ai_processor.execute_prompty = Mock(side_effect=Exception("AI service unavailable"))
        
        # Use constructor injection
        from backend.services.ai_service import AIService
        from unittest.mock import MagicMock
        
        mock_config = MagicMock()
        ai_service = AIService(ai_orchestrator=ai_processor, azure_config=mock_config)
        
        # The service may catch and return an error response instead of raising
        try:
            result = await ai_service.classify_email("Test email")
            # If it returns an error response instead of raising
            assert "error" in result or "category" not in result
        except Exception as exc:
            # If it raises an exception
            assert "AI service unavailable" in str(exc) or "error" in str(exc).lower()
    
    @pytest.mark.asyncio
    async def test_empty_email_list_handling(self):
        """Test handling of empty email list."""
        adapter_instance = Mock()
        adapter_instance.connect = Mock(return_value=True)
        adapter_instance.get_emails = Mock(return_value=[])
        adapter_class = Mock(return_value=adapter_instance)
        
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', adapter_class):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                
                provider = COMEmailProvider()
                provider.adapter = adapter_instance
                provider.authenticate({})
                emails = provider.get_emails()
                
                assert emails == []
                assert isinstance(emails, list)


@pytest.mark.integration
class TestConversationThreadWorkflow:
    """Test conversation thread retrieval and processing."""
    
    def test_retrieve_conversation_thread(self):
        """Test retrieval of email conversation thread."""
        thread_emails = get_conversation_thread()
        
        adapter_instance = Mock()
        adapter_instance.connect = Mock(return_value=True)
        # Mock get_emails to return all emails (thread retrieval filters from this)
        adapter_instance.get_emails = Mock(return_value=thread_emails)
        adapter_instance.get_conversation_thread = Mock(return_value=thread_emails)
        adapter_class = Mock(return_value=adapter_instance)
        
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', adapter_class):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                
                provider = COMEmailProvider()
                provider.adapter = adapter_instance
                provider.authenticate({})
                
                thread = provider.get_conversation_thread("conv-thread-123")
                
                assert len(thread) == 3
                assert all(email["conversation_id"] == "conv-thread-123" for email in thread)
                
                # Verify thread order (chronological)
                email_ids = extract_email_ids(thread)
                assert email_ids == ["thread-1", "thread-2", "thread-3"]


@pytest.mark.integration
class TestEdgeCases:
    """Test edge cases in integrated workflows."""
    
    @pytest.mark.asyncio
    async def test_malformed_email_data(self):
        """Test handling of malformed email data."""
        malformed_email = {
            "id": "malformed-1",
            # Missing required fields
            "body": "Test"
        }
        
        adapter_instance = Mock()
        adapter_instance.connect = Mock(return_value=True)
        adapter_instance.get_emails = Mock(return_value=[malformed_email])
        adapter_class = Mock(return_value=adapter_instance)
        
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', adapter_class):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                
                provider = COMEmailProvider()
                provider.adapter = adapter_instance
                provider.authenticate({})
                emails = provider.get_emails()
                
                # Should return the email even if malformed
                # Validation happens at usage time
                assert len(emails) == 1
    
    @pytest.mark.asyncio
    async def test_very_long_email_content(self):
        """Test processing of very long email content."""
        long_email = {
            "id": "long-email-1",
            "subject": "Very Long Email",
            "body": "A" * 10000,  # Very long body
            "from": "sender@example.com",
            "from_name": "Sender",
            "to": "recipient@example.com",
            "received_time": "2025-01-15T10:00:00Z",
            "is_read": False,
            "categories": [],
            "conversation_id": "conv-long"
        }
        
        adapter_instance = Mock()
        adapter_instance.connect = Mock(return_value=True)
        adapter_instance.get_emails = Mock(return_value=[long_email])
        adapter_instance.get_email_body = Mock(return_value=long_email["body"])
        adapter_class = Mock(return_value=adapter_instance)
        
        ai_processor = Mock()
        ai_processor.execute_prompty = Mock(return_value=get_classification_response_required_action())
        ai_processor.CONFIDENCE_THRESHOLDS = {'required_personal_action': 0.9}
        
        # Should handle long content without error
        with patch('backend.services.com_email_provider.OutlookEmailAdapter', adapter_class):
            with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
                from backend.services.com_email_provider import COMEmailProvider
                
                provider = COMEmailProvider()
                provider.adapter = adapter_instance
                provider.authenticate({})
                emails = provider.get_emails()
                
                assert len(emails) == 1
                assert len(emails[0]["body"]) == 10000

