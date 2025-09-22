"""
GUI Components Package for Email Helper

This package contains modular GUI components extracted from the monolithic
unified_gui.py to improve maintainability and separation of concerns.
"""

# Component base class
from .base_component import BaseComponent

# Individual GUI components
from .progress_component import ProgressComponent
from .email_tree_component import EmailTreeComponent
from .action_panel_component import ActionPanelComponent
from .summary_display_component import SummaryDisplayComponent

__all__ = [
    'BaseComponent',
    'ProgressComponent',
    'EmailTreeComponent',
    'ActionPanelComponent',
    'SummaryDisplayComponent'
]