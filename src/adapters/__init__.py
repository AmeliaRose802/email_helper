"""Adapters package for Email Helper.

This package contains adapter classes that wrap existing components
to provide standardized interfaces for different parts of the system.
"""

from .outlook_email_adapter import OutlookEmailAdapter

__all__ = ['OutlookEmailAdapter']
