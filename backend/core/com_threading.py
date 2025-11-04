"""COM threading utilities for safe multi-threaded COM operations.

This module provides utilities for managing COM threading in multi-threaded
environments like FastAPI + Uvicorn. COM objects are apartment-threaded and
must be created and accessed from the same thread.

Key Patterns:
    - Initialize COM per-thread (not per-process)
    - Reconnect COM adapters when crossing thread boundaries
    - Handle COM exceptions gracefully
    - Avoid Unicode encoding errors in console output
"""

import logging
import sys
import io
from functools import wraps
from typing import Any, Callable, TypeVar, cast

logger = logging.getLogger(__name__)

# Check if pythoncom is available
try:
    import pythoncom
    PYTHONCOM_AVAILABLE = True
except ImportError:
    PYTHONCOM_AVAILABLE = False
    pythoncom = None

# Type variable for generic functions
F = TypeVar('F', bound=Callable[..., Any])


def init_com_thread() -> bool:
    """Initialize COM for the current thread.

    Returns:
        bool: True if initialization successful or already initialized
    """
    if not PYTHONCOM_AVAILABLE:
        return False

    try:
        pythoncom.CoInitialize()
        return True
    except Exception as e:
        # Already initialized or initialization failed
        logger.debug(f"COM initialization: {e}")
        return True  # Treat as success if already initialized


def uninit_com_thread() -> None:
    """Uninitialize COM for the current thread."""
    if not PYTHONCOM_AVAILABLE:
        return

    try:
        pythoncom.CoUninitialize()
    except Exception as e:
        logger.debug(f"COM uninitialization: {e}")


def com_thread_safe(func: F) -> F:
    """Decorator to ensure COM is initialized for the current thread.

    This decorator:
    1. Initializes COM on the current thread if needed
    2. Executes the wrapped function
    3. Handles COM exceptions gracefully

    Usage:
        @com_thread_safe
        def my_com_operation(self):
            # COM operations here
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Initialize COM on this thread
        init_com_thread()

        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Check if it's a COM threading error
            error_msg = str(e).lower()
            if 'marshalled for a different thread' in error_msg:
                logger.error(
                    f"COM threading error in {func.__name__}: {e}. "
                    "COM object was accessed from wrong thread."
                )
            raise

    return cast(F, wrapper)


class SafeConsoleOutput:
    """Context manager for safe console output that handles Unicode encoding.

    Windows console has limited character encoding support. This context
    manager temporarily replaces stdout/stderr with UTF-8 capable streams.

    Usage:
        with SafeConsoleOutput():
            print("Some text with Unicode: 你好")
    """

    def __init__(self):
        self.original_stdout = None
        self.original_stderr = None

    def __enter__(self):
        """Replace stdout/stderr with UTF-8 capable streams."""
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # Create UTF-8 capable streams with error handling
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding='utf-8',
            errors='replace',
            line_buffering=True
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer,
            encoding='utf-8',
            errors='replace',
            line_buffering=True
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original stdout/stderr."""
        if self.original_stdout:
            sys.stdout = self.original_stdout
        if self.original_stderr:
            sys.stderr = self.original_stderr


def safe_print(msg: str, logger_instance: logging.Logger = None) -> None:
    """Print message safely, handling Unicode encoding errors.

    Args:
        msg: Message to print
        logger_instance: Optional logger to use instead of print
    """
    if logger_instance:
        # Use logger if provided (safer for production)
        logger_instance.info(msg)
    else:
        # Try to print, fallback to ASCII if Unicode fails
        try:
            print(msg)
        except UnicodeEncodeError:
            # Strip non-ASCII characters and try again
            ascii_msg = msg.encode('ascii', errors='replace').decode('ascii')
            print(ascii_msg)


def setup_console_encoding() -> None:
    """Set up console encoding to handle Unicode characters.

    Call this at application startup to configure console encoding.
    This helps prevent 'charmap' codec errors on Windows.
    """
    # Try to set UTF-8 encoding for stdout/stderr
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        logger.info("Console encoding configured for UTF-8")
    except Exception as e:
        logger.warning(f"Could not configure console encoding: {e}")


# Auto-setup console encoding when module is imported
setup_console_encoding()
