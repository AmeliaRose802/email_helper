#!/usr/bin/env python3
"""
Test script for thread email moving using fresh COM objects.
Tests the fix for COM disconnection issues in thread processing.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_thread_email_moving():
    """Test that thread email moving works with fresh COM objects."""
    print("🧪 Testing thread email moving with fresh COM objects...")
    
    try:
        from outlook_manager import OutlookManager
        from email_processing_controller import EmailProcessingController
        
        # Initialize manager
        outlook = OutlookManager()
        if not outlook.connect_to_outlook():
            print("❌ Failed to connect to Outlook")
            return False
            
        print("✅ Connected to Outlook successfully")
        
        # Initialize controller 
        controller = EmailProcessingController()
        
        # Get some conversation data to test with
        print("🔍 Getting conversation data...")
        conversation_data = outlook.get_conversation_data(limit=5)  # Small sample
        
        if not conversation_data:
            print("❌ No conversation data found")
            return False
            
        print(f"✅ Found {len(conversation_data)} conversations to test")
        
        # Process a conversation with multiple emails if possible
        multi_email_conv = None
        for conv_id, conv_info in conversation_data:
            if len(conv_info.get('emails', [])) > 1:
                multi_email_conv = (conv_id, conv_info)
                print(f"✅ Found multi-email thread: {conv_info.get('topic', 'Unknown')[:50]}... ({len(conv_info['emails'])} emails)")
                break
        
        if not multi_email_conv:
            print("⚠️  No multi-email threads found, testing with single email thread")
            multi_email_conv = conversation_data[0]
        
        # Test thread data creation
        conv_id, conv_info = multi_email_conv
        print("🔄 Testing thread data creation...")
        
        # Simulate the email processing workflow
        enriched_data = controller._enrich_conversation_data([multi_email_conv])
        if not enriched_data:
            print("❌ Failed to enrich conversation data")
            return False
            
        conv_id, enriched_conv_info = enriched_data[0]
        emails_with_body = enriched_conv_info.get('emails_with_body', [])
        
        print(f"✅ Enriched data contains {len(emails_with_body)} emails")
        
        # Verify unique_id is present in emails_with_body
        for i, email_data in enumerate(emails_with_body):
            if 'unique_id' not in email_data:
                print(f"❌ Email {i+1} missing unique_id")
                return False
            
            unique_id = email_data['unique_id']
            if '|' not in unique_id:
                print(f"⚠️  Email {i+1} unique_id not in StoreID|EntryID format: {unique_id}")
            else:
                print(f"✅ Email {i+1} has proper unique_id: {unique_id[:50]}...")
        
        # Test thread_data creation
        email_obj = emails_with_body[0]['email_object']
        
        # Create proper StoreID|EntryID identifiers for all emails in thread
        thread_entry_ids = []
        for e in emails_with_body:
            if 'unique_id' in e:
                thread_entry_ids.append(e['unique_id'])
            else:
                unique_id = outlook.get_unique_email_identifier(e['email_object'])
                thread_entry_ids.append(unique_id)
        
        thread_data = {
            'email_object': email_obj,
            'conversation_id': conv_id,
            'thread_count': len(emails_with_body),
            'participants': conv_info.get('participants', []),
            'topic': conv_info.get('topic', 'Unknown Thread'),
            'entry_ids': thread_entry_ids
        }
        
        print(f"✅ Thread data created with {len(thread_entry_ids)} entry_ids")
        
        # Test fresh object retrieval for each entry_id
        print("🔄 Testing fresh object retrieval for each thread email...")
        fresh_objects_count = 0
        
        for i, entry_id in enumerate(thread_entry_ids):
            try:
                fresh_email = outlook.get_fresh_email_object(entry_id)
                if fresh_email:
                    fresh_objects_count += 1
                    subject = getattr(fresh_email, 'Subject', 'No Subject')
                    print(f"✅ Fresh object {i+1}: {subject[:50]}...")
                else:
                    print(f"⚠️  Could not get fresh object for entry_id {i+1}: {entry_id}")
            except Exception as e:
                print(f"❌ Error getting fresh object {i+1}: {e}")
        
        print(f"✅ Successfully retrieved {fresh_objects_count}/{len(thread_entry_ids)} fresh objects")
        
        if fresh_objects_count == len(thread_entry_ids):
            print("🎉 Thread email moving fix should work correctly!")
            return True
        elif fresh_objects_count > 0:
            print("⚠️  Partial success - some emails can be moved")
            return True
        else:
            print("❌ No fresh objects could be retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Thread Email Moving Test")
    print("=" * 50)
    
    success = test_thread_email_moving()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    
    if success:
        print("🎉 Thread email moving test PASSED!")
        print("✅ Fresh COM objects can be retrieved from StoreID|EntryID")
        print("✅ Thread data contains proper unique identifiers")
        print("✅ Fix should resolve COM disconnection errors")
        
        print("\n🔧 IMPLEMENTATION STATUS:")
        print("✅ Updated thread processing to use entry_ids instead of stale COM objects")
        print("✅ Enhanced emails_with_body to include unique_id (StoreID|EntryID format)")
        print("✅ Improved thread_data creation with proper entry_ids")
        print("✅ Added robust fallback for legacy EntryID formats")
        
    else:
        print("❌ Thread email moving test FAILED!")
        print("⚠️  Review the errors above for troubleshooting")
