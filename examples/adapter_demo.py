"""Example demonstrating the adapter pattern for backend integration.

This script shows how to use OutlookEmailAdapter and AIProcessorAdapter
to build backend services without duplicating existing functionality.

Usage:
    python examples/adapter_demo.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adapters import OutlookEmailAdapter, AIProcessorAdapter


def demo_email_adapter():
    """Demonstrate OutlookEmailAdapter usage."""
    print("=" * 60)
    print("EMAIL ADAPTER DEMO")
    print("=" * 60)
    
    # Create adapter
    print("\n1. Creating OutlookEmailAdapter...")
    email_adapter = OutlookEmailAdapter()
    
    # Connect to Outlook
    print("2. Connecting to Outlook...")
    if not email_adapter.connect():
        print("   ❌ Failed to connect to Outlook")
        print("   Make sure Outlook is installed and accessible")
        return
    print("   ✅ Connected successfully")
    
    # Get folders
    print("\n3. Listing available folders...")
    folders = email_adapter.get_folders()
    print(f"   Found {len(folders)} folders:")
    for folder in folders[:5]:  # Show first 5
        print(f"   - {folder['name']}")
    
    # Get recent emails
    print("\n4. Retrieving recent emails from Inbox...")
    try:
        emails = email_adapter.get_emails("Inbox", count=5, offset=0)
        print(f"   Retrieved {len(emails)} emails:")
        
        for i, email in enumerate(emails, 1):
            print(f"\n   Email {i}:")
            print(f"   Subject: {email['subject'][:50]}...")
            print(f"   From: {email['sender']}")
            print(f"   Received: {email['received_time']}")
            print(f"   Read: {email['is_read']}")
            
            # Get full body of first email
            if i == 1:
                print("\n5. Getting full body of first email...")
                body = email_adapter.get_email_body(email['id'])
                print(f"   Body length: {len(body)} characters")
                print(f"   Preview: {body[:100]}...")
                
    except Exception as e:
        print(f"   ❌ Error retrieving emails: {e}")


def demo_ai_adapter():
    """Demonstrate AIProcessorAdapter usage."""
    print("\n\n")
    print("=" * 60)
    print("AI ADAPTER DEMO")
    print("=" * 60)
    
    # Create adapter
    print("\n1. Creating AIProcessorAdapter...")
    ai_adapter = AIProcessorAdapter()
    print("   ✅ Adapter ready")
    
    # Example email content
    email_content = """Subject: Urgent: Project Deadline Tomorrow

From: manager@company.com

Hi Team,

Please ensure that the quarterly report is completed and submitted by tomorrow at 5 PM.
This is critical for our board meeting on Wednesday.

Key items to include:
- Q4 revenue figures
- Customer satisfaction metrics
- Team growth statistics

Let me know if you have any questions.

Best regards,
Manager
"""
    
    # Classify email
    print("\n2. Classifying email...")
    print(f"   Email subject: 'Urgent: Project Deadline Tomorrow'")
    
    try:
        classification = ai_adapter.classify_email(email_content)
        
        print(f"\n   Classification Results:")
        print(f"   Category: {classification['category']}")
        print(f"   Confidence: {classification['confidence']:.2%}")
        print(f"   Requires Review: {classification['requires_review']}")
        print(f"   Reasoning: {classification['reasoning'][:100]}...")
        
        if classification.get('alternatives'):
            print(f"\n   Alternative Categories:")
            for alt in classification['alternatives'][:3]:
                print(f"   - {alt.get('category', 'N/A')}: {alt.get('confidence', 0):.2%}")
    
    except Exception as e:
        print(f"   ❌ Classification error: {e}")
    
    # Extract action items
    print("\n3. Extracting action items...")
    
    try:
        action_items = ai_adapter.extract_action_items(email_content)
        
        print(f"\n   Action Item Results:")
        print(f"   Due Date: {action_items.get('due_date', 'N/A')}")
        print(f"   Urgency: {action_items.get('urgency', 'N/A')}")
        print(f"   Action Required: {action_items.get('action_required', 'N/A')[:100]}...")
        
        if action_items.get('action_items'):
            print(f"\n   Extracted Action Items:")
            for item in action_items['action_items']:
                print(f"   - {item}")
    
    except Exception as e:
        print(f"   ❌ Action item extraction error: {e}")
    
    # Generate summary
    print("\n4. Generating email summary...")
    
    try:
        summary = ai_adapter.generate_summary(email_content, summary_type="brief")
        
        print(f"\n   Summary:")
        print(f"   {summary.get('summary', 'N/A')}")
        print(f"   Confidence: {summary.get('confidence', 0):.2%}")
        
        if summary.get('key_points'):
            print(f"\n   Key Points:")
            for point in summary['key_points']:
                print(f"   - {point}")
    
    except Exception as e:
        print(f"   ❌ Summary generation error: {e}")


def demo_batch_analysis():
    """Demonstrate batch email analysis."""
    print("\n\n")
    print("=" * 60)
    print("BATCH ANALYSIS DEMO")
    print("=" * 60)
    
    # Create adapters
    print("\n1. Initializing adapters...")
    email_adapter = OutlookEmailAdapter()
    ai_adapter = AIProcessorAdapter()
    
    # Connect to Outlook
    if not email_adapter.connect():
        print("   ❌ Failed to connect to Outlook")
        return
    print("   ✅ Adapters ready")
    
    # Get batch of emails
    print("\n2. Retrieving batch of emails...")
    try:
        emails = email_adapter.get_emails("Inbox", count=10)
        print(f"   Retrieved {len(emails)} emails")
        
        # Analyze batch
        print("\n3. Performing holistic batch analysis...")
        batch_result = ai_adapter.analyze_batch(emails)
        
        print(f"\n   Batch Analysis Results:")
        print(f"   Total Emails: {batch_result['total_emails']}")
        print(f"   High Priority: {batch_result['high_priority']}")
        print(f"   Action Required: {batch_result['action_required']}")
        print(f"   Conversation Threads: {len(batch_result.get('threads', []))}")
        
        if batch_result.get('recommendations'):
            print(f"\n   Recommendations:")
            for rec in batch_result['recommendations'][:5]:
                print(f"   - {rec}")
        
        if batch_result.get('summary'):
            print(f"\n   Summary:")
            print(f"   {batch_result['summary'][:200]}...")
    
    except Exception as e:
        print(f"   ❌ Batch analysis error: {e}")


def demo_integration_pattern():
    """Demonstrate FastAPI integration pattern."""
    print("\n\n")
    print("=" * 60)
    print("FASTAPI INTEGRATION PATTERN")
    print("=" * 60)
    
    print("""
