#!/usr/bin/env python3
"""
Notification Service for Email Helper

Handles user notifications, feedback messages, and status updates.
Provides a centralized way to communicate with users.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional, Callable, Dict, Any
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing user notifications and feedback."""
    
    def __init__(self, status_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the notification service.
        
        Args:
            status_callback: Optional callback function to update status bar
        """
        self.status_callback = status_callback
        self.notification_handlers: Dict[str, Callable] = {}
        
    def register_status_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback for status updates."""
        self.status_callback = callback
        
    def register_notification_handler(self, event_type: str, handler: Callable) -> None:
        """Register a handler for specific notification types."""
        self.notification_handlers[event_type] = handler
        
    def show_status(self, message: str) -> None:
        """
        Display a status message.
        
        Args:
            message: Status message to display
        """
        logger.info(f"Status: {message}")
        if self.status_callback:
            try:
                self.status_callback(message)
            except Exception as e:
                logger.error(f"Error updating status: {e}")
                
    def show_info(self, title: str, message: str, parent: Optional[tk.Widget] = None) -> None:
        """
        Show an information dialog.
        
        Args:
            title: Dialog title
            message: Information message
            parent: Parent widget for the dialog
        """
        logger.info(f"Info dialog: {title} - {message}")
        try:
            messagebox.showinfo(title, message, parent=parent)
        except Exception as e:
            logger.error(f"Error showing info dialog: {e}")
            
    def show_warning(self, title: str, message: str, parent: Optional[tk.Widget] = None) -> None:
        """
        Show a warning dialog.
        
        Args:
            title: Dialog title
            message: Warning message
            parent: Parent widget for the dialog
        """
        logger.warning(f"Warning dialog: {title} - {message}")
        try:
            messagebox.showwarning(title, message, parent=parent)
        except Exception as e:
            logger.error(f"Error showing warning dialog: {e}")
            
    def show_error(self, title: str, message: str, parent: Optional[tk.Widget] = None) -> None:
        """
        Show an error dialog.
        
        Args:
            title: Dialog title
            message: Error message
            parent: Parent widget for the dialog
        """
        logger.error(f"Error dialog: {title} - {message}")
        try:
            messagebox.showerror(title, message, parent=parent)
        except Exception as e:
            logger.error(f"Error showing error dialog: {e}")
            
    def ask_yes_no(self, title: str, message: str, parent: Optional[tk.Widget] = None) -> bool:
        """
        Show a yes/no confirmation dialog.
        
        Args:
            title: Dialog title
            message: Question message
            parent: Parent widget for the dialog
            
        Returns:
            True if user clicked Yes, False otherwise
        """
        logger.info(f"Yes/No dialog: {title} - {message}")
        try:
            return messagebox.askyesno(title, message, parent=parent)
        except Exception as e:
            logger.error(f"Error showing yes/no dialog: {e}")
            return False
            
    def ask_ok_cancel(self, title: str, message: str, parent: Optional[tk.Widget] = None) -> bool:
        """
        Show an OK/Cancel confirmation dialog.
        
        Args:
            title: Dialog title
            message: Question message
            parent: Parent widget for the dialog
            
        Returns:
            True if user clicked OK, False otherwise
        """
        logger.info(f"OK/Cancel dialog: {title} - {message}")
        try:
            return messagebox.askokcancel(title, message, parent=parent)
        except Exception as e:
            logger.error(f"Error showing OK/Cancel dialog: {e}")
            return False
            
    def notify_processing_complete(self, result_summary: str) -> None:
        """
        Notify user that processing is complete.
        
        Args:
            result_summary: Summary of processing results
        """
        self.show_status("Processing complete")
        if 'processing_complete' in self.notification_handlers:
            try:
                self.notification_handlers['processing_complete'](result_summary)
            except Exception as e:
                logger.error(f"Error in processing complete handler: {e}")
                
    def notify_error(self, error_type: str, error_message: str, show_dialog: bool = True) -> None:
        """
        Notify user of an error.
        
        Args:
            error_type: Type/category of error
            error_message: Detailed error message
            show_dialog: Whether to show an error dialog
        """
        status_msg = f"Error: {error_type}"
        self.show_status(status_msg)
        
        if show_dialog:
            self.show_error("Error", f"{error_type}:\n\n{error_message}")
            
        if 'error' in self.notification_handlers:
            try:
                self.notification_handlers['error']({
                    'type': error_type,
                    'message': error_message
                })
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
                
    def notify_progress(self, progress: float, message: str) -> None:
        """
        Notify of progress update.
        
        Args:
            progress: Progress percentage (0-100)
            message: Progress message
        """
        self.show_status(message)
        
        if 'progress' in self.notification_handlers:
            try:
                self.notification_handlers['progress']({
                    'progress': progress,
                    'message': message
                })
            except Exception as e:
                logger.error(f"Error in progress handler: {e}")
                
    def clear_status(self) -> None:
        """Clear the status message."""
        self.show_status("Ready")