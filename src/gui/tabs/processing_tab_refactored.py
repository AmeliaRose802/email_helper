#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Processing Tab - Email processing interface (VIEW ONLY - NO BUSINESS LOGIC)."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox


class ProcessingTab:
    """Email processing tab with controls and progress display.
    
    This is a pure view component that delegates all business logic to controllers.
    """
    
    def __init__(self, parent, on_start_callback, on_cancel_callback, on_dashboard_callback):
        """Initialize processing tab view.
        
        Args:
            parent: Parent widget
            on_start_callback: Callback for start processing button
            on_cancel_callback: Callback for cancel button
            on_dashboard_callback: Callback for dashboard button
        """
        self.parent = parent
        self.on_start_callback = on_start_callback
        self.on_cancel_callback = on_cancel_callback
        self.on_dashboard_callback = on_dashboard_callback
        
        self.email_count_var = tk.StringVar(value="50")
        self.progress_var = tk.DoubleVar()
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create all UI widgets."""
        # Email count selection
        email_count_frame = ttk.Frame(self.parent)
        email_count_frame.pack(pady=20)
        
        ttk.Label(email_count_frame, text="Number of emails:").pack(side=tk.LEFT)
        for count in [25, 50, 100, 200]:
            ttk.Radiobutton(email_count_frame, text=str(count), variable=self.email_count_var, 
                           value=str(count)).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(email_count_frame, text="Other:", variable=self.email_count_var, 
                       value="other").pack(side=tk.LEFT, padx=5)
        
        self.custom_count_entry = ttk.Entry(email_count_frame, width=10)
        self.custom_count_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.custom_count_entry.bind('<KeyPress>', self._on_custom_count_keypress)
        self.custom_count_entry.bind('<FocusIn>', self._on_custom_count_focus)
        
        # Processing controls
        control_frame = ttk.Frame(self.parent)
        control_frame.pack(pady=20)
        
        self.start_btn = ttk.Button(control_frame, text="Start Processing", 
                                    command=self._on_start_clicked,
                                    style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = ttk.Button(control_frame, text="Cancel", 
                                     command=self.on_cancel_callback, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="📊 Accuracy Dashboard", 
                  command=self.on_dashboard_callback).pack(side=tk.LEFT, padx=5)
        
        # Progress
        self.progress_bar = ttk.Progressbar(self.parent, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(pady=10, fill=tk.X, padx=20)
        
        self.progress_text = scrolledtext.ScrolledText(self.parent, height=15, 
                                                      state=tk.DISABLED, wrap=tk.WORD,
                                                      font=('Segoe UI', 10))
        self.progress_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self._add_welcome_message()
    
    def _on_start_clicked(self):
        """Handle start button click - validates input and delegates to callback."""
        selected_option = self.email_count_var.get()
        try:
            if selected_option == "other":
                custom_value = self.custom_count_entry.get().strip()
                if not custom_value:
                    messagebox.showwarning("Missing Input", "Please enter a number in the custom count field.")
                    return
                max_emails = int(custom_value)
            else:
                max_emails = int(selected_option)
            
            if max_emails <= 0:
                messagebox.showwarning("Invalid Input", "Please enter a positive number for email count.")
                return
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid number for email count.")
            return
        
        # Delegate to callback
        self.on_start_callback(max_emails)
    
    def _on_custom_count_keypress(self, event):
        """Handle custom count keypress."""
        self.parent.after_idle(lambda: self.email_count_var.set("other") if self.custom_count_entry.get().strip() else None)
    
    def _on_custom_count_focus(self, event):
        """Handle custom count focus."""
        if self.custom_count_entry.get().strip():
            self.email_count_var.set("other")
    
    def _add_welcome_message(self):
        """Add welcome message to progress text."""
        self.progress_text.config(state=tk.NORMAL)
        welcome_msg = '''Welcome to Email Helper! 🎉

This intelligent email processing system will help you:
• 📧 Analyze your Outlook emails using AI
• 📋 Identify action items and tasks automatically  
• 🎯 Categorize emails by priority and type
• 📊 Generate focused summaries for better productivity

To get started:
1. Select the number of emails to process above
2. Click 'Start Processing' to begin AI analysis
3. Watch this area for detailed progress updates
4. Review and edit results in the next tab when complete

Ready when you are! 🚀'''
        self.progress_text.insert(tk.END, welcome_msg)
        self.progress_text.config(state=tk.DISABLED)
    
    # Public methods for updating UI from controller
    
    def set_buttons_state(self, start_enabled: bool, cancel_enabled: bool):
        """Set button states.
        
        Args:
            start_enabled: Whether start button should be enabled
            cancel_enabled: Whether cancel button should be enabled
        """
        self.start_btn.config(state=tk.NORMAL if start_enabled else tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL if cancel_enabled else tk.DISABLED)
    
    def update_progress(self, percent: float, message: str):
        """Update progress bar and status message.
        
        Args:
            percent: Progress percentage (0-100)
            message: Status message
        """
        self.progress_var.set(percent)
    
    def add_log_message(self, message: str):
        """Add a log message to the progress text.
        
        Args:
            message: Message to add
        """
        self.progress_text.config(state=tk.NORMAL)
        self.progress_text.insert(tk.END, message + "\n")
        self.progress_text.see(tk.END)
        self.progress_text.config(state=tk.DISABLED)
    
    def clear_progress(self):
        """Clear progress text."""
        self.progress_text.config(state=tk.NORMAL)
        self.progress_text.delete(1.0, tk.END)
        self.progress_text.config(state=tk.DISABLED)
        self.progress_var.set(0)
