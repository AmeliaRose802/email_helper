"""Demonstration of COM Email Provider usage.

This script shows how to use the COMEmailProvider to access Outlook
emails through the FastAPI backend interface.

Note: This script requires:
- Windows OS with pywin32 installed
- Microsoft Outlook installed and configured
- Running Outlook application
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.com_email_provider import COMEmailProvider


def demonstrate_com_provider():
    """Demonstrate basic COM provider operations."""
    print("=" * 70)
    print("COM Email Provider Demonstration")
    print("=" * 70)
    print()
    
    try:
        # Initialize the provider
        print("1. Initializing COM Email Provider...")
        provider = COMEmailProvider()
        print("   ✓ Provider initialized")
        print()
        
        # Connect to Outlook
        print("2. Connecting to Outlook...")
        if provider.authenticate({}):
            print("   ✓ Connected to Outlook successfully")
        else:
            print("   ✗ Failed to connect to Outlook")
            return
        print()
        
        # Get folders
        print("3. Retrieving email folders...")
        folders = provider.get_folders()
        print(f"   ✓ Found {len(folders)} folders:")
        for folder in folders[:5]:  # Show first 5 folders
            print(f"     - {folder['name']}")
        if len(folders) > 5:
            print(f"     ... and {len(folders) - 5} more")
        print()
        
        # Get emails
        print("4. Retrieving emails from Inbox...")
        emails = provider.get_emails("Inbox", count=5, offset=0)
        print(f"   ✓ Retrieved {len(emails)} emails:")
        for i, email in enumerate(emails, 1):
            print(f"     {i}. {email['subject'][:50]}")
            print(f"        From: {email['sender']}")
            print(f"        Read: {email['is_read']}")
        print()
        
        # Get email content
        if emails:
            print("5. Retrieving full content of first email...")
            email_id = emails[0]['id']
            content = provider.get_email_content(email_id)
            if content:
                body_preview = content['body'][:200].replace('\n', ' ')
                print(f"   ✓ Body preview: {body_preview}...")
            print()
        
        print("=" * 70)
        print("Demonstration completed successfully!")
        print("=" * 70)
        
    except ImportError as e:
        print(f"✗ Error: {e}")
        print("\nThis demonstration requires:")
        print("  - Windows OS")
        print("  - pywin32 package (pip install pywin32)")
        print("  - Microsoft Outlook installed and configured")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demonstrate_com_provider()
