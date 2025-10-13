#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enhanced text widget with clickable links and rich formatting.

Provides a ScrolledText widget with built-in support for:
- Clickable hyperlinks
- Rich text formatting with tags
- Smooth updates and animations
- Email body display with automatic link detection
"""

import tkinter as tk
from tkinter import scrolledtext
import re
from ..theme import ModernTheme
from ..helpers import find_urls_in_text, open_url


class RichTextWidget(scrolledtext.ScrolledText):
    """Enhanced scrolledtext widget with rich text support.
    
    Features:
    - Automatic link detection and clickable links
    - Pre-configured text tags for common formatting
    - Email-specific formatting helpers
    - Smooth text updates
    
    Attributes:
        link_tags (dict): Map of link tags to their URLs
    """
    
    def __init__(self, parent, **kwargs):
        """Initialize the rich text widget.
        
        Args:
            parent: Parent widget
            **kwargs: Additional arguments passed to ScrolledText
        """
        # Set defaults
        kwargs.setdefault('wrap', tk.WORD)
        kwargs.setdefault('font', ('Segoe UI', 10))
        
        super().__init__(parent, **kwargs)
        
        # Track link tags
        self.link_tags = {}
        
        # Configure text tags
        self._configure_text_tags()
    
    def _configure_text_tags(self):
        """Configure rich text formatting tags."""
        # Header styles
        self.tag_configure("header", 
                          font=("Arial", 10, "bold"), 
                          foreground=ModernTheme.TEXT)
        
        self.tag_configure("main_title", 
                          font=("Segoe UI", 14, "bold"), 
                          foreground=ModernTheme.PRIMARY,
                          justify="center")
        
        self.tag_configure("subtitle", 
                          font=("Segoe UI", 10), 
                          foreground=ModernTheme.TEXT_SECONDARY,
                          justify="center")
        
        # Content styles
        self.tag_configure("summary", 
                          font=("Arial", 9), 
                          background=ModernTheme.SURFACE,
                          foreground=ModernTheme.TEXT)
        
        self.tag_configure("separator", 
                          font=("Courier", 8), 
                          foreground=ModernTheme.BORDER)
        
        self.tag_configure("body", 
                          font=("Arial", 9), 
                          foreground=ModernTheme.TEXT)
        
        # Metadata and labels
        self.tag_configure("metadata", 
                          font=("Arial", 8, "italic"), 
                          foreground=ModernTheme.TEXT_SECONDARY)
        
        self.tag_configure("content_label", 
                          font=("Arial", 9, "bold"), 
                          foreground=ModernTheme.TEXT_SECONDARY)
        
        self.tag_configure("content_text", 
                          font=("Arial", 9), 
                          foreground=ModernTheme.TEXT)
        
        # Link style
        self.tag_configure("link", 
                          font=("Arial", 9, "underline"), 
                          foreground=ModernTheme.PRIMARY)
        
        self.tag_bind("link", "<Enter>", lambda e: self.config(cursor="hand2"))
        self.tag_bind("link", "<Leave>", lambda e: self.config(cursor=""))
        
        # Section headers with backgrounds
        self.tag_configure("section_required", 
                          font=("Segoe UI", 11, "bold"), 
                          foreground=ModernTheme.ERROR,
                          background=ModernTheme.ERROR_LIGHT)
        
        self.tag_configure("section_team", 
                          font=("Segoe UI", 11, "bold"), 
                          foreground="#CA5010",
                          background="#FFF9F5")
        
        self.tag_configure("section_optional", 
                          font=("Segoe UI", 11, "bold"), 
                          foreground=ModernTheme.PRIMARY,
                          background=ModernTheme.PRIMARY_LIGHT)
        
        # Item titles
        self.tag_configure("item_title", 
                          font=("Segoe UI", 11, "bold"), 
                          foreground=ModernTheme.TEXT)
        
        self.tag_configure("item_title_completed", 
                          font=("Segoe UI", 11, "bold"), 
                          foreground=ModernTheme.SUCCESS)
        
        self.tag_configure("item_meta", 
                          font=("Segoe UI", 9), 
                          foreground=ModernTheme.TEXT_SECONDARY)
        
        # Status indicators
        self.tag_configure("completion_status", 
                          font=("Segoe UI", 10, "bold"), 
                          foreground=ModernTheme.SUCCESS)
        
        self.tag_configure("completion_note", 
                          font=("Segoe UI", 9, "italic"), 
                          foreground=ModernTheme.TEXT_SECONDARY)
        
        # Priority colors
        self.tag_configure("error", 
                          font=("Arial", 9, "bold"), 
                          foreground=ModernTheme.ERROR)
        
        self.tag_configure("warning", 
                          font=("Arial", 9, "bold"), 
                          foreground=ModernTheme.WARNING)
        
        # Empty state
        self.tag_configure("empty_section", 
                          font=("Segoe UI", 10, "italic"), 
                          foreground=ModernTheme.TEXT_TERTIARY,
                          justify="center")
    
    def insert_with_links(self, text, base_tag="body"):
        """Insert text with automatic link detection.
        
        Args:
            text (str): Text to insert (may contain URLs)
            base_tag (str): Base formatting tag to apply
        """
        # Find all URLs in the text
        urls = find_urls_in_text(text)
        
        # Insert text with clickable links
        last_pos = 0
        for url_info in urls:
            # Insert text before the URL
            text_before = text[last_pos:url_info['start']]
            self.insert(tk.END, text_before, base_tag)
            
            # Insert clickable URL
            link_tag = f"url_{id(url_info['url'])}"
            self.link_tags[link_tag] = url_info['url']
            
            link_start = self.index(tk.END)
            self.insert(tk.END, url_info['display_url'], (base_tag, "link", link_tag))
            link_end = self.index(tk.END)
            
            # Bind click handler
            self.tag_bind(link_tag, "<Button-1>", 
                         lambda e, url=url_info['url']: open_url(url))
            
            last_pos = url_info['end']
        
        # Insert remaining text
        remaining_text = text[last_pos:]
        self.insert(tk.END, remaining_text, base_tag)
    
    def insert_clickable_link(self, text, url_or_callback, tag="link"):
        """Insert a clickable link with custom handler.
        
        Args:
            text (str): Display text for the link
            url_or_callback: URL string or callback function
            tag (str): Base tag to apply
        """
        link_tag = f"custom_link_{id(url_or_callback)}"
        
        link_start = self.index(tk.END)
        self.insert(tk.END, text, (tag, link_tag))
        link_end = self.index(tk.END)
        
        # Configure link appearance
        self.tag_config(link_tag, foreground=ModernTheme.PRIMARY, underline=True)
        
        # Bind click handler
        if callable(url_or_callback):
            self.tag_bind(link_tag, "<Button-1>", url_or_callback)
        else:
            self.tag_bind(link_tag, "<Button-1>", 
                         lambda e, url=url_or_callback: open_url(url))
        
        # Bind hover effects
        self.tag_bind(link_tag, "<Enter>", lambda e: self.config(cursor="hand2"))
        self.tag_bind(link_tag, "<Leave>", lambda e: self.config(cursor=""))
    
    def smooth_clear(self):
        """Clear the widget smoothly."""
        current_state = self.cget('state')
        self.config(state=tk.NORMAL)
        self.delete(1.0, tk.END)
        self.config(state=current_state)
    
    def smooth_update(self, text, delay=0):
        """Update text smoothly with optional delay.
        
        Args:
            text (str): New text content
            delay (int): Delay in milliseconds before update
        """
        def update():
            current_state = self.cget('state')
            self.config(state=tk.NORMAL)
            self.delete(1.0, tk.END)
            self.insert(tk.END, text)
            self.config(state=current_state)
        
        if delay > 0:
            self.after(delay, update)
        else:
            update()
