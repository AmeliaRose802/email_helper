#!/usr/bin/env python3
"""Quick test of COM email provider for backend API."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("Testing COM Email Provider for Backend API")
print("=" * 80)
print()

# Test 1: Import and create provider
print("[1/4] Testing COM provider import and creation...")
try:
    from backend.services.com_email_provider import COMEmailProvider
    provider = COMEmailProvider()
    print("  [OK] COM provider created successfully")
except Exception as e:
    print(f"  [ERROR] Failed to create provider: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Authenticate/Connect
print()
print("[2/4] Testing Outlook connection (authenticate)...")
try:
    success = provider.authenticate({})
    if success:
        print("  [OK] Successfully authenticated/connected to Outlook")
    else:
        print("  [ERROR] Authentication returned False")
        sys.exit(1)
except Exception as e:
    print(f"  [ERROR] Authentication failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Get emails
print()
print("[3/4] Testing email retrieval...")
try:
    emails = provider.get_emails(folder_name="Inbox", count=5, offset=0)
    print(f"  [OK] Retrieved {len(emails)} emails")
    
    if emails:
        print()
        print("  Sample email:")
        email = emails[0]
        print(f"    ID: {email.get('id', 'N/A')[:50]}...")
        print(f"    Subject: {email.get('subject', 'N/A')}")
        print(f"    From: {email.get('sender', 'N/A')}")
        print(f"    Received: {email.get('received_time', 'N/A')}")
        print(f"    Read: {email.get('is_read', False)}")
except Exception as e:
    print(f"  [ERROR] Failed to retrieve emails: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Get folders
print()
print("[4/4] Testing folder listing...")
try:
    folders = provider.get_folders()
    print(f"  [OK] Retrieved {len(folders)} folders")
    
    if folders:
        print()
        print("  Sample folders:")
        for folder in folders[:5]:
            print(f"    - {folder.get('name', 'N/A')}")
except Exception as e:
    print(f"  [ERROR] Failed to retrieve folders: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("[SUCCESS] All COM provider tests passed!")
print("=" * 80)
print()
print("The backend API should be able to connect to Outlook successfully.")
