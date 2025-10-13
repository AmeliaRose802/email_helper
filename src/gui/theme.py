#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modern theme and styling for Email Helper GUI.

This module provides a consistent, professional UI theme with:
- Modern color palette with excellent contrast
- Typography standards and font configurations
- Spacing and layout guidelines following 8px grid system
- TTK style configurations for all widgets
"""

import tkinter as tk
from tkinter import ttk


class ModernTheme:
    """Professional 2025 UI theme with excellent contrast and modern aesthetics."""
    
    # Modern high-contrast color palette
    PRIMARY = "#0066CC"  # Rich blue with excellent contrast
    PRIMARY_HOVER = "#0052A3"  # Darker blue for hover
    PRIMARY_LIGHT = "#E6F2FF"  # Light blue background
    PRIMARY_DISABLED = "#99C2E6"  # Muted blue for disabled state
    
    SECONDARY = "#5C2D91"  # Professional purple
    SECONDARY_LIGHT = "#F3EDF7"  # Light purple background
    
    SUCCESS = "#0F7B0F"  # Strong green
    SUCCESS_LIGHT = "#E6F4E6"  # Light green background
    WARNING = "#F7B500"  # Vibrant amber
    WARNING_LIGHT = "#FFF8E1"  # Light amber background
    ERROR = "#C50F1F"  # Bold red
    ERROR_LIGHT = "#FDE7E9"  # Light red background
    INFO = "#0078D4"  # Info blue
    INFO_LIGHT = "#E5F2FA"  # Light info background
    
    # Modern neutral colors
    BACKGROUND = "#FFFFFF"  # Pure white
    SURFACE = "#F5F5F5"  # Subtle gray surface
    SURFACE_VARIANT = "#E8E8E8"  # Darker surface for hierarchy
    BORDER = "#C8C8C8"  # Visible borders
    BORDER_LIGHT = "#E0E0E0"  # Subtle borders
    DIVIDER = "#D4D4D4"  # Section dividers
    
    TEXT = "#1A1A1A"  # Near-black for excellent readability
    TEXT_SECONDARY = "#4D4D4D"  # Medium gray
    TEXT_TERTIARY = "#737373"  # Lighter gray for hints
    TEXT_DISABLED = "#999999"  # Disabled text
    TEXT_INVERSE = "#FFFFFF"  # White text on dark backgrounds
    
    # Enhanced typography
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE_TITLE = 14
    FONT_SIZE_LARGE = 11
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_SMALL = 9
    FONT_SIZE_TINY = 8
    
    FONT_BOLD = ("Segoe UI", 10, "bold")
    FONT_SEMIBOLD = ("Segoe UI Semibold", 10)
    FONT_LARGE = ("Segoe UI", 11, "bold")
    FONT_TITLE = ("Segoe UI", 14, "bold")
    
    # Modern spacing (8px grid system)
    SPACING_TINY = 4
    SPACING_SMALL = 8
    SPACING_MEDIUM = 16
    SPACING_LARGE = 24
    SPACING_XLARGE = 32
    
    # Animation timing
    ANIMATION_FAST = 150  # milliseconds
    ANIMATION_NORMAL = 250
    ANIMATION_SLOW = 400
    
    @staticmethod
    def configure_ttk_style(style):
        """Configure ttk.Style with modern 2025 aesthetics."""
        style.theme_use('clam')  # Better base for customization than vista
        
        # TNotebook - Modern tab styling
        style.configure("TNotebook", 
                       background=ModernTheme.BACKGROUND, 
                       borderwidth=0,
                       relief="flat")
        style.configure("TNotebook.Tab", 
                       padding=[20, 10], 
                       font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_NORMAL),
                       background=ModernTheme.SURFACE,
                       foreground=ModernTheme.TEXT_SECONDARY,
                       borderwidth=0)
        style.map("TNotebook.Tab",
                 background=[("selected", ModernTheme.BACKGROUND), 
                           ("!selected", ModernTheme.SURFACE),
                           ("active", ModernTheme.SURFACE_VARIANT)],
                 foreground=[("selected", ModernTheme.PRIMARY), 
                           ("!selected", ModernTheme.TEXT_SECONDARY),
                           ("active", ModernTheme.TEXT)],
                 padding=[("selected", [20, 12])],
                 expand=[("selected", [1, 1, 1, 0])])
        
        # TFrame - Modern frames
        style.configure("TFrame", 
                       background=ModernTheme.BACKGROUND,
                       borderwidth=0)
        style.configure("Surface.TFrame", 
                       background=ModernTheme.SURFACE,
                       borderwidth=0)
        style.configure("Card.TFrame",
                       background=ModernTheme.BACKGROUND,
                       relief="flat",
                       borderwidth=1)
        
        # TLabel - Modern typography
        style.configure("TLabel", 
                       background=ModernTheme.BACKGROUND, 
                       foreground=ModernTheme.TEXT,
                       font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_NORMAL))
        style.configure("Title.TLabel", 
                       font=ModernTheme.FONT_TITLE,
                       foreground=ModernTheme.PRIMARY)
        style.configure("Header.TLabel", 
                       font=ModernTheme.FONT_LARGE,
                       foreground=ModernTheme.TEXT)
        style.configure("Secondary.TLabel",
                       foreground=ModernTheme.TEXT_SECONDARY,
                       font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_SMALL))
        style.configure("Metric.TLabel",
                       font=(ModernTheme.FONT_FAMILY, 24, "bold"),
                       foreground=ModernTheme.PRIMARY,
                       background=ModernTheme.SURFACE,
                       padding=20,
                       relief="flat",
                       borderwidth=1)
        
        # TButton - Consistent professional buttons
        style.configure("TButton",
                       padding=[16, 8],
                       font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_NORMAL),
                       borderwidth=1,
                       relief="flat",
                       background=ModernTheme.SURFACE,
                       foreground=ModernTheme.TEXT)
        style.map("TButton",
                 background=[("active", ModernTheme.SURFACE_VARIANT),
                           ("disabled", ModernTheme.SURFACE)],
                 foreground=[("disabled", ModernTheme.TEXT_DISABLED)])
        
        style.configure("Accent.TButton",
                       padding=[16, 8],
                       font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_NORMAL, "bold"),
                       background=ModernTheme.PRIMARY,
                       foreground=ModernTheme.TEXT_INVERSE,
                       borderwidth=0,
                       relief="flat")
        style.map("Accent.TButton",
                 background=[("active", ModernTheme.PRIMARY_HOVER),
                           ("disabled", ModernTheme.PRIMARY_DISABLED)],
                 foreground=[("disabled", ModernTheme.TEXT_INVERSE)])
        
        # TProgressbar - Smooth progress bar
        style.configure("TProgressbar",
                       troughcolor=ModernTheme.SURFACE_VARIANT,
                       background=ModernTheme.PRIMARY,
                       borderwidth=0,
                       thickness=8)
        
        # TEntry - Modern input fields
        style.configure("TEntry",
                       fieldbackground=ModernTheme.BACKGROUND,
                       foreground=ModernTheme.TEXT,
                       bordercolor=ModernTheme.BORDER,
                       lightcolor=ModernTheme.BORDER_LIGHT,
                       darkcolor=ModernTheme.BORDER,
                       insertcolor=ModernTheme.PRIMARY,
                       borderwidth=1,
                       relief="flat")
        style.map("TEntry",
                 bordercolor=[("focus", ModernTheme.PRIMARY)],
                 lightcolor=[("focus", ModernTheme.PRIMARY_LIGHT)],
                 darkcolor=[("focus", ModernTheme.PRIMARY)])
        
        # TCombobox - Consistent with Entry
        style.configure("TCombobox",
                       fieldbackground=ModernTheme.BACKGROUND,
                       background=ModernTheme.BACKGROUND,
                       foreground=ModernTheme.TEXT,
                       bordercolor=ModernTheme.BORDER,
                       arrowcolor=ModernTheme.TEXT_SECONDARY,
                       borderwidth=1,
                       relief="flat")
        style.map("TCombobox",
                 fieldbackground=[("readonly", ModernTheme.BACKGROUND)],
                 bordercolor=[("focus", ModernTheme.PRIMARY)])
        
        # Treeview - Modern table styling
        style.configure("Treeview",
                       background=ModernTheme.BACKGROUND,
                       foreground=ModernTheme.TEXT,
                       fieldbackground=ModernTheme.BACKGROUND,
                       font=(ModernTheme.FONT_FAMILY, ModernTheme.FONT_SIZE_NORMAL),
                       borderwidth=1,
                       relief="flat",
                       rowheight=28)
        style.configure("Treeview.Heading",
                       background=ModernTheme.SURFACE,
                       foreground=ModernTheme.TEXT,
                       font=ModernTheme.FONT_BOLD,
                       borderwidth=1,
                       relief="flat")
        style.map("Treeview",
                 background=[("selected", ModernTheme.PRIMARY_LIGHT)],
                 foreground=[("selected", ModernTheme.TEXT)])
        style.map("Treeview.Heading",
                 background=[("active", ModernTheme.SURFACE_VARIANT)])
        
        # TLabelframe - Modern group boxes
        style.configure("TLabelframe",
                       background=ModernTheme.BACKGROUND,
                       borderwidth=1,
                       bordercolor=ModernTheme.BORDER_LIGHT,
                       relief="flat")
        style.configure("TLabelframe.Label",
                       background=ModernTheme.BACKGROUND,
                       foreground=ModernTheme.TEXT_SECONDARY,
                       font=ModernTheme.FONT_SEMIBOLD)
