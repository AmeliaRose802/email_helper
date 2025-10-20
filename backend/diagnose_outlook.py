#!/usr/bin/env python3
"""Diagnostic script to check Outlook COM connectivity.

This script helps troubleshoot Outlook COM connection issues by:
1. Checking if pywin32 is installed
2. Checking if Outlook process is running
3. Attempting to connect to Outlook COM interface
4. Testing basic Outlook operations
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("Outlook COM Connection Diagnostic Tool")
print("=" * 80)
print()

# Step 1: Check pywin32
print("[1/5] Checking pywin32 installation...")
try:
    import win32com.client
    print("  [OK] pywin32 is installed")
except ImportError as e:
    print(f"  [ERROR] pywin32 not found: {e}")
    print("  Please install with: pip install pywin32")
    sys.exit(1)

# Step 2: Check if Outlook process is running
print()
print("[2/5] Checking if Outlook is running...")
try:
    import psutil
    outlook_running = any(
        'outlook' in p.name().lower()
        for p in psutil.process_iter(['name'])
    )
    if outlook_running:
        print("  [OK] Outlook process found")
    else:
        print("  [WARNING] Outlook process not found")
        print("  Please start Microsoft Outlook before running this application")
except ImportError:
    print("  [SKIP] psutil not installed (optional check)")
except Exception as e:
    print(f"  [WARNING] Could not check processes: {e}")

# Step 3: Try to connect to Outlook COM interface
print()
print("[3/5] Attempting to connect to Outlook COM interface...")
try:
    outlook = win32com.client.Dispatch("Outlook.Application")
    print("  [OK] Successfully created Outlook COM object")
except Exception as e:
    print(f"  [ERROR] Failed to create Outlook COM object: {e}")
    print()
    print("Possible causes:")
    print("  - Outlook is not installed")
    print("  - Outlook is not running")
    print("  - COM security policy is blocking access")
    print("  - Outlook is in a corrupted state")
    print()
    print("Suggested fixes:")
    print("  1. Start Microsoft Outlook")
    print("  2. Restart Outlook if it's already running")
    print("  3. Run this script with administrator privileges")
    sys.exit(1)

# Step 4: Try to access MAPI namespace
print()
print("[4/5] Attempting to access MAPI namespace...")
try:
    namespace = outlook.GetNamespace("MAPI")
    print("  [OK] Successfully accessed MAPI namespace")
except Exception as e:
    print(f"  [ERROR] Failed to access MAPI namespace: {e}")
    sys.exit(1)

# Step 5: Try to access Inbox
print()
print("[5/5] Attempting to access Inbox folder...")
try:
    inbox = namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
    item_count = inbox.Items.Count
    print(f"  [OK] Successfully accessed Inbox ({item_count} items)")
except Exception as e:
    print(f"  [ERROR] Failed to access Inbox: {e}")
    print()
    print("Possible causes:")
    print("  - Outlook profile not configured")
    print("  - No default email account set up")
    print("  - Outlook is in offline mode")
    print()
    print("Suggested fixes:")
    print("  1. Open Outlook and ensure you can see your emails")
    print("  2. Check that Outlook is connected (not in offline mode)")
    print("  3. Verify your email account is properly configured")
    sys.exit(1)

# Success!
print()
print("=" * 80)
print("[SUCCESS] All diagnostic checks passed!")
print("=" * 80)
print()
print("Outlook COM interface is working correctly.")
print("The Email Helper backend should be able to connect to Outlook.")
print()

# Try to test the actual adapter
print("[BONUS] Testing OutlookEmailAdapter...")
try:
    from src.adapters.outlook_email_adapter import OutlookEmailAdapter
    
    adapter = OutlookEmailAdapter()
    if adapter.connect():
        print("  [OK] OutlookEmailAdapter connected successfully")
        
        # Try to get a few emails
        emails = adapter.get_emails("Inbox", count=5)
        print(f"  [OK] Retrieved {len(emails)} sample emails from Inbox")
        
        if emails:
            print()
            print("Sample email (first in list):")
            first_email = emails[0]
            print(f"  Subject: {first_email.get('subject', 'N/A')}")
            print(f"  From: {first_email.get('sender', 'N/A')}")
            print(f"  Received: {first_email.get('received_time', 'N/A')}")
    else:
        print("  [ERROR] OutlookEmailAdapter failed to connect")
        
except Exception as e:
    print(f"  [ERROR] Failed to test OutlookEmailAdapter: {e}")
    import traceback
    traceback.print_exc()

print()
print("Diagnostic complete!")
