#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Progress bar widget with smooth animations and percentage display.

Provides an enhanced progress bar with:
- Smooth animation
- Percentage text overlay
- Task status display
- Configurable styling
"""

import tkinter as tk
from tkinter import ttk
from ..theme import ModernTheme


class AnimatedProgressBar(ttk.Frame):
    """Enhanced progress bar with animations and text overlay.
    
    Features:
    - Smooth progress animations
    - Percentage display
    - Status text
    - Indeterminate mode support
    
    Attributes:
        progress_bar (ttk.Progressbar): The actual progress bar
        status_label (ttk.Label): Status text label
        percentage_label (ttk.Label): Percentage text label
    """
    
    def __init__(self, parent, **kwargs):
        """Initialize the animated progress bar.
        
        Args:
            parent: Parent widget
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        
        # Create progress bar
        self.progress_bar = ttk.Progressbar(
            self,
            mode='determinate',
            length=400,
            style='Custom.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(pady=(0, 5))
        
        # Create status label
        self.status_label = ttk.Label(
            self,
            text="",
            font=("Segoe UI", 9),
            foreground=ModernTheme.TEXT_SECONDARY
        )
        self.status_label.pack()
        
        # Create percentage label (overlay)
        self.percentage_label = ttk.Label(
            self,
            text="0%",
            font=("Segoe UI", 9, "bold"),
            foreground=ModernTheme.TEXT
        )
        # Position over progress bar
        self.percentage_label.place(relx=0.5, rely=0.0, anchor='n')
        
        # Animation variables
        self._target_value = 0
        self._animation_id = None
    
    def set_progress(self, value, status_text="", animate=True):
        """Set progress value with optional animation.
        
        Args:
            value (float): Progress value (0-100)
            status_text (str): Optional status text to display
            animate (bool): Whether to animate the transition
        """
        # Clamp value
        value = max(0, min(100, value))
        
        # Update status text if provided
        if status_text:
            self.status_label.config(text=status_text)
        
        # Update percentage display
        self.percentage_label.config(text=f"{int(value)}%")
        
        if animate:
            self._animate_to(value)
        else:
            self.progress_bar['value'] = value
    
    def _animate_to(self, target_value):
        """Animate progress bar to target value.
        
        Args:
            target_value (float): Target progress value
        """
        # Cancel any existing animation
        if self._animation_id:
            self.after_cancel(self._animation_id)
        
        current_value = self.progress_bar['value']
        
        # Calculate step
        diff = target_value - current_value
        if abs(diff) < 0.5:
            # Close enough, snap to target
            self.progress_bar['value'] = target_value
            self._animation_id = None
            return
        
        # Smooth animation step
        step = diff * 0.2  # 20% of remaining distance
        new_value = current_value + step
        
        self.progress_bar['value'] = new_value
        
        # Schedule next frame
        self._animation_id = self.after(20, lambda: self._animate_to(target_value))
    
    def start_indeterminate(self, status_text="Processing..."):
        """Start indeterminate progress mode.
        
        Args:
            status_text (str): Status text to display
        """
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(10)
        self.status_label.config(text=status_text)
        self.percentage_label.config(text="")
    
    def stop_indeterminate(self):
        """Stop indeterminate progress mode."""
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
        self.progress_bar['value'] = 0
    
    def reset(self):
        """Reset progress bar to initial state."""
        # Cancel animations
        if self._animation_id:
            self.after_cancel(self._animation_id)
            self._animation_id = None
        
        # Reset values
        self.progress_bar['value'] = 0
        self.percentage_label.config(text="0%")
        self.status_label.config(text="")
    
    def complete(self, status_text="Complete!"):
        """Set progress to 100% and show completion message.
        
        Args:
            status_text (str): Completion message
        """
        self.set_progress(100, status_text, animate=True)