The adapters are designed for seamless FastAPI integration.
Here's how you would use them in a FastAPI endpoint:

```python
from fastapi import FastAPI, Depends
from adapters import OutlookEmailAdapter, AIProcessorAdapter

app = FastAPI()

# Global singleton instances
_email_adapter = None
_ai_adapter = None

def get_email_adapter() -> OutlookEmailAdapter:
    '''FastAPI dependency for email adapter.'''
    global _email_adapter
    if _email_adapter is None:
        _email_adapter = OutlookEmailAdapter()
        _email_adapter.connect()
    return _email_adapter

def get_ai_adapter() -> AIProcessorAdapter:
    '''FastAPI dependency for AI adapter.'''
    global _ai_adapter
    if _ai_adapter is None:
        _ai_adapter = AIProcessorAdapter()
    return _ai_adapter

# Use in endpoints
@app.get("/api/emails")
async def get_emails(
    count: int = 50,
    offset: int = 0,
    email_adapter: OutlookEmailAdapter = Depends(get_email_adapter)
):
    emails = email_adapter.get_emails("Inbox", count=count, offset=offset)
    return {"emails": emails, "count": len(emails)}

@app.post("/api/classify")
async def classify_email(
    email_content: str,
    ai_adapter: AIProcessorAdapter = Depends(get_ai_adapter)
):
    result = ai_adapter.classify_email(email_content)
    return result

@app.post("/api/analyze-batch")
async def analyze_batch(
    email_adapter: OutlookEmailAdapter = Depends(get_email_adapter),
    ai_adapter: AIProcessorAdapter = Depends(get_ai_adapter)
):
    # Get recent emails
    emails = email_adapter.get_emails("Inbox", count=20)
    
    # Analyze batch
    analysis = ai_adapter.analyze_batch(emails)
    
    return {
        "emails_analyzed": len(emails),
        "analysis": analysis
    }
```

Key Benefits:
- Clean dependency injection
- No code duplication
- Easy testing with mocks
- Reuses existing COM and AI logic
- Backward compatible
    """)


def main():
    """Run all demo examples."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       ADAPTER PATTERN DEMO - BACKEND INTEGRATION          ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("\nThis demo shows how to use the adapter pattern to integrate")
    print("existing OutlookManager and AIProcessor functionality with")
    print("the FastAPI backend without code duplication.\n")
    
    try:
        # Run demos
        demo_email_adapter()
        demo_ai_adapter()
        demo_batch_analysis()
        demo_integration_pattern()
        
        print("\n\n")
        print("=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print("\n✅ Adapter pattern successfully demonstrated!")
        print("\nNext steps:")
        print("1. Review adapter code in src/adapters/")
        print("2. Check unit tests in test/test_*_adapter.py")
        print("3. Read docs/implementation/ADAPTER_PATTERN_IMPLEMENTATION.md")
        print("4. Integrate adapters with FastAPI (Tasks T1.1-T1.3)")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
