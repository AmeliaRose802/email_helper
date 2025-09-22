"""
GUI Components Package for Email Helper

This package contains modular GUI components extracted from the monolithic
unified_gui.py to improve maintainability and separation of concerns.
"""

# Component base class
from .base_component import BaseComponent

# Individual GUI components
from .progress_component import ProgressComponent

__all__ = [
    'BaseComponent',
    'ProgressComponent'
]