#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Base class for GUI tab components.

Provides common functionality for all tab components including:
- Lifecycle management
- Status updates
- Data loading and refreshing
- Error handling
"""

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod


class BaseTab(ABC):
    """Base class for all GUI tab components.
    
    Each tab should extend this class and implement:
    - create_ui(): Build the tab's UI components
    - on_show(): Called when tab becomes visible
    - on_hide(): Called when tab is hidden
    
    Attributes:
        parent: Parent widget (usually a ttk.Notebook)
        services: ServiceFactory or dict of service dependencies
        frame: Main ttk.Frame for this tab
    """
    
    def __init__(self, parent, services):
        """Initialize the tab component.
        
        Args:
            parent: Parent widget (ttk.Notebook)
            services: Service dependencies (ServiceFactory or dict)
        """
        self.parent = parent
        self.services = services
        self.frame = ttk.Frame(parent)
        self._visible = False
        
        # Create UI components
        self.create_ui()
    
    @abstractmethod
    def create_ui(self):
        """Create the tab's UI components.
        
        This method must be implemented by subclasses to build their UI.
        """
        pass
    
    def on_show(self):
        """Called when the tab becomes visible.
        
        Override this to perform actions when tab is shown (e.g., refresh data).
        """
        self._visible = True
    
    def on_hide(self):
        """Called when the tab is hidden.
        
        Override this to perform cleanup when tab is hidden.
        """
        self._visible = False
    
    def is_visible(self):
        """Check if the tab is currently visible.
        
        Returns:
            bool: True if tab is visible
        """
        return self._visible
    
    def get_frame(self):
        """Get the main frame for this tab.
        
        Returns:
            ttk.Frame: The tab's frame widget
        """
        return self.frame
    
    def update_status(self, message):
        """Update the status bar with a message.
        
        Args:
            message (str): Status message to display
        """
        if hasattr(self.services, 'status_callback') and callable(self.services.status_callback):
            self.services.status_callback(message)
    
    def show_error(self, title, message):
        """Show an error dialog.
        
        Args:
            title (str): Error dialog title
            message (str): Error message to display
        """
        from tkinter import messagebox
        messagebox.showerror(title, message)
    
    def show_info(self, title, message):
        """Show an info dialog.
        
        Args:
            title (str): Info dialog title
            message (str): Info message to display
        """
        from tkinter import messagebox
        messagebox.showinfo(title, message)
    
    def show_warning(self, title, message):
        """Show a warning dialog.
        
        Args:
            title (str): Warning dialog title
            message (str): Warning message to display
        """
        from tkinter import messagebox
        messagebox.showwarning(title, message)
    
    def ask_yes_no(self, title, message):
        """Show a yes/no confirmation dialog.
        
        Args:
            title (str): Dialog title
            message (str): Question to ask user
            
        Returns:
            bool: True if user clicked Yes
        """
        from tkinter import messagebox
        return messagebox.askyesno(title, message)
