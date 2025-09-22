#!/usr/bin/env python3
"""
UI Service for Email Helper

Manages UI state, component coordination, and user interaction flows.
Provides centralized UI state management and component communication.
"""

import tkinter as tk
from typing import Dict, Any, Optional, Callable, List
import logging

logger = logging.getLogger(__name__)


class UIService:
    """Service for managing UI state and component coordination."""
    
    def __init__(self):
        """Initialize the UI service."""
        self.state: Dict[str, Any] = {}
        self.components: Dict[str, Any] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.ui_callbacks: Dict[str, Callable] = {}
        
    def register_component(self, name: str, component: Any) -> None:
        """
        Register a GUI component.
        
        Args:
            name: Component name/identifier
            component: Component instance
        """
        self.components[name] = component
        logger.info(f"Registered component: {name}")
        
    def get_component(self, name: str) -> Optional[Any]:
        """
        Get a registered component.
        
        Args:
            name: Component name
            
        Returns:
            Component instance or None if not found
        """
        return self.components.get(name)
        
    def set_state(self, key: str, value: Any) -> None:
        """
        Set a UI state value.
        
        Args:
            key: State key
            value: State value
        """
        old_value = self.state.get(key)
        self.state[key] = value
        
        # Notify components of state change
        self.emit_event('state_changed', {
            'key': key,
            'value': value,
            'old_value': old_value
        })
        
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get a UI state value.
        
        Args:
            key: State key
            default: Default value if key not found
            
        Returns:
            State value or default
        """
        return self.state.get(key, default)
        
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register an event handler.
        
        Args:
            event_type: Type of event
            handler: Handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    def emit_event(self, event_type: str, data: Any = None) -> None:
        """
        Emit an event to all registered handlers.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")
                    
    def register_ui_callback(self, callback_type: str, callback: Callable) -> None:
        """
        Register a UI callback function.
        
        Args:
            callback_type: Type of callback
            callback: Callback function
        """
        self.ui_callbacks[callback_type] = callback
        
    def execute_ui_callback(self, callback_type: str, *args, **kwargs) -> Any:
        """
        Execute a registered UI callback.
        
        Args:
            callback_type: Type of callback
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Callback result or None
        """
        if callback_type in self.ui_callbacks:
            try:
                return self.ui_callbacks[callback_type](*args, **kwargs)
            except Exception as e:
                logger.error(f"Error executing UI callback {callback_type}: {e}")
                return None
        else:
            logger.warning(f"UI callback not found: {callback_type}")
            return None
            
    def enable_tab(self, tab_index: int, notebook: tk.Widget) -> None:
        """
        Enable a notebook tab.
        
        Args:
            tab_index: Index of tab to enable
            notebook: Notebook widget
        """
        try:
            notebook.tab(tab_index, state="normal")
            self.emit_event('tab_enabled', {'index': tab_index})
        except Exception as e:
            logger.error(f"Error enabling tab {tab_index}: {e}")
            
    def disable_tab(self, tab_index: int, notebook: tk.Widget) -> None:
        """
        Disable a notebook tab.
        
        Args:
            tab_index: Index of tab to disable
            notebook: Notebook widget
        """
        try:
            notebook.tab(tab_index, state="disabled")
            self.emit_event('tab_disabled', {'index': tab_index})
        except Exception as e:
            logger.error(f"Error disabling tab {tab_index}: {e}")
            
    def select_tab(self, tab_index: int, notebook: tk.Widget) -> None:
        """
        Select a notebook tab.
        
        Args:
            tab_index: Index of tab to select
            notebook: Notebook widget
        """
        try:
            notebook.select(tab_index)
            self.emit_event('tab_selected', {'index': tab_index})
        except Exception as e:
            logger.error(f"Error selecting tab {tab_index}: {e}")
            
    def update_component_data(self, component_name: str, data: Dict[str, Any]) -> None:
        """
        Update a component with new data.
        
        Args:
            component_name: Name of component to update
            data: Data to pass to component
        """
        component = self.get_component(component_name)
        if component and hasattr(component, 'update_data'):
            try:
                component.update_data(data)
                self.emit_event('component_updated', {
                    'component': component_name,
                    'data': data
                })
            except Exception as e:
                logger.error(f"Error updating component {component_name}: {e}")
        else:
            logger.warning(f"Component not found or no update_data method: {component_name}")
            
    def coordinate_processing_flow(self, step: str, data: Any = None) -> None:
        """
        Coordinate UI flow during processing.
        
        Args:
            step: Processing step name
            data: Step data
        """
        flow_map = {
            'start_processing': self._handle_start_processing,
            'processing_complete': self._handle_processing_complete,
            'processing_error': self._handle_processing_error,
            'reset_ui': self._handle_reset_ui
        }
        
        if step in flow_map:
            try:
                flow_map[step](data)
            except Exception as e:
                logger.error(f"Error in processing flow step {step}: {e}")
        else:
            logger.warning(f"Unknown processing flow step: {step}")
            
    def _handle_start_processing(self, data: Any) -> None:
        """Handle start of processing flow."""
        self.set_state('processing', True)
        self.emit_event('processing_started', data)
        
    def _handle_processing_complete(self, data: Any) -> None:
        """Handle completion of processing flow."""
        self.set_state('processing', False)
        self.set_state('processing_complete', True)
        self.emit_event('processing_completed', data)
        
    def _handle_processing_error(self, data: Any) -> None:
        """Handle processing error."""
        self.set_state('processing', False)
        self.set_state('processing_error', True)
        self.emit_event('processing_error', data)
        
    def _handle_reset_ui(self, data: Any) -> None:
        """Handle UI reset."""
        self.set_state('processing', False)
        self.set_state('processing_complete', False)
        self.set_state('processing_error', False)
        self.emit_event('ui_reset', data)
        
    def get_ui_state_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current UI state.
        
        Returns:
            Dictionary with UI state information
        """
        return {
            'state': self.state.copy(),
            'components': list(self.components.keys()),
            'event_handlers': {k: len(v) for k, v in self.event_handlers.items()},
            'callbacks': list(self.ui_callbacks.keys())
        }