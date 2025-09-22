#!/usr/bin/env python3
"""
Summary Display Component for Email Helper GUI

Manages formatted summary display with rich text formatting and interactive elements.
Extracted from unified_gui.py to improve modularity.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
import webbrowser

from .base_component import BaseComponent


class SummaryDisplayComponent(BaseComponent):
    """Component for displaying formatted email summaries with rich text."""
    
    def __init__(self, parent: tk.Widget, config: Dict[str, Any] = None):
        """
        Initialize the summary display component.
        
        Args:
            parent: Parent tkinter widget
            config: Configuration dictionary with options:
                - height: Text widget height (default: 20)
                - font: Text font configuration (default: ('Segoe UI', 10))
                - wrap: Text wrapping mode (default: tk.WORD)
                - enable_links: Whether to enable clickable links (default: True)
        """
        super().__init__(parent, config)
        
        # Text widget
        self.summary_text = None
        
        # Configuration
        self.height = self.get_config('height', 20)
        self.font = self.get_config('font', ('Segoe UI', 10))
        self.wrap = self.get_config('wrap', tk.WORD)
        self.enable_links = self.get_config('enable_links', True)
        
        # Summary data
        self.summary_sections = {}
        
    def create_widget(self) -> tk.Widget:
        """Create the summary display widget."""
        # Create main frame
        main_frame = ttk.Frame(self.parent)
        
        # Create scrolled text widget for summary
        self.summary_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=self.wrap,
            height=self.height,
            state=tk.DISABLED,
            font=self.font
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Configure rich text formatting tags
        self._configure_text_tags()
        
        # Bind link clicking if enabled
        if self.enable_links:
            self.summary_text.tag_bind("link", "<Button-1>", self._on_link_click)
            
        return main_frame
        
    def _configure_text_tags(self) -> None:
        """Configure rich text formatting tags for beautiful summary display."""
        # Main title
        self.summary_text.tag_configure("main_title", 
                                       font=("Segoe UI", 16, "bold"), 
                                       foreground="#007acc",
                                       justify="center")
        
        # Subtitle
        self.summary_text.tag_configure("subtitle", 
                                       font=("Segoe UI", 12), 
                                       foreground="#666666",
                                       justify="center")
        
        # Overview stats
        self.summary_text.tag_configure("overview_title", 
                                       font=("Segoe UI", 14, "bold"), 
                                       foreground="#005a8b")
        
        self.summary_text.tag_configure("overview_stats", 
                                       font=("Segoe UI", 11), 
                                       background="#e8f4fd",
                                       relief="raised",
                                       borderwidth=1)
        
        # Section headers
        self.summary_text.tag_configure("section_header", 
                                       font=("Segoe UI", 13, "bold"), 
                                       foreground="#0066cc",
                                       spacing1=15,
                                       spacing3=5)
        
        # Item titles
        self.summary_text.tag_configure("item_title", 
                                       font=("Segoe UI", 11, "bold"), 
                                       foreground="#2c3e50",
                                       spacing1=8)
        
        # Completed item titles
        self.summary_text.tag_configure("item_title_completed", 
                                       font=("Segoe UI", 11, "bold"), 
                                       foreground="#27ae60")
        
        # Item metadata
        self.summary_text.tag_configure("item_meta", 
                                       font=("Segoe UI", 9, "italic"), 
                                       foreground="#7f8c8d")
        
        # Content labels
        self.summary_text.tag_configure("content_label", 
                                       font=("Segoe UI", 10, "bold"), 
                                       foreground="#34495e")
        
        # Content text
        self.summary_text.tag_configure("content_text", 
                                       font=("Segoe UI", 10), 
                                       foreground="#2c3e50")
        
        # Links
        self.summary_text.tag_configure("link", 
                                       font=("Segoe UI", 10, "underline"), 
                                       foreground="#007acc")
        
        # Empty section placeholder
        self.summary_text.tag_configure("empty_section", 
                                       font=("Segoe UI", 10, "italic"), 
                                       foreground="#999999",
                                       justify="center")
        
        # Completion status styling
        self.summary_text.tag_configure("completion_status", 
                                       font=("Segoe UI", 10, "bold"), 
                                       foreground="#228B22")
        
        # Completion notes
        self.summary_text.tag_configure("completion_note", 
                                       font=("Segoe UI", 9, "italic"), 
                                       foreground="#555555")
        
    def update_data(self, data: Dict[str, Any]) -> None:
        """
        Update summary display with new data.
        
        Args:
            data: Dictionary containing:
                - summary_sections: Dict of summary sections to display
                - clear_content: bool - whether to clear existing content
        """
        if 'summary_sections' in data:
            self.summary_sections = data['summary_sections']
            self.display_formatted_summary(self.summary_sections)
            
        if data.get('clear_content', False):
            self.clear_content()
            
    def display_formatted_summary(self, summary_sections: Dict[str, Any]) -> None:
        """Display beautifully formatted summary directly in the application."""
        # Clear existing content
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        
        # Calculate totals including task persistence info
        total_items = sum(len(section.get('items', [])) for section in summary_sections.values())
        total_outstanding = sum(len(section.get('items', [])) for section_name, section in summary_sections.items() 
                               if section_name not in ['completed_team_actions'])
        
        # Header
        self.summary_text.insert(tk.END, "📧 Email Processing Summary\n", "main_title")
        self.summary_text.insert(tk.END, f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n", "subtitle")
        
        # Overview statistics
        self.summary_text.insert(tk.END, "📊 Summary Overview\n", "overview_title")
        overview_text = f"  📋 Total Items: {total_items}  •  ⏳ Outstanding: {total_outstanding}  •  ✅ Completed: {total_items - total_outstanding}  "
        self.summary_text.insert(tk.END, overview_text + "\n\n", "overview_stats")
        
        # Define display order and icons
        section_order = [
            ('required_personal_action', '🔴 Required Personal Actions', '_display_action_items'),
            ('team_action', '🟠 Team Actions Required', '_display_action_items'),
            ('completed_team_actions', '✅ Recently Completed Team Actions', '_display_completed_team_actions'),
            ('optional_action', '🟡 Optional Actions', '_display_optional_actions'),
            ('job_listing', '💼 Job Opportunities', '_display_job_listings'),
            ('optional_event', '📅 Optional Events', '_display_events'),
            ('fyi', '💡 FYI Notices', '_display_fyi_notices'),
            ('newsletter', '📰 Newsletters', '_display_newsletters')
        ]
        
        # Display each section
        for section_key, section_title, display_method in section_order:
            if section_key in summary_sections and summary_sections[section_key].get('items'):
                items = summary_sections[section_key]['items']
                
                self.summary_text.insert(tk.END, f"{section_title}\n", "section_header")
                
                # Call the appropriate display method
                method = getattr(self, display_method, None)
                if method:
                    method(items)
                else:
                    self._display_generic_items(items)
                    
                self.summary_text.insert(tk.END, "\n", "content_text")
            else:
                # Show empty section
                self.summary_text.insert(tk.END, f"{section_title}\n", "section_header")
                self.summary_text.insert(tk.END, "   No items in this category\n\n", "empty_section")
        
        # Configure text widget to prevent editing but allow button clicks
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.bind("<Key>", lambda e: "break")  # Prevent typing
        
    def _display_action_items(self, items: List[Dict[str, Any]]) -> None:
        """Display required or team action items with full details."""
        for i, item in enumerate(items, 1):
            # Item title with persistence indicator
            batch_count = item.get('batch_count', 1)
            title_prefix = ""
            if batch_count > 1:
                title_prefix = f"📅 [{batch_count}x] "  # Show how many batches this task has appeared in
            
            self.summary_text.insert(tk.END, f"{i}. {title_prefix}{item['subject']}\n", "item_title")
            
            # Metadata with first seen info
            self.summary_text.insert(tk.END, f"   From: {item['sender']}", "item_meta")
            if item.get('first_seen'):
                try:
                    first_seen = datetime.strptime(item['first_seen'], '%Y-%m-%d %H:%M:%S')
                    days_old = (datetime.now() - first_seen).days
                    if days_old > 0:
                        self.summary_text.insert(tk.END, f"  |  First seen: {days_old} days ago", "item_meta")
                except:
                    pass
            self.summary_text.insert(tk.END, "\n", "item_meta")
            
            # Action required
            self.summary_text.insert(tk.END, "   Action: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('action_required', 'Review email')}\n", "content_text")
            
            # Priority/urgency context if available
            if item.get('urgency_context'):
                self.summary_text.insert(tk.END, "   Context: ", "content_label")
                self.summary_text.insert(tk.END, f"{item['urgency_context']}\n", "content_text")
            
            # Task completion button - using embedded button widget
            if item.get('task_id'):
                complete_button = tk.Button(
                    self.summary_text,
                    text="✓ Mark Complete",
                    font=("Segoe UI", 8),
                    bg="#e8f5e8",
                    relief="ridge",
                    command=lambda tid=item['task_id']: self._mark_task_complete(tid)
                )
                self.summary_text.window_create(tk.END, window=complete_button)
                
                self.summary_text.insert(tk.END, "\n", "content_text")
            
            # Links
            if item.get('links'):
                self.summary_text.insert(tk.END, "   Links: ", "content_label")
                for j, link in enumerate(item['links'][:2]):
                    link_text = f"Link {j+1}"
                    link_start = self.summary_text.index(tk.END)
                    self.summary_text.insert(tk.END, link_text, "link")
                    link_end = self.summary_text.index(tk.END)
                    
                    # Create unique tag for this link
                    link_tag = f"link_{hash(link)}"
                    self.summary_text.tag_add(link_tag, link_start, link_end)
                    self.summary_text.tag_configure(link_tag, foreground="#007acc", underline=True)
                    self.summary_text.tag_bind(link_tag, "<Button-1>", lambda e, url=link: self._open_url(url))
                    
                    if j < min(len(item['links']), 2) - 1:
                        self.summary_text.insert(tk.END, " | ", "content_text")
                self.summary_text.insert(tk.END, "\n", "content_text")
            
            self.summary_text.insert(tk.END, "\n", "content_text")
            
    def _display_completed_team_actions(self, items: List[Dict[str, Any]]) -> None:
        """Display completed team action items with completion details."""
        for i, item in enumerate(items, 1):
            # Item title with completion indicator
            self.summary_text.insert(tk.END, f"{i}. ✅ {item['subject']}\n", "item_title_completed")
            
            # Metadata
            self.summary_text.insert(tk.END, f"   From: {item['sender']}", "item_meta")
            if item.get('first_seen'):
                try:
                    first_seen = datetime.strptime(item['first_seen'], '%Y-%m-%d %H:%M:%S')
                    days_old = (datetime.now() - first_seen).days
                    if days_old > 0:
                        self.summary_text.insert(tk.END, f"  |  First seen: {days_old} days ago", "item_meta")
                except:
                    pass
            self.summary_text.insert(tk.END, "\n", "item_meta")
            
            # Original action
            self.summary_text.insert(tk.END, "   Original Action: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('action_required', 'Review email')}\n", "content_text")
            
            # Completion details
            self.summary_text.insert(tk.END, "   ✅ Status: ", "content_label")
            self.summary_text.insert(tk.END, "COMPLETED\n", "completion_status")
            
            if item.get('completion_note'):
                self.summary_text.insert(tk.END, "   📝 Note: ", "content_label")
                self.summary_text.insert(tk.END, f"{item['completion_note']}\n", "completion_note")
            
            self.summary_text.insert(tk.END, "\n", "content_text")
            
    def _display_optional_actions(self, items: List[Dict[str, Any]]) -> None:
        """Display optional action items with relevance context."""
        for i, item in enumerate(items, 1):
            # Item title with persistence indicator
            batch_count = item.get('batch_count', 1)
            title_prefix = ""
            if batch_count > 1:
                title_prefix = f"📅 [{batch_count}x] "
            
            self.summary_text.insert(tk.END, f"{i}. {title_prefix}{item['subject']}\n", "item_title")
            
            # Metadata
            self.summary_text.insert(tk.END, f"   From: {item['sender']}\n", "item_meta")
            
            # Why relevant
            self.summary_text.insert(tk.END, "   Why relevant: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('relevance', 'General interest')}\n", "content_text")
            
            # Suggested action
            self.summary_text.insert(tk.END, "   Suggested action: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('action_required', 'Review when convenient')}\n", "content_text")
            
            self.summary_text.insert(tk.END, "\n", "content_text")
            
    def _display_job_listings(self, items: List[Dict[str, Any]]) -> None:
        """Display job listings with qualification match."""
        for i, item in enumerate(items, 1):
            # Item title
            self.summary_text.insert(tk.END, f"{i}. {item['subject']}\n", "item_title")
            
            # Metadata
            self.summary_text.insert(tk.END, f"   From: {item['sender']}\n", "item_meta")
            
            # Match reason
            self.summary_text.insert(tk.END, "   Why flagged: ", "content_label")
            self.summary_text.insert(tk.END, f"{item.get('relevance', 'Job opportunity detected')}\n", "content_text")
            
            # Links
            if item.get('links'):
                self.summary_text.insert(tk.END, "   Apply: ", "content_label")
                for j, link in enumerate(item['links'][:2]):
                    link_text = f"Apply {j+1}"
                    self._insert_link(link_text, link)
                    if j < min(len(item['links']), 2) - 1:
                        self.summary_text.insert(tk.END, " | ", "content_text")
                self.summary_text.insert(tk.END, "\n", "content_text")
            
            self.summary_text.insert(tk.END, "\n", "content_text")
            
    def _display_events(self, items: List[Dict[str, Any]]) -> None:
        """Display optional events with relevance."""
        for i, item in enumerate(items, 1):
            # Item title
            self.summary_text.insert(tk.END, f"{i}. {item['subject']}\n", "item_title")
            
            # Metadata
            self.summary_text.insert(tk.END, f"   From: {item['sender']}\n", "item_meta")
            
            # Event details
            self.summary_text.insert(tk.END, "   Date: ", "content_label")
            self.summary_text.insert(tk.END, f"{item['date']}\n", "content_text")
            
            self.summary_text.insert(tk.END, "   Why relevant: ", "content_label")
            self.summary_text.insert(tk.END, f"{item['relevance']}\n", "content_text")
            
            # Links
            if item.get('links'):
                self.summary_text.insert(tk.END, "   Register: ", "content_label")
                for j, link in enumerate(item['links'][:2]):
                    link_text = f"Register {j+1}"
                    self._insert_link(link_text, link)
                    if j < min(len(item['links']), 2) - 1:
                        self.summary_text.insert(tk.END, " | ", "content_text")
                self.summary_text.insert(tk.END, "\n", "content_text")
            
            self.summary_text.insert(tk.END, "\n", "content_text")
            
    def _display_fyi_notices(self, items: List[Dict[str, Any]]) -> None:
        """Display FYI notices as bullet points with dismiss functionality."""
        for i, item in enumerate(items, 1):
            self.summary_text.insert(tk.END, f"• {item['subject']}\n", "content_text")
            
        # Dismiss all button for FYI items
        if items:
            dismiss_button = tk.Button(
                self.summary_text,
                text="✓ Dismiss All FYI Items",
                font=("Segoe UI", 9),
                bg="#fff3cd",
                relief="ridge",
                command=self._dismiss_all_fyi_items
            )
            self.summary_text.window_create(tk.END, window=dismiss_button)
            self.summary_text.insert(tk.END, "\n", "content_text")
            
    def _display_newsletters(self, items: List[Dict[str, Any]]) -> None:
        """Display newsletter summaries with dismiss functionality."""
        for i, item in enumerate(items, 1):
            self.summary_text.insert(tk.END, f"• {item['subject']}\n", "content_text")
            
        # Dismiss all button for newsletters
        if items:
            dismiss_button = tk.Button(
                self.summary_text,
                text="✓ Dismiss All Newsletters",
                font=("Segoe UI", 9),
                bg="#fff3cd",
                relief="ridge",
                command=self._dismiss_all_newsletters
            )
            self.summary_text.window_create(tk.END, window=dismiss_button)
            self.summary_text.insert(tk.END, "\n", "content_text")
            
    def _display_generic_items(self, items: List[Dict[str, Any]]) -> None:
        """Display generic items with basic formatting."""
        for i, item in enumerate(items, 1):
            self.summary_text.insert(tk.END, f"{i}. {item.get('subject', 'No subject')}\n", "item_title")
            self.summary_text.insert(tk.END, f"   From: {item.get('sender', 'Unknown')}\n", "item_meta")
            if item.get('action_required'):
                self.summary_text.insert(tk.END, "   Action: ", "content_label")
                self.summary_text.insert(tk.END, f"{item['action_required']}\n", "content_text")
            self.summary_text.insert(tk.END, "\n", "content_text")
            
    def _insert_link(self, text: str, url: str) -> None:
        """Insert a clickable link into the text widget."""
        link_start = self.summary_text.index(tk.END)
        self.summary_text.insert(tk.END, text, "link")
        link_end = self.summary_text.index(tk.END)
        
        # Create unique tag for this link
        link_tag = f"link_{hash(url)}"
        self.summary_text.tag_add(link_tag, link_start, link_end)
        self.summary_text.tag_configure(link_tag, foreground="#007acc", underline=True)
        self.summary_text.tag_bind(link_tag, "<Button-1>", lambda e, u=url: self._open_url(u))
        
    def _on_link_click(self, event) -> None:
        """Handle link clicks in the summary display."""
        # Get the tag at the click position
        tags = self.summary_text.tag_names(tk.CURRENT)
        for tag in tags:
            if tag.startswith("link_"):
                # Extract URL from tag (this would need to be implemented)
                self.emit_event('link_clicked', {'tag': tag})
                break
                
    def _open_url(self, url: str) -> None:
        """Open URL in browser."""
        try:
            webbrowser.open(url)
            self.emit_event('url_opened', {'url': url})
        except Exception as e:
            self.emit_event('url_error', {'url': url, 'error': str(e)})
            
    def _mark_task_complete(self, task_id: str) -> None:
        """Mark a task as complete."""
        self.emit_event('task_complete', {'task_id': task_id})
        
    def _dismiss_all_fyi_items(self) -> None:
        """Dismiss all FYI items."""
        self.emit_event('dismiss_fyi_items', None)
        
    def _dismiss_all_newsletters(self) -> None:
        """Dismiss all newsletter items."""
        self.emit_event('dismiss_newsletters', None)
        
    def clear_content(self) -> None:
        """Clear all content from the summary display."""
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.config(state=tk.DISABLED)
        
    def set_content(self, content: str, tags: Optional[str] = None) -> None:
        """Set plain text content."""
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        if tags:
            self.summary_text.insert(tk.END, content, tags)
        else:
            self.summary_text.insert(tk.END, content)
        self.summary_text.config(state=tk.DISABLED)
        
    def get_text_widget(self) -> scrolledtext.ScrolledText:
        """Get the underlying text widget for advanced operations."""
        return self.summary_text