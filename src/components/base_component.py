#!/usr/bin/env python3
"""
Base Component for Email Helper GUI Components

Provides a consistent interface and common functionality for all GUI components.
"""

import tkinter as tk
from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional


class BaseComponent(ABC):
    """Base class for all GUI components with standard interface."""
    
    def __init__(self, parent: tk.Widget, config: Dict[str, Any] = None):
        """
        Initialize the base component.
        
        Args:
            parent: Parent tkinter widget
            config: Configuration dictionary for the component
        """
        self.parent = parent
        self.config = config or {}
        self.callbacks: Dict[str, Callable] = {}
        self.widget: Optional[tk.Widget] = None
        self._is_initialized = False
        
    @abstractmethod
    def create_widget(self) -> tk.Widget:
        """Create and return the main widget for this component."""
        pass
        
    @abstractmethod
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update component with new data."""
        pass
        
    def initialize(self) -> tk.Widget:
        """Initialize the component and return its main widget."""
        if not self._is_initialized:
            self.widget = self.create_widget()
            self._is_initialized = True
        return self.widget
        
    def register_callback(self, event_name: str, callback: Callable) -> None:
        """Register a callback for component events."""
        self.callbacks[event_name] = callback
        
    def emit_event(self, event_name: str, data: Any = None) -> None:
        """Emit an event to registered callbacks."""
        if event_name in self.callbacks:
            try:
                self.callbacks[event_name](data)
            except Exception as e:
                print(f"Error in callback for {event_name}: {e}")
                
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value with optional default."""
        return self.config.get(key, default)
        
    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.config[key] = value
        
    def destroy(self) -> None:
        """Clean up component resources."""
        if self.widget and hasattr(self.widget, 'destroy'):
            self.widget.destroy()
        self.callbacks.clear()
        self._is_initialized = False