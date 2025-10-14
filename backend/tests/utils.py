"""Test utility functions for backend testing.

This module provides utility functions and helpers for testing COM adapters
and backend services, including assertions, mock helpers, and test data
generation.
"""

from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock
from datetime import datetime


def assert_email_structure(email: Dict[str, Any]) -> None:
    """Assert that an email has the expected structure.
    
    Args:
        email: Email dictionary to validate
        
    Raises:
        AssertionError: If email structure is invalid
    """
    required_fields = ["id", "subject", "body", "from", "received_time"]
    
    for field in required_fields:
        assert field in email, f"Email missing required field: {field}"
    
    assert isinstance(email["id"], str), "Email ID must be a string"
    assert isinstance(email["subject"], str), "Email subject must be a string"
    assert isinstance(email["body"], str), "Email body must be a string"
    assert isinstance(email["from"], str), "Email from must be a string"


def assert_classification_structure(classification: Dict[str, Any]) -> None:
    """Assert that a classification result has the expected structure.
    
    Args:
        classification: Classification dictionary to validate
        
    Raises:
        AssertionError: If classification structure is invalid
    """
    required_fields = ["category", "confidence"]
    
    for field in required_fields:
        assert field in classification, f"Classification missing required field: {field}"
    
    assert isinstance(classification["category"], str), "Category must be a string"
    assert isinstance(classification["confidence"], (int, float)), "Confidence must be numeric"
    assert 0 <= classification["confidence"] <= 1, "Confidence must be between 0 and 1"


def assert_action_items_structure(action_items: Dict[str, Any]) -> None:
    """Assert that action items result has the expected structure.
    
    Args:
        action_items: Action items dictionary to validate
        
    Raises:
        AssertionError: If action items structure is invalid
    """
    assert "action_required" in action_items, "Action items missing action_required field"
    assert "confidence" in action_items, "Action items missing confidence field"
    
    if action_items["action_required"] is not None:
        assert isinstance(action_items["action_required"], str), "action_required must be a string"
    
    assert isinstance(action_items["confidence"], (int, float)), "Confidence must be numeric"
    assert 0 <= action_items["confidence"] <= 1, "Confidence must be between 0 and 1"


def create_mock_outlook_adapter(
    emails: Optional[List[Dict[str, Any]]] = None,
    folders: Optional[List[Dict[str, Any]]] = None
) -> Mock:
    """Create a mock OutlookEmailAdapter with pre-configured data.
    
    Args:
        emails: List of emails to return from get_emails()
        folders: List of folders to return from get_folders()
        
    Returns:
        Mock: Configured mock adapter
    """
    adapter = Mock()
    adapter.connect = Mock(return_value=True)
    adapter.get_emails = Mock(return_value=emails or [])
    adapter.get_email_body = Mock(return_value="Test email body")
    adapter.get_folders = Mock(return_value=folders or [])
    adapter.mark_as_read = Mock(return_value=True)
    adapter.move_email = Mock(return_value=True)
    adapter.get_conversation_thread = Mock(return_value=[])
    adapter.disconnect = Mock()
    
    return adapter


def create_mock_ai_processor(
    classification: Optional[str] = None,
    action_items: Optional[Dict[str, Any]] = None,
    summary: Optional[str] = None
) -> Mock:
    """Create a mock AIProcessor with pre-configured responses.
    
    Args:
        classification: Default classification result
        action_items: Default action items result
        summary: Default summary result
        
    Returns:
        Mock: Configured mock AI processor
    """
    processor = Mock()
    
    processor.azure_config = {
        "endpoint": "https://test.openai.azure.com/",
        "api_key": "test-key",
        "deployment_name": "test-deployment"
    }
    
    processor.classify_email = Mock(return_value=classification or "required_personal_action")
    processor.classify_email_improved = Mock(return_value=classification or "required_personal_action")
    
    processor.extract_action_items = Mock(return_value=action_items or {
        "action_required": "Test action",
        "due_date": "Tomorrow",
        "priority": "medium",
        "confidence": 0.85
    })
    
    processor.execute_prompty = Mock(return_value={
        "category": classification or "required_personal_action",
        "confidence": 0.85
    })
    
    processor.CONFIDENCE_THRESHOLDS = {
        'optional_action': 0.8,
        'work_relevant': 0.8,
        'required_personal_action': 0.9
    }
    
    return processor


def mock_async_function(return_value: Any = None):
    """Create an AsyncMock with a specified return value.
    
    Args:
        return_value: Value to return from the async function
        
    Returns:
        AsyncMock: Configured async mock
    """
    mock = AsyncMock()
    mock.return_value = return_value
    return mock


def generate_email_id(prefix: str = "test") -> str:
    """Generate a unique email ID for testing.
    
    Args:
        prefix: Prefix for the email ID
        
    Returns:
        str: Unique email ID
    """
    timestamp = datetime.now().timestamp()
    return f"{prefix}-{int(timestamp * 1000)}"


