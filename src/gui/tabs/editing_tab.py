#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Editing Tab - Email review and categorization interface (VIEW ONLY - NO BUSINESS LOGIC)."""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import List, Dict, Any, Optional, Callable
from gui.helpers import clean_email_formatting, find_urls_in_text, open_url


class EditingTab:
    """Email editing and review tab - pure view component.
    
    This view delegates all business logic to the EmailEditingController.
    """
    
    def __init__(
        self,
        parent,
        category_mapping: Dict[str, str],
        on_email_select_callback: Callable,
        on_category_change_callback: Callable,
        on_apply_category_callback: Callable,
        on_apply_to_outlook_callback: Callable,
        on_generate_summary_callback: Callable,
        on_sort_callback: Callable
    ):
        """Initialize editing tab view.
        
        Args:
            parent: Parent widget
            category_mapping: Dictionary mapping category names to display names
            on_email_select_callback: Callback when email is selected
            on_category_change_callback: Callback when category dropdown changes
            on_apply_category_callback: Callback for manual apply button
            on_apply_to_outlook_callback: Callback for apply to Outlook button
            on_generate_summary_callback: Callback for generate summary button
            on_sort_callback: Callback for column sorting
        """
        self.parent = parent
        self.category_mapping = category_mapping
        self.on_email_select_callback = on_email_select_callback
        self.on_category_change_callback = on_category_change_callback
        self.on_apply_category_callback = on_apply_category_callback
        self.on_apply_to_outlook_callback = on_apply_to_outlook_callback
        self.on_generate_summary_callback = on_generate_summary_callback
        self.on_sort_callback = on_sort_callback
        
        self.sort_column = None
        self.sort_reverse = False
        self.current_email_index = None
        self.original_category = None
        
        self.category_var = tk.StringVar()
        self.explanation_var = tk.StringVar()
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create all UI widgets."""
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Email list
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        columns = ('Subject', 'From', 'Category', 'AI Summary', 'Date')
        self.email_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.email_tree.heading(col, text=col, command=lambda c=col: self._on_column_click(c))
        
        self.email_tree.column('Subject', width=250)
        self.email_tree.column('From', width=150)
        self.email_tree.column('Category', width=150)
        self.email_tree.column('AI Summary', width=300)
        self.email_tree.column('Date', width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.email_tree.yview)
        self.email_tree.configure(yscrollcommand=scrollbar.set)
        self.email_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.email_tree.bind('<<TreeviewSelect>>', self._on_email_select)
        
        # Details panel
        details_frame = ttk.LabelFrame(main_frame, text="Email Details", padding="10")
        details_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        details_frame.columnconfigure(1, weight=1)
        details_frame.rowconfigure(4, weight=1)
        
        ttk.Label(details_frame, text="Category:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.category_combo = ttk.Combobox(
            details_frame,
            textvariable=self.category_var,
            values=self.category_mapping if isinstance(self.category_mapping, list) else list(self.category_mapping.keys()),
            state="readonly"
        )
        self.category_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.category_combo.bind('<<ComboboxSelected>>', self._on_category_change)
        
        ttk.Label(
            details_frame,
            text="ℹ️ Changes apply automatically when category changes or switching emails",
            font=('Segoe UI', 8),
            foreground="#666666"
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(details_frame, text="Reason (optional):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.explanation_entry = ttk.Entry(details_frame, textvariable=self.explanation_var)
        self.explanation_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        self.apply_btn = ttk.Button(
            details_frame,
            text="Manual Apply",
            command=self._on_apply_click,
            state=tk.DISABLED
        )
        self.apply_btn.grid(row=3, column=1, sticky=tk.E, pady=5, padx=(5, 0))
        
        self.preview_text = scrolledtext.ScrolledText(
            details_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Segoe UI', 10)
        )
        self.preview_text.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        # Tag configuration for clickable links
        self.preview_text.tag_config("hyperlink", foreground="blue", underline=True)
        self.preview_text.tag_bind("hyperlink", "<Button-1>", self._on_link_click)
        self.preview_text.tag_bind("hyperlink", "<Enter>", lambda e: self.preview_text.config(cursor="hand2"))
        self.preview_text.tag_bind("hyperlink", "<Leave>", lambda e: self.preview_text.config(cursor=""))
        
        # Controls
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(15, 0))
        
        ttk.Button(
            button_frame,
            text="Apply to Outlook",
            command=self.on_apply_to_outlook_callback
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Generate Summary",
            command=self.on_generate_summary_callback,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)
    
    def _on_column_click(self, column: str):
        """Handle column header click for sorting."""
        self.on_sort_callback(column)
    
    def _on_email_select(self, event):
        """Handle email selection in tree."""
        self.on_email_select_callback()
    
    def _on_category_change(self, event):
        """Handle category dropdown change."""
        self.on_category_change_callback()
    
    def _on_apply_click(self):
        """Handle manual apply button click."""
        explanation = self.explanation_var.get().strip()
        self.on_apply_category_callback(explanation)
    
    def _on_link_click(self, event):
        """Handle hyperlink click in preview."""
        # Get the clicked position
        index = self.preview_text.index(f"@{event.x},{event.y}")
        # Get all hyperlink ranges
        for tag_range in self.preview_text.tag_ranges("hyperlink"):
            if self.preview_text.compare(index, ">=", tag_range[0]) and \
               self.preview_text.compare(index, "<=", tag_range[1]):
                url = self.preview_text.get(tag_range[0], tag_range[1])
                open_url(url)
                break
    
    # Public methods for updating UI from controller
    
    def load_emails(self, email_viewmodels: List[Any]):
        """Load emails into the tree view.
        
        Args:
            email_viewmodels: List of EmailSuggestionViewModel objects
        """
        self.email_tree.delete(*self.email_tree.get_children())
        
        for idx, vm in enumerate(email_viewmodels):
            self.email_tree.insert(
                '',
                tk.END,
                iid=str(idx),
                values=(
                    vm.subject,
                    vm.sender,
                    vm.category,
                    vm.ai_summary,
                    vm.date
                )
            )
    
    def get_selected_email_index(self) -> Optional[int]:
        """Get the currently selected email index.
        
        Returns:
            Index of selected email or None
        """
        selected = self.email_tree.selection()
        if not selected:
            return None
        return int(selected[0])
    
    def show_email_details(self, email_viewmodel: Any, is_modified: bool = False):
        """Display email details in the preview pane.
        
        Args:
            email_viewmodel: EmailDetailViewModel with full email details
            is_modified: Whether this email has been modified
        """
        self.current_email_index = email_viewmodel.index
        self.original_category = email_viewmodel.original_category
        
        # Update category dropdown
        self.category_var.set(email_viewmodel.category)
        
        # Update preview text
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        
        # Format email details
        header = f"📧 {email_viewmodel.subject}\n"
        header += f"From: {email_viewmodel.sender}\n"
        header += f"Date: {email_viewmodel.date}\n"
        if email_viewmodel.recipients:
            header += f"To: {email_viewmodel.recipients}\n"
        header += f"Category: {email_viewmodel.category}"
        if is_modified:
            header += " ✏️ (Modified)"
        header += "\n"
        header += f"AI Summary: {email_viewmodel.ai_summary}\n"
        header += "-" * 80 + "\n\n"
        
        self.preview_text.insert(tk.END, header)
        
        # Insert body with clickable links
        body = clean_email_formatting(email_viewmodel.body)
        urls = find_urls_in_text(body)
        
        if urls:
            last_pos = 0
            for url in urls:
                url_start = body.find(url, last_pos)
                if url_start != -1:
                    # Insert text before URL
                    self.preview_text.insert(tk.END, body[last_pos:url_start])
                    # Insert URL as hyperlink
                    self.preview_text.insert(tk.END, url, "hyperlink")
                    last_pos = url_start + len(url)
            # Insert remaining text
            self.preview_text.insert(tk.END, body[last_pos:])
        else:
            self.preview_text.insert(tk.END, body)
        
        self.preview_text.config(state=tk.DISABLED)
        
        # Enable/disable apply button based on modification
        self.apply_btn.config(state=tk.NORMAL if is_modified else tk.DISABLED)
    
    def clear_details(self):
        """Clear the details pane."""
        self.category_var.set("")
        self.explanation_var.set("")
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.config(state=tk.DISABLED)
        self.apply_btn.config(state=tk.DISABLED)
        self.current_email_index = None
        self.original_category = None
    
    def update_email_in_tree(self, index: int, email_viewmodel: Any):
        """Update a single email row in the tree.
        
        Args:
            index: Index of email to update
            email_viewmodel: EmailSuggestionViewModel with updated data
        """
        self.email_tree.item(
            str(index),
            values=(
                email_viewmodel.subject,
                email_viewmodel.sender,
                email_viewmodel.category,
                email_viewmodel.ai_summary,
                email_viewmodel.date
            )
        )
    
    def get_category(self) -> str:
        """Get currently selected category.
        
        Returns:
            Selected category string
        """
        return self.category_var.get()
    
    def get_explanation(self) -> str:
        """Get explanation text.
        
        Returns:
            Explanation string
        """
        return self.explanation_var.get().strip()
    
    def set_apply_button_state(self, enabled: bool):
        """Set apply button state.
        
        Args:
            enabled: Whether button should be enabled
        """
        self.apply_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)
