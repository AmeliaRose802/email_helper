"""Email fixtures for testing.

This module provides comprehensive email data fixtures for testing email
processing workflows, including various email types, edge cases, and
realistic email content.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any


def get_simple_email(email_id: str = "simple-1") -> Dict[str, Any]:
    """Get a simple email for basic testing.

    Args:
        email_id: Unique identifier for the email

    Returns:
        dict: Simple email data
    """
    return {
        "id": email_id,
        "subject": "Simple Test Email",
        "body": "This is a simple test email body.",
        "from": "sender@example.com",
        "from_name": "Test Sender",
        "to": "recipient@example.com",
        "received_time": datetime.now().isoformat(),
        "is_read": False,
        "categories": [],
        "conversation_id": f"conv-{email_id}"
    }


def get_action_required_email() -> Dict[str, Any]:
    """Get an email that requires action.

    Returns:
        dict: Email with action items
    """
    return {
        "id": "action-required-1",
        "subject": "Action Required: Complete Survey by Friday",
        "body": """Hi,

Please complete the employee satisfaction survey by this Friday, January 20th.
The survey takes approximately 15 minutes.

Access the survey here: https://surveys.company.com/employee-satisfaction

Your feedback is important to us.

Thank you,
HR Team""",
        "from": "hr@company.com",
        "from_name": "HR Department",
        "to": "employee@company.com",
        "received_time": datetime.now().isoformat(),
        "is_read": False,
        "categories": ["Work"],
        "conversation_id": "conv-action-1",
        "importance": "high"
    }


def get_meeting_invitation_email() -> Dict[str, Any]:
    """Get a meeting invitation email.

    Returns:
        dict: Meeting invitation data
    """
    tomorrow = datetime.now() + timedelta(days=1)
    return {
        "id": "meeting-invite-1",
        "subject": "Meeting: Project Status Review",
        "body": f"""You are invited to a meeting:

When: {tomorrow.strftime('%B %d, %Y at 2:00 PM')}
Where: Conference Room A
Duration: 1 hour

Agenda:
- Project milestone review
- Budget discussion
- Next quarter planning

Please confirm your attendance.

Best regards,
Project Manager""",
        "from": "pm@company.com",
        "from_name": "Project Manager",
        "to": "team@company.com",
        "received_time": datetime.now().isoformat(),
        "is_read": False,
        "categories": ["Meeting"],
        "conversation_id": "conv-meeting-1",
        "has_attachments": False
    }


def get_newsletter_email() -> Dict[str, Any]:
    """Get a newsletter/FYI email.

    Returns:
        dict: Newsletter email data
    """
    return {
        "id": "newsletter-1",
        "subject": "Weekly Tech Newsletter - January 2025",
        "body": """Welcome to our weekly technology newsletter!

This week's highlights:
- New AI developments in machine learning
- Cloud computing trends for 2025
- Best practices for cybersecurity

Read the full newsletter at: https://newsletter.techcompany.com

Stay informed!
Tech Newsletter Team""",
        "from": "newsletter@techcompany.com",
        "from_name": "Tech Newsletter",
        "to": "subscriber@example.com",
        "received_time": (datetime.now() - timedelta(days=1)).isoformat(),
        "is_read": True,
        "categories": ["Newsletter", "FYI"],
        "conversation_id": "conv-newsletter-1"
    }


def get_urgent_email() -> Dict[str, Any]:
    """Get an urgent email requiring immediate attention.

    Returns:
        dict: Urgent email data
    """
    return {
        "id": "urgent-1",
        "subject": "URGENT: Production System Down",
        "body": """URGENT ALERT

Our production system is currently experiencing downtime.

Issue: Database connection failure
Started: 10 minutes ago
Impact: All users affected

Please join the emergency call immediately:
Phone: 555-0100
Conference ID: 12345

We need all hands on deck.

IT Operations""",
        "from": "alerts@company.com",
        "from_name": "IT Operations",
        "to": "engineers@company.com",
        "received_time": (datetime.now() - timedelta(minutes=10)).isoformat(),
        "is_read": False,
        "categories": ["Urgent"],
        "conversation_id": "conv-urgent-1",
        "importance": "high"
    }


def get_job_listing_email() -> Dict[str, Any]:
    """Get a job listing email.

    Returns:
        dict: Job listing data
    """
    return {
        "id": "job-listing-1",
        "subject": "Senior Software Engineer - Remote Position",
        "body": """We're hiring!

