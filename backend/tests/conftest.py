"""Pytest configuration and shared fixtures for backend tests.

This module provides shared fixtures and test configuration for COM adapter testing,
including mock objects, sample data, and common test utilities.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List


# ============================================================================
# Mock OutlookManager Fixtures
# ============================================================================

@pytest.fixture
def mock_outlook_manager():
    """Create a mock OutlookManager for testing.
    
    This fixture provides a mock OutlookManager with pre-configured
    responses for common operations like connecting, getting emails, etc.
    
    Returns:
        Mock: Configured mock OutlookManager instance
    """
    manager = Mock()
    manager.connect = Mock(return_value=True)
    manager.get_emails = Mock(return_value=[])
    manager.get_folder_emails = Mock(return_value=[])
    manager.is_connected = True
    manager.disconnect = Mock()
    return manager


@pytest.fixture
def mock_outlook_adapter():
    """Create a mock OutlookEmailAdapter for COM provider testing.
    
    This fixture provides a mock adapter that simulates the OutlookEmailAdapter
    behavior used by COMEmailProvider.
    
    Returns:
        tuple: (adapter_class, adapter_instance) for patching
    """
    adapter_instance = Mock()
    adapter_instance.connect = Mock(return_value=True)
    adapter_instance.get_emails = Mock(return_value=[])
    adapter_instance.get_email_body = Mock(return_value="Test body")
    adapter_instance.get_folders = Mock(return_value=[])
    adapter_instance.mark_as_read = Mock(return_value=True)
    adapter_instance.move_email = Mock(return_value=True)
    adapter_instance.get_conversation_thread = Mock(return_value=[])
    
    adapter_class = Mock(return_value=adapter_instance)
    return adapter_class, adapter_instance


# ============================================================================
# Mock AIProcessor Fixtures
# ============================================================================

@pytest.fixture
def mock_ai_processor():
    """Create a mock AIProcessor for testing.
    
    This fixture provides a mock AIProcessor with pre-configured
    responses for common AI operations like classification, action items, etc.
    
    Returns:
        Mock: Configured mock AIProcessor instance
    """
    processor = Mock()
    processor.azure_config = {
        "endpoint": "https://test.openai.azure.com/",
        "api_key": "test-api-key",
        "deployment_name": "test-deployment"
    }
    
    # Configure common AI methods
    processor.classify_email = Mock(return_value="required_personal_action")
    processor.classify_email_improved = Mock(return_value="required_personal_action")
    processor.extract_action_items = Mock(return_value={
        "action_required": "Review document",
        "due_date": "Tomorrow",
        "priority": "high",
        "confidence": 0.85
    })
    processor.get_username = Mock(return_value="test_user")
    processor.load_learning_data = Mock(return_value={})
    processor.execute_prompty = Mock(return_value={
        "category": "required_personal_action",
        "confidence": 0.85
    })
    
    # Confidence thresholds
    processor.CONFIDENCE_THRESHOLDS = {
        'optional_action': 0.8,
        'work_relevant': 0.8,
        'required_personal_action': 0.9
    }
    
    return processor





# ============================================================================
# Sample Email Data Fixtures
# ============================================================================

@pytest.fixture
def sample_email_data():
    """Sample email data for testing.
    
    Returns:
        dict: Sample email with common fields
    """
    return {
        "id": "test-email-123",
        "subject": "Test Meeting Request",
        "body": "Please join our team meeting tomorrow at 2 PM to discuss project updates.",
        "from": "manager@company.com",
        "from_name": "Project Manager",
        "to": "user@company.com",
        "received_time": "2025-01-15T10:00:00Z",
        "is_read": False,
        "categories": [],
        "conversation_id": "conv-123"
    }


@pytest.fixture
def sample_email_list():
    """List of sample emails for testing batch operations.
    
    Returns:
        list: List of sample email dictionaries
    """
    base_time = datetime.now()
    return [
        {
            "id": "email-1",
            "subject": "Q4 Report Review Required",
            "body": "Please review the attached Q4 report by Friday.",
            "from": "boss@company.com",
            "from_name": "Manager",
            "to": "user@company.com",
            "received_time": (base_time - timedelta(hours=2)).isoformat(),
            "is_read": False,
            "categories": ["Work"],
            "conversation_id": "conv-1"
        },
        {
            "id": "email-2",
            "subject": "Team Building Event",
            "body": "Join us for a team building event next month!",
            "from": "hr@company.com",
            "from_name": "HR Department",
            "to": "user@company.com",
            "received_time": (base_time - timedelta(hours=5)).isoformat(),
            "is_read": False,
            "categories": [],
            "conversation_id": "conv-2"
        },
        {
            "id": "email-3",
            "subject": "Newsletter: Tech Updates",
            "body": "Check out this month's technology newsletter...",
            "from": "newsletter@techsite.com",
            "from_name": "Tech Newsletter",
            "to": "user@company.com",
            "received_time": (base_time - timedelta(days=1)).isoformat(),
            "is_read": True,
            "categories": ["FYI"],
            "conversation_id": "conv-3"
        }
    ]


@pytest.fixture
def sample_action_item_email():
    """Sample email with action items for testing.
    
    Returns:
        dict: Email containing action items
    """
    return {
        "id": "action-email-456",
        "subject": "Action Required: Budget Approval by EOD",
        "body": """Hi Team,
        
