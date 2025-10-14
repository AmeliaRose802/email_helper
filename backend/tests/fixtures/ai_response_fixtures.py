"""AI response fixtures for testing.

This module provides comprehensive AI response fixtures for testing AI
service workflows, including classification, action item extraction,
summarization, and duplicate detection.
"""

from typing import Dict, Any, List


def get_classification_response_required_action() -> Dict[str, Any]:
    """Get a classification response for required personal action.
    
    Returns:
        dict: Classification result
    """
    return {
        "category": "required_personal_action",
        "confidence": 0.92,
        "reasoning": "Email explicitly requests action from the recipient with a deadline",
        "requires_review": False
    }


def get_classification_response_optional_action() -> Dict[str, Any]:
    """Get a classification response for optional action.
    
    Returns:
        dict: Classification result
    """
    return {
        "category": "optional_action",
        "confidence": 0.78,
        "reasoning": "Email suggests action but does not require immediate response",
        "requires_review": True
    }


def get_classification_response_work_relevant() -> Dict[str, Any]:
    """Get a classification response for work relevant email.
    
    Returns:
        dict: Classification result
    """
    return {
        "category": "work_relevant",
        "confidence": 0.85,
        "reasoning": "Email contains work-related information but no action required",
        "requires_review": False
    }


def get_classification_response_fyi() -> Dict[str, Any]:
    """Get a classification response for FYI email.
    
    Returns:
        dict: Classification result
    """
    return {
        "category": "fyi_only",
        "confidence": 0.88,
        "reasoning": "Email is informational only, no action needed",
        "requires_review": False
    }


def get_classification_response_optional_event() -> Dict[str, Any]:
    """Get a classification response for optional event.
    
    Returns:
        dict: Classification result
    """
    return {
        "category": "optional_event",
        "confidence": 0.82,
        "reasoning": "Email invites to an optional event or activity",
        "requires_review": False
    }


def get_classification_response_job_listing() -> Dict[str, Any]:
    """Get a classification response for job listing.
    
    Returns:
        dict: Classification result
    """
    return {
        "category": "job_listing",
        "confidence": 0.95,
        "reasoning": "Email contains job opportunity or career-related content",
        "requires_review": False
    }


def get_classification_response_low_confidence() -> Dict[str, Any]:
    """Get a classification response with low confidence.
    
    Returns:
        dict: Classification result requiring review
    """
    return {
        "category": "required_personal_action",
        "confidence": 0.55,
        "reasoning": "Unclear if action is required",
        "requires_review": True
    }


def get_action_items_response_single() -> Dict[str, Any]:
    """Get action items response with a single action.
    
    Returns:
        dict: Action items result
    """
    return {
        "action_required": "Complete employee satisfaction survey",
        "due_date": "2025-01-20",
        "priority": "medium",
        "confidence": 0.88,
        "action_items": [
            {
                "task": "Complete employee satisfaction survey",
                "deadline": "2025-01-20",
                "priority": "medium",
                "estimated_time": "15 minutes"
            }
        ],
        "links": [
            "https://surveys.company.com/employee-satisfaction"
        ]
    }


def get_action_items_response_multiple() -> Dict[str, Any]:
    """Get action items response with multiple actions.
    
    Returns:
        dict: Action items result with multiple tasks
    """
    return {
        "action_required": "Review and approve Q4 budget",
        "due_date": "2025-01-20",
        "priority": "high",
        "confidence": 0.93,
        "action_items": [
            {
                "task": "Review budget line items for accuracy",
                "deadline": "2025-01-19",
                "priority": "high",
                "estimated_time": "30 minutes"
            },
            {
                "task": "Provide approval or feedback",
                "deadline": "2025-01-20",
                "priority": "high",
                "estimated_time": "15 minutes"
            },
            {
                "task": "Submit signed approval form",
                "deadline": "2025-01-20",
                "priority": "high",
                "estimated_time": "5 minutes"
            }
        ],
        "links": [
            "https://company.com/budget/q4",
            "https://company.com/forms/approval"
        ]
    }


def get_action_items_response_urgent() -> Dict[str, Any]:
    """Get action items response for urgent task.
    
    Returns:
        dict: Urgent action items result
    """
    return {
        "action_required": "Join emergency call for system outage",
        "due_date": "Immediately",
        "priority": "urgent",
        "confidence": 0.98,
        "action_items": [
            {
                "task": "Join emergency conference call",
                "deadline": "Immediately",
                "priority": "urgent",
                "estimated_time": "Unknown"
            },
            {
                "task": "Investigate database connection failure",
                "deadline": "Immediately",
                "priority": "urgent",
                "estimated_time": "Unknown"
            }
        ],
        "links": []
    }


def get_action_items_response_no_action() -> Dict[str, Any]:
    """Get action items response when no action is required.
    
    Returns:
        dict: No action required result
    """
    return {
        "action_required": None,
        "due_date": None,
        "priority": "none",
        "confidence": 0.90,
        "action_items": [],
        "links": []
    }


def get_summary_response_meeting() -> Dict[str, Any]:
    """Get summary response for meeting invitation.
    
    Returns:
        dict: Meeting summary
    """
    return {
        "summary": "Project status review meeting scheduled for tomorrow at 2:00 PM in Conference Room A.",
        "key_points": [
            "Meeting tomorrow at 2:00 PM",
            "Location: Conference Room A",
            "Duration: 1 hour",
            "Topics: Milestone review, budget, next quarter planning",
            "Attendance confirmation requested"
        ],
        "category": "required_personal_action",
        "sentiment": "neutral"
    }