Position: Senior Software Engineer
Location: Remote (US-based)
Salary: $130k - $180k

Requirements:
- 5+ years of experience
- Python, JavaScript proficiency
- Cloud platform experience (AWS/Azure)
- Strong communication skills

This role matches your background and skills. Apply now!

Apply here: https://careers.techcompany.com/senior-engineer

Recruiting Team""",
        "from": "recruiting@techcompany.com",
        "from_name": "Tech Company Recruiting",
        "to": "candidate@example.com",
        "received_time": (datetime.now() - timedelta(hours=6)).isoformat(),
        "is_read": False,
        "categories": ["Career"],
        "conversation_id": "conv-job-1"
    }


def get_team_collaboration_email() -> Dict[str, Any]:
    """Get a team collaboration email.

    Returns:
        dict: Team collaboration data
    """
    return {
        "id": "team-collab-1",
        "subject": "Code Review: New Feature Branch",
        "body": """Hi team,

I've pushed a new feature branch that needs review:

Branch: feature/user-authentication
Pull Request: #234
Files changed: 12

Key changes:
- Implemented JWT authentication
- Added user session management
- Updated API endpoints for auth

Please review when you have a chance this week.

Thanks!
Developer""",
        "from": "developer@company.com",
        "from_name": "Team Developer",
        "to": "team@company.com",
        "received_time": (datetime.now() - timedelta(hours=3)).isoformat(),
        "is_read": False,
        "categories": ["Work", "Team"],
        "conversation_id": "conv-team-1"
    }


def get_spam_email() -> Dict[str, Any]:
    """Get a spam/promotional email.

    Returns:
        dict: Spam email data
    """
    return {
        "id": "spam-1",
        "subject": "🎉 AMAZING OFFER: 90% OFF Everything!!!",
        "body": """LIMITED TIME ONLY!

Get 90% off ALL products! This is not a drill!

Click here NOW: http://suspicious-site.xyz/offer

Hurry! Offer expires in 24 hours!

Buy now or regret forever!

