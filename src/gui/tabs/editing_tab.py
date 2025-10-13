#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Editing Tab - Email review and categorization interface."""

import tkinter as tk
from tkinter import ttk, scrolledtext
from gui.helpers import clean_email_formatting, find_urls_in_text, open_url


class EditingTab:
    """Email editing and review tab."""
    
    def __init__(self, parent, gui_ref):
        self.parent = parent
        self.gui = gui_ref
        self.sort_column = None
        self.sort_reverse = False
        self.current_email_index = None
        self.original_category = None
        self.create_widgets()
    
    def create_widgets(self):
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
            self.email_tree.heading(col, text=col, command=lambda c=col: self.gui.sort_by_column(c))
        
        self.email_tree.column('Subject', width=250)
        self.email_tree.column('From', width=150)
        self.email_tree.column('Category', width=150)
        self.email_tree.column('AI Summary', width=300)
        self.email_tree.column('Date', width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.email_tree.yview)
        self.email_tree.configure(yscrollcommand=scrollbar.set)
        self.email_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.email_tree.bind('<<TreeviewSelect>>', self.gui.on_email_select)
        
        # Details panel
        details_frame = ttk.LabelFrame(main_frame, text="Email Details", padding="10")
        details_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        details_frame.columnconfigure(1, weight=1)
        details_frame.rowconfigure(4, weight=1)
        
        ttk.Label(details_frame, text="Category:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(details_frame, textvariable=self.category_var,
                                          values=list(self.gui.CATEGORY_MAPPING.keys()),
                                          state="readonly")
        self.category_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.category_combo.bind('<<ComboboxSelected>>', self.gui.on_category_change)
        
        ttk.Label(details_frame, text="ℹ️ Changes apply automatically when category changes or switching emails",
                 font=('Segoe UI', 8), foreground="#666666").grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(details_frame, text="Reason (optional):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.explanation_var = tk.StringVar()
        self.explanation_entry = ttk.Entry(details_frame, textvariable=self.explanation_var)
        self.explanation_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        self.apply_btn = ttk.Button(details_frame, text="Manual Apply",
                                   command=self.gui.apply_category_change, state=tk.DISABLED)
        self.apply_btn.grid(row=3, column=1, sticky=tk.E, pady=5, padx=(5, 0))
        
        self.preview_text = scrolledtext.ScrolledText(details_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.preview_text.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        # Controls
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(15, 0))
        
        ttk.Button(button_frame, text="Apply to Outlook",
                  command=self.gui.apply_to_outlook).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Generate Summary",
                  command=self.gui.proceed_to_summary).pack(side=tk.LEFT, padx=5)
