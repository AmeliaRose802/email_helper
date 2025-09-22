#!/usr/bin/env python3
"""
Email Tree Component for Email Helper GUI

Manages email list display, sorting, filtering, and selection.
Extracted from unified_gui.py to improve modularity.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from .base_component import BaseComponent


class EmailTreeComponent(BaseComponent):
    """Component for displaying and managing email list with tree view."""
    
    def __init__(self, parent: tk.Widget, config: Dict[str, Any] = None):
        """
        Initialize the email tree component.
        
        Args:
            parent: Parent tkinter widget
            config: Configuration dictionary with options:
                - columns: List of column names (default: standard email columns)
                - height: Tree height (default: 12)
                - column_widths: Dict of column widths
                - show_headers: bool (default: True)
                - sortable: bool (default: True)
        """
        super().__init__(parent, config)
        
        # Data
        self.email_suggestions = []
        self.current_selection_index = None
        
        # Sorting state
        self.sort_column = None
        self.sort_reverse = False
        
        # Tree components
        self.tree = None
        self.scrollbar = None
        
        # Default configuration
        self.columns = self.get_config('columns', ('Subject', 'From', 'Category', 'AI Summary', 'Date'))
        self.column_widths = self.get_config('column_widths', {
            'Subject': 250,
            'From': 150, 
            'Category': 150,
            'AI Summary': 300,
            'Date': 100
        })
        
    def create_widget(self) -> tk.Widget:
        """Create the email tree widget."""
        # Main frame to contain tree and scrollbar
        main_frame = ttk.Frame(self.parent)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Create treeview
        height = self.get_config('height', 12)
        self.tree = ttk.Treeview(
            main_frame, 
            columns=self.columns, 
            show='headings', 
            height=height
        )
        
        # Configure columns
        if self.get_config('sortable', True):
            for col in self.columns:
                self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
        else:
            for col in self.columns:
                self.tree.heading(col, text=col)
                
        # Set column widths
        for col in self.columns:
            width = self.column_widths.get(col, 100)
            self.tree.column(col, width=width)
        
        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        # Layout tree and scrollbar
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self._on_selection_change)
        
        return main_frame
        
    def update_data(self, data: Dict[str, Any]) -> None:
        """
        Update tree with new email data.
        
        Args:
            data: Dictionary containing:
                - emails: List of email suggestion dictionaries
                - clear_selection: bool (optional) - whether to clear current selection
        """
        if 'emails' in data:
            self.email_suggestions = data['emails']
            self.refresh_tree()
            
        if data.get('clear_selection', False):
            self.clear_selection()
            
    def refresh_tree(self) -> None:
        """Refresh the tree view with current email suggestions."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Populate with email data
        for i, suggestion_data in enumerate(self.email_suggestions):
            self._add_email_item(suggestion_data, i)
            
    def _add_email_item(self, suggestion_data: Dict[str, Any], index: int) -> None:
        """Add an email item to the tree."""
        email_data = suggestion_data.get('email_data', {})
        suggestion = suggestion_data['ai_suggestion']
        ai_summary = suggestion_data.get('ai_summary', 'No summary')
        thread_data = suggestion_data.get('thread_data', {})
        thread_count = thread_data.get('thread_count', 1)
        
        # Extract display values
        subject = email_data.get('subject', 'No Subject')
        sender_name = email_data.get('sender_name', email_data.get('sender', 'Unknown'))
        date_received = email_data.get('received_time', email_data.get('date_received'))
        
        # Format thread information
        if thread_count > 1:
            participants = thread_data.get('participants', [])
            participant_count = len(participants)
            sender_display = f"{sender_name} (+{participant_count-1} participants)"
            subject_display = f"🧵 {subject} ({thread_count} emails)"
        else:
            sender_display = sender_name
            subject_display = subject
            
        # Format date
        if isinstance(date_received, datetime):
            date_str = date_received.strftime('%m/%d/%Y')
        elif hasattr(date_received, 'strftime'):
            date_str = date_received.strftime('%m/%d/%Y')
        else:
            date_str = str(date_received) if date_received else 'Unknown'
            
        # Format category for display
        category = self._format_category_for_display(suggestion)
        
        # Truncate long text for display
        if len(subject_display) > 50:
            subject_display = subject_display[:47] + "..."
        if not sender_display.endswith('participants') and len(sender_display) > 25:
            sender_display = sender_display[:22] + "..."
        if len(ai_summary) > 50:
            ai_summary = ai_summary[:47] + "..."
            
        # Insert item into tree
        values = (subject_display, sender_display, category, ai_summary, date_str)
        self.tree.insert('', 'end', values=values)
        
    def _format_category_for_display(self, category: str) -> str:
        """Format internal category name for display."""
        category_mapping = {
            'required_personal_action': 'Required Personal Action',
            'team_action': 'Team Action',
            'optional_action': 'Optional Action',
            'job_listing': 'Job Listing',
            'optional_event': 'Optional Event',
            'fyi': 'FYI Notice',
            'newsletter': 'Newsletter',
            'work_relevant': 'Work Relevant',
            'general_information': 'General Information',
            'spam_to_delete': 'Spam To Delete'
        }
        return category_mapping.get(category, category.replace('_', ' ').title())
        
    def sort_by_column(self, col: str) -> None:
        """Sort the tree by specified column."""
        if not self.email_suggestions:
            return
            
        # Toggle sort direction if clicking same column
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False
            
        # Update column headers to show sort direction
        for column in self.columns:
            if column == col:
                direction = " ↓" if self.sort_reverse else " ↑"
                self.tree.heading(column, text=f"{column}{direction}")
            else:
                self.tree.heading(column, text=column)
                
        # Create list of (index, sort_value) pairs
        items_with_sort_keys = []
        for i, suggestion in enumerate(self.email_suggestions):
            email_data = suggestion['email_data']
            
            if col == 'Subject':
                sort_key = email_data.get('subject', '').lower()
            elif col == 'From':
                sort_key = email_data.get('sender_name', email_data.get('sender', '')).lower()
            elif col == 'Category':
                sort_key = suggestion['ai_suggestion'].lower()
            elif col == 'AI Summary':
                sort_key = suggestion.get('ai_summary', '').lower()
            elif col == 'Date':
                date_received = email_data.get('received_time', email_data.get('date_received'))
                if isinstance(date_received, datetime):
                    sort_key = date_received
                elif hasattr(date_received, 'strftime'):
                    sort_key = date_received
                else:
                    sort_key = datetime.min
            else:
                sort_key = ''
                
            items_with_sort_keys.append((i, sort_key))
            
        # Sort the items
        items_with_sort_keys.sort(key=lambda x: x[1], reverse=self.sort_reverse)
        
        # Reorder email suggestions and refresh tree
        self.email_suggestions = [self.email_suggestions[i] for i, _ in items_with_sort_keys]
        self.refresh_tree()
        
        # Emit sort event
        self.emit_event('tree_sorted', {
            'column': col,
            'reverse': self.sort_reverse,
            'email_suggestions': self.email_suggestions
        })
        
    def _on_selection_change(self, event) -> None:
        """Handle tree selection change."""
        selection = self.tree.selection()
        if not selection:
            self.current_selection_index = None
            self.emit_event('selection_cleared', None)
            return
            
        # Find index of selected item
        item = selection[0]
        index = None
        for i, child in enumerate(self.tree.get_children()):
            if child == item:
                index = i
                break
                
        if index is not None and index < len(self.email_suggestions):
            self.current_selection_index = index
            email_data = self.email_suggestions[index]
            self.emit_event('email_selected', {
                'index': index,
                'email_data': email_data
            })
        else:
            self.current_selection_index = None
            self.emit_event('selection_cleared', None)
            
    def get_selected_index(self) -> Optional[int]:
        """Get the index of currently selected email."""
        return self.current_selection_index
        
    def get_selected_email(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected email data."""
        if (self.current_selection_index is not None and 
            0 <= self.current_selection_index < len(self.email_suggestions)):
            return self.email_suggestions[self.current_selection_index]
        return None
        
    def select_first_email(self) -> None:
        """Select and focus the first email in the tree."""
        children = self.tree.get_children()
        if children:
            first_item = children[0]
            self.tree.selection_set(first_item)
            self.tree.focus(first_item)
            # This will trigger _on_selection_change
            
    def clear_selection(self) -> None:
        """Clear the current selection."""
        self.tree.selection_clear()
        self.current_selection_index = None
        
    def clear_tree(self) -> None:
        """Clear all items from the tree."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.email_suggestions = []
        self.current_selection_index = None
        
    def get_email_count(self) -> int:
        """Get the number of emails in the tree."""
        return len(self.email_suggestions)
        
    def find_email_by_entry_id(self, entry_id: str) -> Optional[int]:
        """
        Find email index by entry_id.
        
        Args:
            entry_id: Email entry ID to search for
            
        Returns:
            Index of email or None if not found
        """
        for i, suggestion in enumerate(self.email_suggestions):
            email_data = suggestion.get('email_data', {})
            if email_data.get('entry_id') == entry_id:
                return i
        return None
        
    def update_email_category(self, index: int, new_category: str) -> None:
        """
        Update the category of an email at specified index.
        
        Args:
            index: Index of email to update
            new_category: New category value
        """
        if 0 <= index < len(self.email_suggestions):
            self.email_suggestions[index]['ai_suggestion'] = new_category
            self.refresh_tree()
            
            # Restore selection if it was the updated item
            if self.current_selection_index == index:
                children = self.tree.get_children()
                if 0 <= index < len(children):
                    self.tree.selection_set(children[index])
                    self.tree.focus(children[index])