def get_summary_response_action_required() -> Dict[str, Any]:
    """Get summary response for action-required email.
    
    Returns:
        dict: Action-required summary
    """
    return {
        "summary": "HR requests completion of employee satisfaction survey by Friday, January 20th.",
        "key_points": [
            "Survey deadline: Friday, January 20th",
            "Estimated time: 15 minutes",
            "Link provided to access survey",
            "Feedback is important to HR"
        ],
        "category": "required_personal_action",
        "sentiment": "positive"
    }


def get_summary_response_fyi() -> Dict[str, Any]:
    """Get summary response for FYI email.
    
    Returns:
        dict: FYI summary
    """
    return {
        "summary": "Weekly technology newsletter covering AI developments, cloud trends, and cybersecurity.",
        "key_points": [
            "AI and machine learning developments",
            "Cloud computing trends for 2025",
            "Cybersecurity best practices",
            "Full newsletter available online"
        ],
        "category": "fyi_only",
        "sentiment": "informational"
    }


def get_summary_response_urgent() -> Dict[str, Any]:
    """Get summary response for urgent email.
    
    Returns:
        dict: Urgent email summary
    """
    return {
        "summary": "URGENT: Production system down due to database connection failure. All users affected.",
        "key_points": [
            "Production system outage",
            "Database connection failure",
            "Started 10 minutes ago",
            "All users impacted",
            "Emergency call in progress",
            "All hands needed"
        ],
        "category": "required_personal_action",
        "sentiment": "urgent",
        "urgency_level": "critical"
    }


def get_duplicate_detection_response_with_duplicates() -> Dict[str, Any]:
    """Get duplicate detection response when duplicates are found.
    
    Returns:
        dict: Duplicate detection result
    """
    return {
        "duplicate_ids": ["duplicate-1a", "duplicate-1b"],
        "duplicate_groups": [
            {
                "primary": "original-1",
                "duplicates": ["duplicate-1a", "duplicate-1b"],
                "similarity": 0.98,
                "reason": "Nearly identical content and subject"
            }
        ],
        "total_duplicates": 2
    }


def get_duplicate_detection_response_no_duplicates() -> Dict[str, Any]:
    """Get duplicate detection response when no duplicates are found.
    
    Returns:
        dict: No duplicates result
    """
    return {
        "duplicate_ids": [],
        "duplicate_groups": [],
        "total_duplicates": 0
    }


def get_batch_classification_responses() -> List[Dict[str, Any]]:
    """Get batch classification responses for multiple emails.
    
    Returns:
        list: Multiple classification results
    """
    return [
        {
            "email_id": "action-required-1",
            "category": "required_personal_action",
            "confidence": 0.92,
            "reasoning": "Survey requires completion by deadline"
        },
        {
            "email_id": "meeting-invite-1",
            "category": "required_personal_action",
            "confidence": 0.88,
            "reasoning": "Meeting attendance confirmation requested"
        },
        {
            "email_id": "newsletter-1",
            "category": "fyi_only",
            "confidence": 0.90,
            "reasoning": "Informational newsletter, no action required"
        },
        {
            "email_id": "urgent-1",
            "category": "required_personal_action",
            "confidence": 0.98,
            "reasoning": "Critical system outage requiring immediate attention"
        },
        {
            "email_id": "job-listing-1",
            "category": "job_listing",
            "confidence": 0.95,
            "reasoning": "Job opportunity matching recipient's profile"
        },
        {
            "email_id": "team-collab-1",
            "category": "optional_action",
            "confidence": 0.80,
            "reasoning": "Code review requested but no strict deadline"
        },
        {
            "email_id": "spam-1",
            "category": "spam",
            "confidence": 0.99,
            "reasoning": "Suspicious promotional content with excessive claims"
        }
    ]


def get_error_response() -> Dict[str, Any]:
    """Get an error response for testing error handling.
    
    Returns:
        dict: Error response
    """
    return {
        "error": "AI service temporarily unavailable",
        "error_code": "SERVICE_UNAVAILABLE",
        "retry_after": 60
    }


def get_malformed_response() -> str:
    """Get a malformed response for testing parsing error handling.
    
    Returns:
        str: Non-JSON response string
    """
    return "This is not a valid JSON response"


def get_incomplete_response() -> Dict[str, Any]:
    """Get an incomplete response missing required fields.
    
    Returns:
        dict: Incomplete response
    """
    return {
        "category": "required_personal_action"
        # Missing confidence, reasoning, etc.
    }


def get_confidence_thresholds() -> Dict[str, float]:
    """Get confidence thresholds for classification.
    
    Returns:
        dict: Category confidence thresholds
    """
    return {
        "required_personal_action": 0.90,
        "optional_action": 0.80,
        "work_relevant": 0.80,
        "optional_event": 0.75,
        "job_listing": 0.85,
        "fyi_only": 0.70
    }


def get_prompty_template_list() -> List[str]:
    """Get list of available prompty templates.
    
    Returns:
        list: Template file names
    """
    return [
        "email_classifier.prompty",
        "action_item.prompty",
        "email_summarizer.prompty",
        "duplicate_detector.prompty",
        "batch_analyzer.prompty"
    ]
