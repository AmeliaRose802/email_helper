#!/usr/bin/env python3
"""
Action Panel Component for Email Helper GUI

Manages action buttons, controls, and user interaction elements.
Extracted from unified_gui.py to improve modularity.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, List, Callable, Optional

from .base_component import BaseComponent


class ActionPanelComponent(BaseComponent):
    """Component for managing action buttons and controls."""
    
    def __init__(self, parent: tk.Widget, config: Dict[str, Any] = None):
        """
        Initialize the action panel component.
        
        Args:
            parent: Parent tkinter widget
            config: Configuration dictionary with options:
                - buttons: List of button configurations
                - layout: 'horizontal' or 'vertical' (default: 'horizontal')
                - padding: Padding around buttons (default: 5)
                - button_spacing: Space between buttons (default: 5)
                - frame_style: Frame style options
        """
        super().__init__(parent, config)
        
        # Button storage
        self.buttons: Dict[str, ttk.Button] = {}
        self.button_configs: List[Dict[str, Any]] = self.get_config('buttons', [])
        
        # Layout settings
        self.layout = self.get_config('layout', 'horizontal')
        self.padding = self.get_config('padding', 5)
        self.button_spacing = self.get_config('button_spacing', 5)
        
    def create_widget(self) -> tk.Widget:
        """Create the action panel widget."""
        # Create main frame
        frame_style = self.get_config('frame_style', {})
        main_frame = ttk.Frame(self.parent, **frame_style)
        
        # Create buttons based on configuration
        self._create_buttons(main_frame)
        
        return main_frame
        
    def _create_buttons(self, parent_frame: tk.Widget) -> None:
        """Create buttons based on configuration."""
        for i, button_config in enumerate(self.button_configs):
            button = self._create_single_button(parent_frame, button_config)
            
            if self.layout == 'horizontal':
                button.pack(side=tk.LEFT, padx=self.button_spacing)
            else:  # vertical
                button.pack(pady=self.button_spacing)
                
    def _create_single_button(self, parent: tk.Widget, config: Dict[str, Any]) -> ttk.Button:
        """Create a single button from configuration."""
        button_id = config.get('id', f'button_{len(self.buttons)}')
        text = config.get('text', 'Button')
        command = config.get('command')
        state = config.get('state', tk.NORMAL)
        
        # Create button
        button = ttk.Button(
            parent,
            text=text,
            command=lambda: self._handle_button_click(button_id, command),
            state=state
        )
        
        # Apply additional button styling if provided
        button_style = config.get('style', {})
        if button_style:
            for key, value in button_style.items():
                if hasattr(button, key):
                    setattr(button, key, value)
                    
        # Store button reference
        self.buttons[button_id] = button
        
        return button
        
    def _handle_button_click(self, button_id: str, command: Optional[Callable]) -> None:
        """Handle button click events."""
        # Emit button click event
        self.emit_event('button_clicked', {
            'button_id': button_id,
            'button': self.buttons[button_id]
        })
        
        # Execute command if provided
        if command and callable(command):
            try:
                command()
            except Exception as e:
                self.emit_event('button_error', {
                    'button_id': button_id,
                    'error': str(e)
                })
                
    def update_data(self, data: Dict[str, Any]) -> None:
        """
        Update action panel with new data.
        
        Args:
            data: Dictionary containing:
                - button_states: Dict of {button_id: state}
                - button_texts: Dict of {button_id: text}
                - enable_buttons: List of button IDs to enable
                - disable_buttons: List of button IDs to disable
        """
        # Update button states
        if 'button_states' in data:
            for button_id, state in data['button_states'].items():
                self.set_button_state(button_id, state)
                
        # Update button texts
        if 'button_texts' in data:
            for button_id, text in data['button_texts'].items():
                self.set_button_text(button_id, text)
                
        # Enable specific buttons
        if 'enable_buttons' in data:
            for button_id in data['enable_buttons']:
                self.enable_button(button_id)
                
        # Disable specific buttons
        if 'disable_buttons' in data:
            for button_id in data['disable_buttons']:
                self.disable_button(button_id)
                
    def add_button(self, button_id: str, text: str, command: Optional[Callable] = None, 
                   state: str = tk.NORMAL, **kwargs) -> ttk.Button:
        """
        Add a new button to the panel.
        
        Args:
            button_id: Unique button identifier
            text: Button text
            command: Button command function
            state: Initial button state
            **kwargs: Additional button configuration
            
        Returns:
            Created button widget
        """
        button_config = {
            'id': button_id,
            'text': text,
            'command': command,
            'state': state,
            **kwargs
        }
        
        # Add to configuration and recreate widget
        self.button_configs.append(button_config)
        
        # If widget already exists, recreate it
        if self.widget:
            # Clear existing buttons
            for widget in self.widget.winfo_children():
                widget.destroy()
            self.buttons.clear()
            
            # Recreate all buttons
            self._create_buttons(self.widget)
            
        return self.buttons.get(button_id)
        
    def remove_button(self, button_id: str) -> bool:
        """
        Remove a button from the panel.
        
        Args:
            button_id: Button identifier to remove
            
        Returns:
            True if button was removed, False if not found
        """
        if button_id in self.buttons:
            # Remove from widget
            self.buttons[button_id].destroy()
            del self.buttons[button_id]
            
            # Remove from configuration
            self.button_configs = [
                config for config in self.button_configs
                if config.get('id') != button_id
            ]
            
            return True
        return False
        
    def set_button_state(self, button_id: str, state: str) -> bool:
        """
        Set the state of a specific button.
        
        Args:
            button_id: Button identifier
            state: New button state (tk.NORMAL, tk.DISABLED, etc.)
            
        Returns:
            True if state was set, False if button not found
        """
        if button_id in self.buttons:
            self.buttons[button_id].config(state=state)
            return True
        return False
        
    def set_button_text(self, button_id: str, text: str) -> bool:
        """
        Set the text of a specific button.
        
        Args:
            button_id: Button identifier
            text: New button text
            
        Returns:
            True if text was set, False if button not found
        """
        if button_id in self.buttons:
            self.buttons[button_id].config(text=text)
            return True
        return False
        
    def enable_button(self, button_id: str) -> bool:
        """Enable a specific button."""
        return self.set_button_state(button_id, tk.NORMAL)
        
    def disable_button(self, button_id: str) -> bool:
        """Disable a specific button."""
        return self.set_button_state(button_id, tk.DISABLED)
        
    def get_button(self, button_id: str) -> Optional[ttk.Button]:
        """Get a button widget by ID."""
        return self.buttons.get(button_id)
        
    def get_all_buttons(self) -> Dict[str, ttk.Button]:
        """Get all button widgets."""
        return self.buttons.copy()
        
    def enable_all_buttons(self) -> None:
        """Enable all buttons in the panel."""
        for button in self.buttons.values():
            button.config(state=tk.NORMAL)
            
    def disable_all_buttons(self) -> None:
        """Disable all buttons in the panel."""
        for button in self.buttons.values():
            button.config(state=tk.DISABLED)
            
    def set_button_command(self, button_id: str, command: Callable) -> bool:
        """
        Set the command for a specific button.
        
        Args:
            button_id: Button identifier
            command: New command function
            
        Returns:
            True if command was set, False if button not found
        """
        if button_id in self.buttons:
            self.buttons[button_id].config(
                command=lambda: self._handle_button_click(button_id, command)
            )
            
            # Update configuration
            for config in self.button_configs:
                if config.get('id') == button_id:
                    config['command'] = command
                    break
                    
            return True
        return False
        
    @classmethod
    def create_processing_panel(cls, parent: tk.Widget, start_command: Callable, 
                              cancel_command: Callable, dashboard_command: Callable) -> 'ActionPanelComponent':
        """
        Create a processing control panel with standard buttons.
        
        Args:
            parent: Parent widget
            start_command: Start processing command
            cancel_command: Cancel processing command
            dashboard_command: Open dashboard command
            
        Returns:
            Configured ActionPanelComponent
        """
        config = {
            'buttons': [
                {
                    'id': 'start_processing',
                    'text': 'Start Processing',
                    'command': start_command,
                    'state': tk.NORMAL
                },
                {
                    'id': 'cancel_processing',
                    'text': 'Cancel',
                    'command': cancel_command,
                    'state': tk.DISABLED
                },
                {
                    'id': 'accuracy_dashboard',
                    'text': '📊 Accuracy Dashboard',
                    'command': dashboard_command,
                    'state': tk.NORMAL
                }
            ],
            'layout': 'horizontal',
            'padding': 20
        }
        
        return cls(parent, config)
        
    @classmethod
    def create_editing_panel(cls, parent: tk.Widget, apply_outlook_command: Callable,
                           generate_summary_command: Callable) -> 'ActionPanelComponent':
        """
        Create an editing control panel with standard buttons.
        
        Args:
            parent: Parent widget
            apply_outlook_command: Apply to Outlook command
            generate_summary_command: Generate summary command
            
        Returns:
            Configured ActionPanelComponent
        """
        config = {
            'buttons': [
                {
                    'id': 'apply_to_outlook',
                    'text': 'Apply to Outlook',
                    'command': apply_outlook_command,
                    'state': tk.NORMAL
                },
                {
                    'id': 'generate_summary',
                    'text': 'Generate Summary',
                    'command': generate_summary_command,
                    'state': tk.NORMAL
                }
            ],
            'layout': 'horizontal',
            'padding': (15, 0)
        }
        
        return cls(parent, config)
        
    @classmethod
    def create_accuracy_panel(cls, parent: tk.Widget, refresh_command: Callable,
                            export_command: Callable) -> 'ActionPanelComponent':
        """
        Create an accuracy dashboard panel with standard buttons.
        
        Args:
            parent: Parent widget
            refresh_command: Refresh data command
            export_command: Export data command
            
        Returns:
            Configured ActionPanelComponent
        """
        config = {
            'buttons': [
                {
                    'id': 'refresh_accuracy',
                    'text': '🔄 Refresh',
                    'command': refresh_command,
                    'state': tk.NORMAL
                },
                {
                    'id': 'export_csv',
                    'text': '📤 Export CSV',
                    'command': export_command,
                    'state': tk.NORMAL
                }
            ],
            'layout': 'horizontal'
        }
        
        return cls(parent, config)