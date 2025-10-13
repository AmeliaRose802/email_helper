#!/usr/bin/env python3
"""Quick diagnostic script to test GUI link functionality."""

import tkinter as tk
from tkinter import messagebox
import webbrowser

def test_gui_links():
    root = tk.Tk()
    root.title("GUI Link Test")
    root.geometry("500x300")
    
    text_widget = tk.Text(root, wrap=tk.WORD, font=("Arial", 11))
    text_widget.pack(expand=True, fill='both', padx=10, pady=10)
    
    # Configure link styling
    text_widget.tag_configure("link", foreground="#007acc", underline=True)
    
    # Method to configure clickable links (same as in unified_gui.py)
    def _configure_clickable_link(tag_name, url_or_handler, is_email_handler=False):
        text_widget.tag_configure(tag_name, foreground="#007acc", underline=True)
        
        if is_email_handler:
            text_widget.tag_bind(tag_name, "<Button-1>", url_or_handler)
        else:
            text_widget.tag_bind(tag_name, "<Button-1>", lambda e, url=url_or_handler: _open_url(url))
        
        text_widget.tag_bind(tag_name, "<Enter>", lambda e: text_widget.config(cursor="hand2"))
        text_widget.tag_bind(tag_name, "<Leave>", lambda e: text_widget.config(cursor=""))
        print(f"Configured clickable link: {tag_name} -> {'email_handler' if is_email_handler else url_or_handler}")
    
    def _open_url(url):
        try:
            webbrowser.open(url)
            messagebox.showinfo("Success", f"Opened: {url}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open URL: {url}\n\nError: {str(e)}")
    
    def email_handler(event):
        messagebox.showinfo("Email Handler", "Email handler called successfully!")
    
    # Test the same pattern as in the GUI
    text_widget.insert(tk.END, "Testing GUI Link Patterns\n\n", "title")
    
    # Test 1: URL link
    text_widget.insert(tk.END, "   Links: ", "content_label")
    link_text = "Link 1"
    link_url = "https://github.com"
    link_tag = f"link_{hash(link_url)}"
    text_widget.insert(tk.END, link_text, link_tag)
    _configure_clickable_link(link_tag, link_url)
    text_widget.insert(tk.END, "\n\n", "content_text")
    
    # Test 2: Email link
    text_widget.insert(tk.END, "   Email: ", "content_label")
    email_link_tag = f"email_link_{hash('test_email_data')}"
    text_widget.insert(tk.END, "View in Outlook", email_link_tag)
    _configure_clickable_link(email_link_tag, email_handler, is_email_handler=True)
    text_widget.insert(tk.END, "\n\n", "content_text")
    
    # Test 3: Generic link (fallback)
    def generic_link_handler(event):
        messagebox.showinfo("Link Access", 
                          "For clickable links, please use the 'Open in Browser' button to view the full HTML summary with working links.\n\nThe HTML version has fully functional clickable links.")
    
    text_widget.tag_bind("link", "<Button-1>", generic_link_handler)
    text_widget.tag_bind("link", "<Enter>", lambda e: text_widget.config(cursor="hand2"))
    text_widget.tag_bind("link", "<Leave>", lambda e: text_widget.config(cursor=""))
    
    text_widget.insert(tk.END, "   Generic: ", "content_label")
    text_widget.insert(tk.END, "Generic Link", "link")
    text_widget.insert(tk.END, "\n\n", "content_text")
    
    text_widget.insert(tk.END, "Instructions:\n")
    text_widget.insert(tk.END, "1. Click 'Link 1' - should open GitHub\n")
    text_widget.insert(tk.END, "2. Click 'View in Outlook' - should show email handler message\n")
    text_widget.insert(tk.END, "3. Click 'Generic Link' - should show HTML redirect message\n")
    text_widget.insert(tk.END, "4. Hover over all links - cursor should change to hand\n")
    
    root.mainloop()

if __name__ == "__main__":
    test_gui_links()