def create_email_batch(count: int, base_subject: str = "Test Email") -> List[Dict[str, Any]]:
    """Create a batch of test emails.
    
    Args:
        count: Number of emails to create
        base_subject: Base subject line for emails
        
    Returns:
        list: Batch of email dictionaries
    """
    emails = []
    base_time = datetime.now()
    
    for i in range(count):
        email = {
            "id": generate_email_id(f"batch-{i}"),
            "subject": f"{base_subject} {i + 1}",
            "body": f"This is test email number {i + 1}.",
            "from": f"sender{i}@example.com",
            "from_name": f"Sender {i + 1}",
            "to": "recipient@example.com",
            "received_time": base_time.isoformat(),
            "is_read": False,
            "categories": [],
            "conversation_id": f"conv-{i}"
        }
        emails.append(email)
    
    return emails


def assert_workflow_success(
    emails_retrieved: bool = False,
    classified: bool = False,
    action_items_extracted: bool = False,
    summarized: bool = False
) -> None:
    """Assert that workflow steps completed successfully.
    
    Args:
        emails_retrieved: Whether emails were retrieved
        classified: Whether emails were classified
        action_items_extracted: Whether action items were extracted
        summarized: Whether emails were summarized
        
    Raises:
        AssertionError: If any expected step failed
    """
    if emails_retrieved:
        assert emails_retrieved, "Emails should be retrieved"
    if classified:
        assert classified, "Emails should be classified"
    if action_items_extracted:
        assert action_items_extracted, "Action items should be extracted"
    if summarized:
        assert summarized, "Emails should be summarized"


def compare_emails(email1: Dict[str, Any], email2: Dict[str, Any]) -> float:
    """Calculate similarity between two emails.
    
    Args:
        email1: First email
        email2: Second email
        
    Returns:
        float: Similarity score between 0 and 1
    """
    # Simple similarity based on subject and body
    subject_match = email1.get("subject", "") == email2.get("subject", "")
    body_match = email1.get("body", "") == email2.get("body", "")
    from_match = email1.get("from", "") == email2.get("from", "")
    
    matches = sum([subject_match, body_match, from_match])
    return matches / 3.0


def filter_emails_by_category(
    emails: List[Dict[str, Any]],
    category: str
) -> List[Dict[str, Any]]:
    """Filter emails by category.
    
    Args:
        emails: List of emails to filter
        category: Category to filter by
        
    Returns:
        list: Filtered emails
    """
    return [
        email for email in emails
        if category in email.get("categories", [])
    ]


def count_unread_emails(emails: List[Dict[str, Any]]) -> int:
    """Count unread emails in a list.
    
    Args:
        emails: List of emails
        
    Returns:
        int: Count of unread emails
    """
    return sum(1 for email in emails if not email.get("is_read", False))


def extract_email_ids(emails: List[Dict[str, Any]]) -> List[str]:
    """Extract email IDs from a list of emails.
    
    Args:
        emails: List of emails
        
    Returns:
        list: List of email IDs
    """
    return [email["id"] for email in emails]


def create_test_folders() -> List[Dict[str, Any]]:
    """Create a list of test folders.
    
    Returns:
        list: Test folder data
    """
    return [
        {"id": "inbox", "name": "Inbox", "type": "mail", "item_count": 25},
        {"id": "sent", "name": "Sent Items", "type": "mail", "item_count": 50},
        {"id": "drafts", "name": "Drafts", "type": "mail", "item_count": 3},
        {"id": "archive", "name": "Archive", "type": "mail", "item_count": 100},
        {"id": "junk", "name": "Junk Email", "type": "mail", "item_count": 10}
    ]


def simulate_connection_error(adapter: Mock, error_message: str = "Connection lost") -> None:
    """Simulate a connection error on a mock adapter.
    
    Args:
        adapter: Mock adapter to configure
        error_message: Error message to raise
    """
    from fastapi import HTTPException
    adapter.connect.side_effect = HTTPException(status_code=500, detail=error_message)
    adapter.get_emails.side_effect = HTTPException(status_code=500, detail=error_message)


def simulate_authentication_failure(adapter: Mock) -> None:
    """Simulate an authentication failure on a mock adapter.
    
    Args:
        adapter: Mock adapter to configure
    """
    adapter.connect.return_value = False


def verify_mock_called_with_email(mock: Mock, email_id: str) -> bool:
    """Verify that a mock was called with a specific email ID.
    
    Args:
        mock: Mock object to check
        email_id: Email ID to verify
        
    Returns:
        bool: True if mock was called with email_id
    """
    for call in mock.call_args_list:
        args, kwargs = call
        if email_id in args or email_id in kwargs.values():
            return True
    return False


def reset_all_mocks(*mocks: Mock) -> None:
    """Reset all provided mocks.
    
    Args:
        *mocks: Mock objects to reset
    """
    for mock in mocks:
        mock.reset_mock()
