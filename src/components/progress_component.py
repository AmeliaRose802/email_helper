#!/usr/bin/env python3
"""
Progress Component for Email Helper GUI

Manages progress bars, status indicators, and processing feedback.
Extracted from unified_gui.py to improve modularity.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, Any

from .base_component import BaseComponent


class ProgressComponent(BaseComponent):
    """Component for displaying progress bars and status information."""
    
    def __init__(self, parent: tk.Widget, config: Dict[str, Any] = None):
        """
        Initialize the progress component.
        
        Args:
            parent: Parent tkinter widget
            config: Configuration dictionary with options:
                - show_text_log: bool (default True) - whether to show scrollable text log
                - progress_height: int (default 15) - height of progress text area
                - max_progress: int (default 100) - maximum progress value
        """
        super().__init__(parent, config)
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready")
        self.progress_bar = None
        self.progress_text = None
        self.status_bar = None
        
    def create_widget(self) -> tk.Widget:
        """Create the progress component widgets."""
        # Create main container frame
        main_frame = ttk.Frame(self.parent)
        
        # Progress bar
        max_progress = self.get_config('max_progress', 100)
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            variable=self.progress_var,
            maximum=max_progress
        )
        self.progress_bar.pack(pady=10, fill=tk.X, padx=20)
        
        # Progress text log (optional)
        if self.get_config('show_text_log', True):
            height = self.get_config('progress_height', 15)
            self.progress_text = scrolledtext.ScrolledText(
                main_frame, 
                height=height,
                state=tk.DISABLED, 
                wrap=tk.WORD
            )
            self.progress_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        return main_frame
        
    def update_data(self, data: Dict[str, Any]) -> None:
        """
        Update progress component with new data.
        
        Args:
            data: Dictionary containing:
                - progress: float (0-100) - progress percentage
                - message: str - status message
                - log_message: str (optional) - message to add to log
        """
        if 'progress' in data:
            self.update_progress(data['progress'], data.get('message', ''))
            
        if 'log_message' in data:
            self.update_progress_text(data['log_message'])
            
        if 'status' in data:
            self.set_status(data['status'])
    
    def update_progress(self, value: float, message: str = '') -> None:
        """
        Update progress bar and status message.
        
        Args:
            value: Progress value (0-100)
            message: Status message to display
        """
        def update_ui():
            self.progress_var.set(value)
            if message:
                self.status_var.set(message)
                
        # Schedule UI update on main thread
        if hasattr(self.parent, 'after'):
            self.parent.after(0, update_ui)
        else:
            # Fallback if parent doesn't have after method
            update_ui()
    
    def update_progress_text(self, message: str) -> None:
        """
        Add a message to the progress text log.
        
        Args:
            message: Message to add to the log
        """
        if not self.progress_text:
            return
            
        def update_ui():
            self.progress_text.config(state=tk.NORMAL)
            self.progress_text.insert(tk.END, message + "\n")
            self.progress_text.see(tk.END)
            self.progress_text.config(state=tk.DISABLED)
            
        # Schedule UI update on main thread
        if hasattr(self.parent, 'after'):
            self.parent.after(0, update_ui)
        else:
            update_ui()
    
    def set_status(self, message: str) -> None:
        """
        Set the status message.
        
        Args:
            message: Status message to display
        """
        self.status_var.set(message)
    
    def get_status(self) -> str:
        """Get the current status message."""
        return self.status_var.get()
    
    def get_progress(self) -> float:
        """Get the current progress value."""
        return self.progress_var.get()
    
    def reset(self) -> None:
        """Reset progress and clear logs."""
        self.progress_var.set(0)
        self.status_var.set("Ready")
        
        if self.progress_text:
            self.progress_text.config(state=tk.NORMAL)
            self.progress_text.delete(1.0, tk.END)
            self.progress_text.config(state=tk.DISABLED)
    
    def create_status_bar(self, parent_window: tk.Widget) -> ttk.Label:
        """
        Create a status bar widget for the main window.
        
        Args:
            parent_window: Parent window widget
            
        Returns:
            Status bar label widget
        """
        self.status_bar = ttk.Label(
            parent_window, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        return self.status_bar
    
    def get_status_var(self) -> tk.StringVar:
        """Get the status StringVar for external binding."""
        return self.status_var
    
    def get_progress_var(self) -> tk.DoubleVar:
        """Get the progress DoubleVar for external binding."""
        return self.progress_var