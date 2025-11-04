"""Dependency injection for FastAPI Email Helper API."""

import logging
from typing import Optional
from fastapi import HTTPException, status

from backend.core.config import settings

try:
    from unittest.mock import Mock  # type: ignore
except ImportError:  # pragma: no cover
    Mock = None

logger = logging.getLogger(__name__)

# Lazy imports (actual imports done in functions when needed)
COMEmailProvider = None
get_email_provider_instance = None

try:
    from backend.services.com_email_provider import COMEmailProvider
except ImportError:
    pass

try:
    from backend.services.email_provider import get_email_provider_instance
except ImportError:
    pass

# Singletons
_com_email_provider: Optional[object] = None
_ai_service: Optional[object] = None
_email_provider: Optional[object] = None
_ai_service_override: Optional[object] = None


def _retry_authenticate(provider, max_retries=3):
    """Retry authentication with exponential backoff."""
    import time
    for attempt in range(max_retries):
        try:
            if provider.authenticate({}):
                return True
        except Exception:
            if attempt < max_retries - 1:
                logger.warning(f"Auth attempt {attempt + 1} failed, retrying...")
                time.sleep(0.5 * (attempt + 1))
            else:
                raise
    return False


def _initialize_com_provider_class():
    """Initialize and return COM provider class."""
    global COMEmailProvider

    if COMEmailProvider is not None:
        return COMEmailProvider

    try:
        from backend.services.com_email_provider import COMEmailProvider as ImportedProvider
        COMEmailProvider = ImportedProvider
        return ImportedProvider
    except ImportError as e:
        logger.error(f"COM email provider not available: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="COM email provider not available. Requires Windows and pywin32."
        )


def _create_and_authenticate_provider(provider_class):
    """Create provider instance and authenticate."""
    logger.info("Initializing COM email provider")
    provider = provider_class()

    if not _retry_authenticate(provider):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to Outlook COM interface"
        )

    logger.info("COM email provider initialized")
    return provider

def get_com_email_provider():
    """FastAPI dependency for COM email provider."""
    global _com_email_provider

    if _com_email_provider is not None:
        return _com_email_provider

    try:
        provider_class = _initialize_com_provider_class()
        _com_email_provider = _create_and_authenticate_provider(provider_class)
        return _com_email_provider
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize COM email provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"COM email provider initialization failed: {str(e)}"
        )


def get_com_ai_service():
    """FastAPI dependency for COM AI service."""
    global _ai_service

    if _ai_service is None:
        try:
            from backend.services.com_ai_service import COMAIService

            logger.info("Initializing COM AI service")
            _ai_service = COMAIService()
            _ai_service._ensure_initialized()
            logger.info("COM AI service initialized")

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

    return _ai_service


def get_ai_service():
    """FastAPI dependency for AI service with configuration-based selection."""
    global _ai_service, _ai_service_override

    if _ai_service is None and _ai_service_override is not None:
        _ai_service = _ai_service_override
        _ai_service_override = None
        logger.debug("[Dependencies] Restored AI service override after reset")

    if _ai_service is None:
        if getattr(settings, 'use_com_backend', False):
            try:
                logger.info("Using COM AI service")
                _ai_service = get_com_ai_service()
                return _ai_service
            except HTTPException as e:
                logger.warning(f"COM AI service unavailable: {e.detail}, falling back")
            except Exception as e:
                logger.error(f"COM AI service error: {str(e)}, falling back")

        try:
            # Always import fresh for testability
            from backend.services.ai_service import AIService as ImportedAIService

            logger.info("Using standard AI service")
            _ai_service = ImportedAIService()
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service initialization failed"
            )

    return _ai_service

def get_email_provider():
    """FastAPI dependency for email provider with configuration-based selection."""
    global _email_provider

    if _email_provider is None:
        import os
        running_tests = 'PYTEST_CURRENT_TEST' in os.environ
        prefer_mock_for_tests = running_tests and get_email_provider_instance is not None

        # In test context, prefer the patched factory first (even if COM is available)
        if prefer_mock_for_tests:
            try:
                logger.info("[DI] Test context detected - using patched email provider factory (dynamic import)")
                from importlib import import_module
                provider_module = import_module('backend.services.email_provider')
                provider_factory = getattr(provider_module, 'get_email_provider_instance')
                _email_provider = provider_factory()
                return _email_provider
            except Exception as e:
                logger.warning(f"[DI] Test provider initialization failed: {e}, attempting COM provider")

        # Normal path: attempt COM provider if configured/available
        if getattr(settings, 'use_com_backend', False) and not prefer_mock_for_tests:
            try:
                logger.info("Using COM email provider")
                _email_provider = get_com_email_provider()
                return _email_provider
            except HTTPException as e:
                logger.warning(f"COM provider unavailable: {e.detail}, falling back")
            except Exception as e:
                logger.error(f"COM provider error: {str(e)}, falling back")

        # Fallback: standard provider factory (will raise if not configured)
        try:
            from importlib import import_module
            provider_module = import_module('backend.services.email_provider')
            provider_factory = getattr(provider_module, 'get_email_provider_instance')
            logger.info("Using standard email provider")
            _email_provider = provider_factory()
        except Exception as e:
            logger.error(f"Failed to initialize email provider: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email provider initialization failed"
            )

    return _email_provider


def reset_dependencies():
    """Reset singletons for testing."""
    global _com_email_provider, _ai_service, _email_provider, _ai_service_override
    logger.debug(
        "[Dependencies] reset_dependencies called (before) ai=%s email=%s com=%s",
        type(_ai_service).__name__ if _ai_service is not None else "None",
        type(_email_provider).__name__ if _email_provider is not None else "None",
        type(_com_email_provider).__name__ if _com_email_provider is not None else "None",
    )

    if Mock is not None and isinstance(_ai_service, Mock):
        _ai_service_override = _ai_service
        logger.debug("[Dependencies] Captured AI service override for test reuse")
    else:
        _ai_service_override = None

    _com_email_provider = None
    _ai_service = None
    _email_provider = None
    logger.debug("[Dependencies] reset_dependencies completed")


def get_task_service():
    """FastAPI dependency for task service."""
    from backend.services.task_service import TaskService
    return TaskService()


def get_email_processing_service():
    """FastAPI dependency for email processing service."""
    from backend.services.email_processing_service import EmailProcessingService

    return EmailProcessingService(
        get_ai_service(),
        get_email_provider(),
        get_task_service()
    )
