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
            from backend.services.com_email_provider import COMEmailProvider
            
            logger.info("Initializing COM email provider")
            _com_email_provider = COMEmailProvider()
            
            # Authenticate/connect to Outlook
            if not _com_email_provider.authenticate({}):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to connect to Outlook COM interface"
                )
            
            logger.info("COM email provider initialized successfully")
            
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
    
    Returns singleton instance of COMAIService that wraps AIProcessor
    for COM-based AI operations using Azure OpenAI.
    
    The service is lazily initialized on first use. Subsequent calls
    return the same instance.
    
    Returns:
        COMAIService: COM AI service instance
        
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
            from backend.services.com_ai_service import COMAIService
            
            logger.info("Initializing COM AI service")
            _com_ai_service = COMAIService()
            
            # Test initialization by ensuring AI components are available
            _com_ai_service._ensure_initialized()
            
            logger.info("COM AI service initialized successfully")
            
        except ImportError as e:
            logger.error(f"COM AI service not available: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="COM AI service not available. Check AI dependencies."
            )
        except Exception as e:
            logger.error(f"Failed to initialize COM AI service: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"COM AI service initialization failed: {str(e)}"
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
                logger.info("Using COM email provider (configured)")
                _email_provider = get_com_email_provider()
                return _email_provider
            except HTTPException as e:
                logger.warning(f"COM provider unavailable, falling back: {e.detail}")
        
        # Fall back to existing provider selection logic
        try:
            from backend.services.email_provider import get_email_provider_instance
            logger.info("Using standard email provider selection")
            _email_provider = get_email_provider_instance()
        except Exception as e:
            logger.error(f"Failed to initialize email provider: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email provider initialization failed"
            )
    
    return _email_provider


def get_ai_service():
    """FastAPI dependency for AI service with configuration-based selection.
    
    Selects AI service based on configuration settings:
    1. COM AI service if use_com_backend is True
    2. Standard AI service for general use
    
    This function provides backward compatibility while enabling COM
    AI service selection through configuration.
    
    Returns:
        AIService or COMAIService: Selected AI service instance
        
    Raises:
        HTTPException: If no service can be initialized
        
    Example:
        >>> from fastapi import Depends
        >>> @router.post("/classify")
        >>> async def classify(service = Depends(get_ai_service)):
        >>>     return await service.classify_email(email_text)
    """
    global _ai_service
    
    if _ai_service is None:
        # Check for COM AI service preference
        if getattr(settings, 'use_com_backend', False):
            try:
                logger.info("Using COM AI service (configured)")
                _ai_service = get_com_ai_service()
                return _ai_service
            except HTTPException as e:
                logger.warning(f"COM AI service unavailable, falling back: {e.detail}")
        
        # Fall back to standard AI service
        try:
            from backend.services.ai_service import AIService
            logger.info("Using standard AI service")
            _ai_service = AIService()
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service initialization failed"
            )
    
    return _ai_service


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
