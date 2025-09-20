#!/usr/bin/env python3
"""
Test if EntryID changes when an email is moved
"""

import sys
import os
sys.path.append('src')

from outlook_manager import OutlookManager

def test_entryid_after_move():
    """Test if EntryID changes when an email is moved"""
    
    # Connect to Outlook
    outlook_manager = OutlookManager()
    try:
        outlook_manager.connect_to_outlook()
        print("✅ Connected to Outlook")
    except Exception as e:
        print(f"❌ Failed to connect to Outlook: {e}")
        return
    
    # Get an email from inbox
    try:
        inbox = outlook_manager.namespace.GetDefaultFolder(6)  # Inbox
        emails = inbox.Items
        
        if emails.Count == 0:
            print("❌ No emails in inbox to test with")
            return
            
        test_email = emails[1]  # Get first email
        original_subject = test_email.Subject
        original_entry_id = test_email.EntryID
        
        print(f"Test email: {original_subject[:30]}...")
        print(f"Original EntryID: {original_entry_id[:40]}...")
        
        # Try to access it again using the EntryID
        try:
            same_email = outlook_manager.namespace.GetItemFromID(original_entry_id)
            print(f"✅ Original EntryID is valid: {same_email.Subject[:30]}...")
        except Exception as e:
            print(f"❌ Original EntryID is invalid: {e}")
            
    except Exception as e:
        print(f"❌ Error accessing inbox: {e}")

if __name__ == "__main__":
    test_entryid_after_move()
