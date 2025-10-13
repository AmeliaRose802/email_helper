#!/usr/bin/env python3
"""Test script to verify link functionality in GUI summary."""

import tkinter as tk
from tkinter import messagebox
import webbrowser

def test_link_system():
    """Test the link system to ensure it works properly"""
    root = tk.Tk()
    root.title("Link Test")
    root.geometry("600x400")
    
    # Create text widget
    text_widget = tk.Text(root, wrap=tk.WORD, font=("Arial", 11))
    text_widget.pack(expand=True, fill='both', padx=10, pady=10)
    
    # Configure link styling
    text_widget.tag_configure("link", foreground="#007acc", underline=True)
    
    # Method to configure clickable links
    def configure_clickable_link(tag_name, url):
        """Configure a clickable link tag with proper styling and behavior"""
        text_widget.tag_configure(tag_name, foreground="#007acc", underline=True)
        text_widget.tag_bind(tag_name, "<Button-1>", lambda e, url=url: open_url(url))
        text_widget.tag_bind(tag_name, "<Enter>", lambda e: text_widget.config(cursor="hand2"))
        text_widget.tag_bind(tag_name, "<Leave>", lambda e: text_widget.config(cursor=""))
    
    def open_url(url):
        """Open URL in default browser"""
        try:
            webbrowser.open(url)
            messagebox.showinfo("Success", f"Opened: {url}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open URL: {url}\n\nError: {str(e)}")
    
    # Add test content
    text_widget.insert(tk.END, "Testing Link System\n\n", "title")
    
    # Test 1: Link with unique tag (should work)
    text_widget.insert(tk.END, "Test 1 - Unique Tag Link: ")
    link_tag = f"link_{hash('https://github.com')}"
    text_widget.insert(tk.END, "GitHub", link_tag)
    configure_clickable_link(link_tag, 'https://github.com')
    text_widget.insert(tk.END, "\n\n")
    
    # Test 2: Another unique tag link
    text_widget.insert(tk.END, "Test 2 - Another Link: ")
    link_tag2 = f"link_{hash('https://microsoft.com')}"
    text_widget.insert(tk.END, "Microsoft", link_tag2)
    configure_clickable_link(link_tag2, 'https://microsoft.com')
    text_widget.insert(tk.END, "\n\n")
    
    # Test 3: Generic link tag (should show info message)
    def generic_link_handler(event):
        messagebox.showinfo("Generic Link", "This would be handled by the generic link handler")
    
    text_widget.tag_bind("link", "<Button-1>", generic_link_handler)
    text_widget.tag_bind("link", "<Enter>", lambda e: text_widget.config(cursor="hand2"))
    text_widget.tag_bind("link", "<Leave>", lambda e: text_widget.config(cursor=""))
    
    text_widget.insert(tk.END, "Test 3 - Generic Tag: ")
    text_widget.insert(tk.END, "Generic Link", "link")
    text_widget.insert(tk.END, "\n\n")
    
    text_widget.insert(tk.END, "Instructions:\n")
    text_widget.insert(tk.END, "1. Click on 'GitHub' - should open GitHub\n")
    text_widget.insert(tk.END, "2. Click on 'Microsoft' - should open Microsoft\n")
    text_widget.insert(tk.END, "3. Click on 'Generic Link' - should show info message\n")
    text_widget.insert(tk.END, "4. Hover over links - cursor should change to hand\n")
    
    root.mainloop()

if __name__ == "__main__":
    test_link_system()