Unsubscribe: [broken link]""",
        "from": "deals@random-site.xyz",
        "from_name": "Amazing Deals",
        "to": "victim@example.com",
        "received_time": (datetime.now() - timedelta(hours=12)).isoformat(),
        "is_read": False,
        "categories": ["Junk"],
        "conversation_id": "conv-spam-1"
    }


def get_email_batch_for_classification() -> List[Dict[str, Any]]:
    """Get a batch of emails for classification testing.

    Returns:
        list: Batch of diverse emails
    """
    return [
        get_action_required_email(),
        get_meeting_invitation_email(),
        get_newsletter_email(),
        get_urgent_email(),
        get_job_listing_email(),
        get_team_collaboration_email(),
        get_spam_email()
    ]


def get_duplicate_emails() -> List[Dict[str, Any]]:
    """Get a set of duplicate emails for testing duplicate detection.

    Returns:
        list: Emails with duplicates
    """
    original_time = datetime.now() - timedelta(hours=1)

    return [
        {
            "id": "original-1",
            "subject": "Important Project Update",
            "body": "The project deadline has been moved to next Friday. Please adjust your schedules accordingly.",
            "from": "manager@company.com",
            "from_name": "Manager",
            "to": "team@company.com",
            "received_time": original_time.isoformat(),
            "is_read": False,
            "categories": [],
            "conversation_id": "conv-duplicate-1"
        },
        {
            "id": "duplicate-1a",
            "subject": "Re: Important Project Update",
            "body": "The project deadline has been moved to next Friday. Please adjust your schedules accordingly.",
            "from": "manager@company.com",
            "from_name": "Manager",
            "to": "team@company.com",
            "received_time": (original_time + timedelta(minutes=5)).isoformat(),
            "is_read": False,
            "categories": [],
            "conversation_id": "conv-duplicate-1"
        },
        {
            "id": "duplicate-1b",
            "subject": "FW: Important Project Update",
            "body": "The project deadline has been moved to next Friday. Please adjust your schedules accordingly.",
            "from": "assistant@company.com",
            "from_name": "Assistant",
            "to": "team@company.com",
            "received_time": (original_time + timedelta(minutes=10)).isoformat(),
            "is_read": False,
            "categories": [],
            "conversation_id": "conv-duplicate-1"
        }
    ]


def get_conversation_thread() -> List[Dict[str, Any]]:
    """Get a conversation thread for testing thread operations.

    Returns:
        list: Emails in a conversation thread
    """
    thread_start = datetime.now() - timedelta(days=2)

    return [
        {
            "id": "thread-1",
            "subject": "Discussion: API Design",
            "body": "What are your thoughts on the new API design?",
            "from": "dev1@company.com",
            "from_name": "Developer 1",
            "to": "team@company.com",
            "received_time": thread_start.isoformat(),
            "is_read": True,
            "categories": [],
            "conversation_id": "conv-thread-123"
        },
        {
            "id": "thread-2",
            "subject": "Re: Discussion: API Design",
            "body": "I think we should use REST principles. What do you think?",
            "from": "dev2@company.com",
            "from_name": "Developer 2",
            "to": "team@company.com",
            "received_time": (thread_start + timedelta(hours=2)).isoformat(),
            "is_read": True,
            "categories": [],
            "conversation_id": "conv-thread-123"
        },
        {
            "id": "thread-3",
            "subject": "Re: Discussion: API Design",
            "body": "REST makes sense. Let's also consider GraphQL for flexibility.",
            "from": "dev1@company.com",
            "from_name": "Developer 1",
            "to": "team@company.com",
            "received_time": (thread_start + timedelta(hours=5)).isoformat(),
            "is_read": False,
            "categories": [],
            "conversation_id": "conv-thread-123"
        }
    ]


def get_email_with_attachments() -> Dict[str, Any]:
    """Get an email with attachments.

    Returns:
        dict: Email with attachment metadata
    """
    return {
        "id": "attachment-email-1",
        "subject": "Q4 Financial Report",
        "body": "Please review the attached Q4 financial report. Let me know if you have any questions.",
        "from": "finance@company.com",
        "from_name": "Finance Team",
        "to": "executives@company.com",
        "received_time": datetime.now().isoformat(),
        "is_read": False,
        "categories": ["Important"],
        "conversation_id": "conv-attachments-1",
        "has_attachments": True,
        "attachments": [
            {
                "name": "Q4_Financial_Report.pdf",
                "size": 2048576,
                "type": "application/pdf"
            },
            {
                "name": "Summary.xlsx",
                "size": 512000,
                "type": "application/vnd.ms-excel"
            }
        ]
    }


def get_edge_case_emails() -> List[Dict[str, Any]]:
    """Get edge case emails for testing robustness.

    Returns:
        list: Edge case email data
    """
    return [
        # Empty body
        {
            "id": "edge-empty-body",
            "subject": "Empty Email",
            "body": "",
            "from": "sender@example.com",
            "from_name": "Sender",
            "to": "recipient@example.com",
            "received_time": datetime.now().isoformat(),
            "is_read": False,
            "categories": [],
            "conversation_id": "conv-edge-1"
        },
        # Very long subject
        {
            "id": "edge-long-subject",
            "subject": "A" * 500,
            "body": "This email has a very long subject line.",
            "from": "sender@example.com",
            "from_name": "Sender",
            "to": "recipient@example.com",
            "received_time": datetime.now().isoformat(),
            "is_read": False,
            "categories": [],
            "conversation_id": "conv-edge-2"
        },
        # Special characters
        {
            "id": "edge-special-chars",
            "subject": "Test: 特殊文字 émojis 🎉 symbols $@#%",
            "body": "Testing special characters: 日本語 français español 中文 🚀🎨💻",
            "from": "sender@example.com",
            "from_name": "Sender",
            "to": "recipient@example.com",
            "received_time": datetime.now().isoformat(),
            "is_read": False,
            "categories": [],
            "conversation_id": "conv-edge-3"
        },
        # No sender name
        {
            "id": "edge-no-sender-name",
            "subject": "Email without sender name",
            "body": "This email has no sender name.",
            "from": "noreply@example.com",
            "from_name": "",
            "to": "recipient@example.com",
            "received_time": datetime.now().isoformat(),
            "is_read": False,
            "categories": [],
            "conversation_id": "conv-edge-4"
        }
    ]