Please review and approve the Q1 budget by end of day today. 
The document is attached and needs your signature.

Key points:
- Review line items for accuracy
- Approve or provide feedback
- Submit by 5 PM today

Thanks,
Finance Team
""",
        "from": "finance@company.com",
        "from_name": "Finance Team",
        "to": "user@company.com",
        "received_time": datetime.now().isoformat(),
        "is_read": False,
        "categories": ["Important"],
        "conversation_id": "conv-action-1"
    }


# ============================================================================
# Sample AI Response Fixtures
# ============================================================================

@pytest.fixture
def sample_classification_response():
    """Sample AI classification response.
    
    Returns:
        dict: Classification result with confidence
    """
    return {
        "category": "required_personal_action",
        "confidence": 0.92,
        "reasoning": "Email requires immediate action from recipient"
    }


@pytest.fixture
def sample_action_items_response():
    """Sample AI action items extraction response.
    
    Returns:
        dict: Action items with details
    """
    return {
        "action_required": "Review and approve Q4 budget",
        "due_date": "2025-01-20",
        "priority": "high",
        "confidence": 0.88,
        "action_items": [
            {
                "task": "Review budget line items",
                "deadline": "2025-01-20",
                "priority": "high"
            },
            {
                "task": "Provide approval or feedback",
                "deadline": "2025-01-20",
                "priority": "high"
            }
        ],
        "links": [
            "https://company.com/budget/q4"
        ]
    }


@pytest.fixture
def sample_summary_response():
    """Sample AI summary generation response.
    
    Returns:
        dict: Email summary
    """
    return {
        "summary": "Team meeting scheduled for tomorrow at 2 PM to discuss project updates.",
        "key_points": [
            "Meeting tomorrow at 2 PM",
            "Topic: Project updates",
            "Attendance expected"
        ],
        "category": "required_personal_action"
    }


@pytest.fixture
def sample_duplicate_detection_response():
    """Sample AI duplicate detection response.
    
    Returns:
        dict: Duplicate email IDs
    """
    return {
        "duplicate_ids": ["email-2", "email-3"],
        "duplicate_groups": [
            {
                "primary": "email-1",
                "duplicates": ["email-2", "email-3"],
                "similarity": 0.95
            }
        ]
    }


# ============================================================================
# COM Provider Fixtures
# ============================================================================

@pytest.fixture
def com_email_provider(mock_outlook_adapter):
    """Create a COM email provider with mocked adapter.
    
    Args:
        mock_outlook_adapter: Mock adapter fixture
        
    Returns:
        COMEmailProvider: Provider instance with mocked dependencies
    """
    adapter_class, adapter_instance = mock_outlook_adapter
    
    with patch('backend.services.com_email_provider.OutlookEmailAdapter', adapter_class):
        with patch('backend.services.com_email_provider.COM_AVAILABLE', True):
            from backend.services.com_email_provider import COMEmailProvider
            provider = COMEmailProvider()
            provider.adapter = adapter_instance
            return provider


@pytest.fixture
def authenticated_com_provider(com_email_provider):
    """Create an authenticated COM email provider.
    
    Args:
        com_email_provider: COM provider fixture
        
    Returns:
        COMEmailProvider: Authenticated provider instance
    """
    com_email_provider.authenticate({})
    return com_email_provider


# ============================================================================
# AI Service Fixtures
# ============================================================================

@pytest.fixture
def com_ai_service():
    """Create a COM AI service instance.
    
    Returns:
        COMAIService: Service instance for testing
    """
    from backend.services.com_ai_service import COMAIService
    return COMAIService()


@pytest.fixture
def initialized_com_ai_service(mock_ai_processor, mock_azure_config_obj):
    """Create an initialized COM AI service with mocked dependencies.
    
    Args:
        mock_ai_processor: Mock AI processor fixture
        mock_azure_config_obj: Mock Azure config fixture
        
    Returns:
        COMAIService: Initialized service instance
    """
    with patch('backend.services.com_ai_service.AIProcessor', return_value=mock_ai_processor):
        with patch('backend.services.com_ai_service.get_azure_config', return_value=mock_azure_config_obj):
            from backend.services.com_ai_service import COMAIService
            service = COMAIService()
            service._ensure_initialized()
            return service


# ============================================================================
# Email Provider Mocking Fixtures
# ============================================================================

@pytest.fixture
def mock_email_provider():
    """Create a mock email provider for testing.
    
    This fixture provides a properly configured mock EmailProvider that can be
    used in tests without requiring a real email backend (COM or Graph API).
    
    Returns:
        Mock: Configured mock EmailProvider instance with EmailProvider spec
    """
    from backend.services.email_provider import EmailProvider
    
    provider = Mock(spec=EmailProvider)
    provider.authenticate = Mock(return_value=True)
    provider.get_emails = Mock(return_value=[])
    provider.get_email_content = Mock(return_value={
        'id': 'test-123',
        'subject': 'Test Email',
        'body': 'Test body',
        'sender': 'test@example.com',
        'received_time': '2025-01-01T10:00:00Z'
    })
    provider.get_email_body = Mock(return_value='Test body')
    provider.get_folders = Mock(return_value=[])
    provider.mark_as_read = Mock(return_value=True)
    provider.move_email = Mock(return_value=True)
    provider.get_conversation_thread = Mock(return_value=[
        {
            "id": "test_email_1",
            "subject": "Test Email 1",
            "sender": "sender1@example.com",
            "body": "Test body 1",
            "date": "2024-01-01T10:00:00"
        }
    ])
    return provider


@pytest.fixture(autouse=True)
def patch_email_provider_factory(mock_email_provider, monkeypatch):
    """Automatically patch email provider factory for all tests.
    
    This fixture prevents RuntimeError from being raised when tests import
    modules that try to initialize email providers. It patches both:
    - backend.services.email_provider.get_email_provider_instance
    - backend.core.dependencies.get_email_provider
    
    Args:
        mock_email_provider: The mock provider fixture
        monkeypatch: pytest monkeypatch fixture
    """
    # Reset the global singletons before patching
    import backend.services.email_provider as ep_module
    import backend.core.dependencies as dep_module
    
    ep_module._email_provider = None
    dep_module._email_provider = None
    dep_module._com_email_provider = None
    
    # Patch the factory function to return mock provider
    monkeypatch.setattr(
        'backend.services.email_provider.get_email_provider_instance',
        lambda: mock_email_provider
    )
    
    # Patch the global in email_provider module
    monkeypatch.setattr(
        'backend.services.email_provider._email_provider',
        mock_email_provider
    )
    
    # Also patch the dependencies module
    monkeypatch.setattr(
        'backend.core.dependencies.get_email_provider',
        lambda: mock_email_provider
    )
    
    # Patch the singleton in dependencies module
    monkeypatch.setattr(
        'backend.core.dependencies._email_provider',
        mock_email_provider
    )


@pytest.fixture
def mock_ai_service():
    """Create a mock AI service for testing.
    
    This fixture provides a properly configured mock AIService that can be
    used in tests without requiring real Azure OpenAI credentials.
    
    Returns:
        Mock: Configured mock AIService instance
    """
    from backend.services.ai_service import AIService
    
    service = Mock(spec=AIService)
    service._ensure_initialized = Mock()
    service.classify_email = AsyncMock(return_value={
        'category': 'work_relevant',
        'confidence': 0.85,
        'reasoning': 'Work-related email',
        'alternatives': ['optional_action']
    })
    service.extract_action_items = AsyncMock(return_value={
        'action_items': ['Review document', 'Submit feedback'],
        'action_required': 'Review and submit feedback',
        'due_date': '2024-01-15',
        'urgency': 'medium',
        'confidence': 0.8,
        'explanation': 'Action required',
        'relevance': 'High',
        'links': []
    })
    service.generate_summary = AsyncMock(return_value={
        'summary': 'Email summary',
        'key_points': ['Point 1', 'Point 2'],
        'confidence': 0.9
    })
    return service


@pytest.fixture
def mock_ai_orchestrator():
    """Create a mock AIOrchestrator for testing.
    
    This fixture provides a properly configured mock AIOrchestrator that
    can be used in tests requiring AI operations. This is NOT auto-used,
    allowing tests to customize the mock as needed.
    
    Returns:
        Mock: Configured mock AIOrchestrator instance
    """
    orchestrator = Mock()
    # Default to work_relevant but tests can override this
    orchestrator.classify_email_with_explanation = Mock(return_value={
        'category': 'work_relevant',
        'confidence': 0.85,
        'reasoning': 'Work-related email',
        'alternatives': []
    })
    orchestrator.execute_prompty = Mock(return_value='{"result": "test"}')
    orchestrator.CONFIDENCE_THRESHOLDS = {
        'optional_action': 0.8,
        'work_relevant': 0.8,
        'required_personal_action': 0.9
    }
    return orchestrator


@pytest.fixture
def mock_azure_config_obj():
    """Create mock Azure configuration object.
    
    Returns:
        Mock: Azure configuration object with required attributes
    """
    config = Mock()
    config.endpoint = "https://test.openai.azure.com/"
    config.api_key = "test-api-key"
    config.deployment_name = "test-deployment"
    config.api_version = "2024-02-15-preview"
    return config


@pytest.fixture(autouse=True)
def patch_ai_service_factory(mock_ai_service, mock_azure_config_obj, monkeypatch):
    """Automatically patch AI service factory for all tests.
    
    This fixture prevents initialization errors when tests import modules
    that try to initialize AI services without Azure credentials.
    
    NOTE: This fixture does NOT auto-patch AIOrchestrator. Tests that need
    to customize AI orchestrator behavior should explicitly patch it in their
    test or use the mock_ai_orchestrator fixture with their own context managers.
    
    Args:
        mock_ai_service: The mock AI service fixture
        mock_azure_config_obj: The mock Azure config fixture
        monkeypatch: pytest monkeypatch fixture
    """
    # Reset the global singletons before patching
    import backend.core.dependencies as dep_module
    
    dep_module._ai_service = None
    
    # Patch the dependencies module functions
    monkeypatch.setattr(
        'backend.core.dependencies.get_ai_service',
        lambda: mock_ai_service
    )
    
    monkeypatch.setattr(
        'backend.core.dependencies.get_com_ai_service',
        lambda: mock_ai_service
    )
    
    # Patch the singleton in dependencies module
    monkeypatch.setattr(
        'backend.core.dependencies._ai_service',
        mock_ai_service
    )
    
    # Patch the API module's imported reference (critical for FastAPI Depends)
    monkeypatch.setattr(
        'backend.api.ai.get_ai_service',
        lambda: mock_ai_service
    )
    
    # Patch get_azure_config for tests that create AIService directly
    monkeypatch.setattr(
        'backend.core.infrastructure.azure_config.get_azure_config',
        lambda: mock_azure_config_obj
    )
    
    # NOTE: We do NOT patch AIOrchestrator here. Tests should explicitly
    # patch it when needed, allowing them to customize the mock behavior.


# ============================================================================
# Test Utility Fixtures
# ============================================================================

@pytest.fixture
def temp_prompts_dir(tmp_path):
    """Create a temporary prompts directory with sample prompty files.
    
    Args:
        tmp_path: pytest temporary path fixture
        
    Returns:
        Path: Path to temporary prompts directory
    """
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    
    # Create sample prompty files
    (prompts_dir / "email_classifier.prompty").write_text("""
---
name: Email Classifier
description: Classify emails into categories
---
Classify this email: {{email_content}}
""")
    
    (prompts_dir / "action_item.prompty").write_text("""
---
name: Action Item Extractor
description: Extract action items from emails
---
Extract action items: {{email_content}}
""")
    
    return prompts_dir


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "com: Tests for COM adapter functionality"
    )
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for component workflows"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take significant time to run"
    )
