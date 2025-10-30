"""Dependency injection functions for FastAPI Email Helper API.

This module provides dependency injection functions for COM adapters,
enabling clean integration of COM email provider and AI service with
FastAPI endpoints through the Depends() pattern.

The module handles:
- Provider selection based on configuration
- Singleton pattern for adapter instances
- Graceful error handling for adapter initialization
- Backward compatibility with existing providers
"""

import logging
from typing import Optional
from fastapi import HTTPException, status

from backend.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Import provider classes at module level for test mocking
# These imports are optional and will fail gracefully if not available
COMEmailProvider = None
COMAIService = None
AIService = None
get_email_provider_instance = None

try:
    from backend.services.com_email_provider import COMEmailProvider
except ImportError:
    logger.debug("COMEmailProvider not available")

try:
    from backend.services.com_ai_service import COMAIService
except ImportError:
    logger.debug("COMAIService not available")

try:
    from backend.services.ai_service import AIService
except ImportError:
    logger.debug("AIService not available")

try:
    from backend.services.email_provider import get_email_provider_instance
except ImportError:
    logger.debug("get_email_provider_instance not available")

# Global singleton instances
_com_email_provider: Optional[object] = None
_com_ai_service: Optional[object] = None
_email_provider: Optional[object] = None
_ai_service: Optional[object] = None


def get_com_email_provider():
    """FastAPI dependency for COM email provider.
    
    Returns singleton instance of COMEmailProvider that wraps
    OutlookEmailAdapter for COM-based email operations.
    
    The provider is automatically connected to Outlook on first use.
    Subsequent calls return the same connected instance.
    
    Returns:
        COMEmailProvider: Connected COM email provider instance
        
    Raises:
        HTTPException: If COM provider cannot be initialized or connected
        
    Example:
        >>> from fastapi import Depends
        >>> @router.get("/emails")
        >>> async def get_emails(provider = Depends(get_com_email_provider)):
        >>>     return provider.get_emails("Inbox", count=50)
    """
    global _com_email_provider
    
    if _com_email_provider is None:
        try:
            # Use module-level COMEmailProvider if available, otherwise try import
            provider_class = COMEmailProvider
            if provider_class is None:
                from backend.services.com_email_provider import COMEmailProvider as ImportedProvider
                provider_class = ImportedProvider
            
            logger.info("Initializing COM email provider")
            _com_email_provider = provider_class()
            
            # Authenticate/connect to Outlook with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if _com_email_provider.authenticate({}):
                        logger.info("COM email provider initialized successfully")
                        break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"COM connection attempt {attempt + 1} failed, retrying...")
                        import time
                        time.sleep(0.5)
                    else:
                        raise
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to connect to Outlook COM interface after retries"
                )
            
        except ImportError as e:
            logger.error(f"COM email provider not available: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="COM email provider not available. Requires Windows and pywin32."
            )
        except Exception as e:
            logger.error(f"Failed to initialize COM email provider: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"COM email provider initialization failed: {str(e)}"
            )
    
    return _com_email_provider


def get_com_ai_service():
    """FastAPI dependency for COM AI service.
    
    Returns singleton instance of AIService for AI operations using Azure OpenAI.
    
    The service is lazily initialized on first use. Subsequent calls
    return the same instance.
    
    Returns:
        AIService: AI service instance
        
    Raises:
        HTTPException: If AI service cannot be initialized
        
    Example:
        >>> from fastapi import Depends
        >>> @router.post("/classify")
        >>> async def classify(service = Depends(get_com_ai_service)):
        >>>     return await service.classify_email("Subject: Test")
    """
    global _com_ai_service
    
    if _com_ai_service is None:
        try:
            # Use module-level AIService if available, otherwise try import
            service_class = AIService
            if service_class is None:
                from backend.services.ai_service import AIService as ImportedAIService
                service_class = ImportedAIService
            
            logger.info("Initializing AI service")
            _com_ai_service = service_class()
            
            # Test initialization by ensuring AI components are available
            _com_ai_service._ensure_initialized()
            
            logger.info("AI service initialized successfully")
            
        except ImportError as e:
            logger.error(f"AI service not available: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service not available. Check AI dependencies."
            )
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI service initialization failed: {str(e)}"
            )
    
    return _com_ai_service


def get_email_provider():
    """FastAPI dependency for email provider with configuration-based selection.
    
    Selects email provider based on configuration settings:
    1. COM provider if use_com_backend is True (Windows + Outlook)
    2. Graph API provider if credentials are configured
    3. Mock provider for development/testing
    
    This function provides backward compatibility while enabling COM
    provider selection through configuration.
    
    Returns:
        EmailProvider: Selected email provider instance
        
    Raises:
        HTTPException: If no provider can be initialized
        
    Example:
        >>> from fastapi import Depends
        >>> @router.get("/emails")
        >>> async def get_emails(provider = Depends(get_email_provider)):
        >>>     return provider.get_emails("Inbox")
    """
    global _email_provider
    
    if _email_provider is None:
        # Check for COM provider preference
        if getattr(settings, 'use_com_backend', False):
            try:
                logger.info("Attempting to use COM email provider...")
                _email_provider = get_com_email_provider()
                logger.info("COM email provider initialized successfully")
                return _email_provider
            except HTTPException as e:
                logger.warning(f"COM provider unavailable: {e.detail}")
                logger.info("Falling back to alternative email provider...")
            except Exception as e:
                logger.error(f"COM provider error: {str(e)}")
                logger.info("Falling back to alternative email provider...")
        
        # Fall back to existing provider selection logic
        try:
            # Use module-level function if available, otherwise try import
            provider_factory = get_email_provider_instance
            if provider_factory is None:
                from backend.services.email_provider import get_email_provider_instance as ImportedFactory
                provider_factory = ImportedFactory
            logger.info("Using standard email provider selection")
            _email_provider = provider_factory()
        except Exception as e:
            logger.error(f"Failed to initialize email provider: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email provider initialization failed"
            )
    
    return _email_provider


def get_ai_service():
    """FastAPI dependency for AI service.
    
    Returns singleton instance of AIService for AI operations.
    
    Returns:
        AIService: AI service instance
        
    Raises:
        HTTPException: If no service can be initialized
    """
    return get_com_ai_service()


def get_task_service():
    """FastAPI dependency for task service.
    
    Returns:
        TaskService: Task service instance
    """
    from backend.services.task_service import TaskService
    return TaskService()


def get_email_processing_service():
    """FastAPI dependency for email processing service.
    
    Returns EmailProcessingService that coordinates between:
    - EmailSyncService: Database operations
    - EmailClassificationService: AI classification
    - EmailTaskExtractionService: Task extraction
    - EmailAccuracyService: Accuracy tracking
    
    Returns:
        EmailProcessingService: Email processing coordinator
        
    Example:
        >>> from fastapi import Depends
        >>> @router.post("/emails/sync")
        >>> async def sync_emails(service = Depends(get_email_processing_service)):
        >>>     return await service.sync_emails_to_database(emails)
    """
    from backend.services.email_processing_service import EmailProcessingService
    
    ai_service = get_ai_service()
    email_provider = get_email_provider()
    task_service = get_task_service()
    
    return EmailProcessingService(ai_service, email_provider, task_service)


def reset_dependencies():
    """Reset all singleton instances for testing purposes.
    
    This function is primarily used in tests to ensure clean state
    between test cases.
    """
    global _com_email_provider, _com_ai_service, _email_provider, _ai_service
    
    _com_email_provider = None
    _com_ai_service = None
    _email_provider = None
    _ai_service = None
    
    logger.debug("All dependency singletons reset")
