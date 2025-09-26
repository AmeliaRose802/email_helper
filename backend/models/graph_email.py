"""Graph API email models for FastAPI Email Helper API."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class GraphEmailAddress(BaseModel):
    """Graph API email address model."""
    name: Optional[str] = None
    address: str


class GraphRecipient(BaseModel):
    """Graph API recipient model."""
    emailAddress: GraphEmailAddress


class GraphEmailBody(BaseModel):
    """Graph API email body model."""
    contentType: str = "text"  # "text" or "html"
    content: str


class GraphMessage(BaseModel):
    """Graph API message model."""
    id: str
    subject: Optional[str] = None
    from_: Optional[GraphRecipient] = Field(None, alias="from")
    toRecipients: List[GraphRecipient] = []
    receivedDateTime: datetime
    hasAttachments: bool = False
    isRead: bool = False
    conversationId: Optional[str] = None
    categories: List[str] = []
    importance: str = "normal"  # "low", "normal", "high"
    body: Optional[GraphEmailBody] = None
    bodyPreview: Optional[str] = None


class GraphMailFolder(BaseModel):
    """Graph API mail folder model."""
    id: str
    displayName: str
    parentFolderId: Optional[str] = None
    childFolderCount: int = 0
    unreadItemCount: int = 0
    totalItemCount: int = 0


class EmailNormalizer:
    """Utility class to normalize Graph API email data to internal format."""
    
    @staticmethod
    def normalize_graph_message(graph_message: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Graph API message to internal email format.
        
        Args:
            graph_message: Raw Graph API message object
            
        Returns:
            Normalized email data matching EmailProvider interface
        """
        # Parse sender information
        sender_info = graph_message.get("from", {})
        sender_email = ""
        sender_name = ""
        
        if sender_info and "emailAddress" in sender_info:
            email_addr = sender_info["emailAddress"]
            sender_email = email_addr.get("address", "")
            sender_name = email_addr.get("name", "")
        
        # Parse recipients
        recipients = []
        to_recipients = graph_message.get("toRecipients", [])
        for recipient in to_recipients:
            if "emailAddress" in recipient:
                recipients.append(recipient["emailAddress"].get("address", ""))
        
        # Parse body content
        body_content = ""
        body_info = graph_message.get("body", {})
        if body_info:
            body_content = body_info.get("content", "")
        
        # Use bodyPreview as fallback
        if not body_content:
            body_content = graph_message.get("bodyPreview", "")
        
        # Parse datetime
        received_time = graph_message.get("receivedDateTime", "")
        if received_time:
            try:
                # Graph API returns ISO format datetime
                received_datetime = datetime.fromisoformat(received_time.replace("Z", "+00:00"))
            except ValueError:
                received_datetime = datetime.now()
        else:
            received_datetime = datetime.now()
        
        return {
            "id": graph_message.get("id", ""),
            "subject": graph_message.get("subject", ""),
            "sender": sender_email,
            "sender_name": sender_name,
            "recipient": recipients[0] if recipients else "",
            "recipients": recipients,
            "body": body_content,
            "received_time": received_time,
            "received_datetime": received_datetime,
            "conversation_id": graph_message.get("conversationId"),
            "categories": graph_message.get("categories", []),
            "importance": graph_message.get("importance", "normal"),
            "is_read": graph_message.get("isRead", False),
            "has_attachments": graph_message.get("hasAttachments", False),
            "folder": "Inbox"  # Default folder, can be overridden
        }
    
    @staticmethod
    def normalize_graph_folder(graph_folder: Dict[str, Any]) -> Dict[str, str]:
        """Convert Graph API folder to internal folder format.
        
        Args:
            graph_folder: Raw Graph API folder object
            
        Returns:
            Normalized folder data
        """
        # Map well-known folder names
        folder_type_mapping = {
            "inbox": "inbox",
            "sentitems": "sent",
            "deleteditems": "trash",
            "drafts": "drafts",
            "outbox": "outbox",
            "junkemail": "spam"
        }
        
        folder_id = graph_folder.get("id", "")
        folder_name = graph_folder.get("displayName", "")
        
        # Determine folder type
        folder_type = "custom"
        folder_name_lower = folder_name.lower()
        for known_name, known_type in folder_type_mapping.items():
            if known_name in folder_name_lower or known_name == folder_id.lower():
                folder_type = known_type
                break
        
        return {
            "id": folder_id,
            "name": folder_name,
            "type": folder_type,
            "parent_id": graph_folder.get("parentFolderId"),
            "unread_count": graph_folder.get("unreadItemCount", 0),
            "total_count": graph_folder.get("totalItemCount", 0)
        }
    
    @staticmethod
    def batch_normalize_messages(graph_messages: List[Dict[str, Any]], folder_name: str = "Inbox") -> List[Dict[str, Any]]:
        """Normalize a batch of Graph API messages.
        
        Args:
            graph_messages: List of raw Graph API message objects
            folder_name: Name of the source folder
            
        Returns:
            List of normalized email data
        """
        normalized_emails = []
        
        for graph_message in graph_messages:
            try:
                normalized_email = EmailNormalizer.normalize_graph_message(graph_message)
                normalized_email["folder"] = folder_name
                normalized_emails.append(normalized_email)
            except Exception as e:
                # Log error but continue processing other emails
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to normalize message {graph_message.get('id', 'unknown')}: {e}")
                continue
        
        return normalized_emails


class GraphAuthResponse(BaseModel):
    """Graph API authentication response model."""
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int
    token_type: str = "Bearer"
    scope: Optional[str] = None


class GraphAuthRequest(BaseModel):
    """Graph API authentication request model."""
    authorization_code: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    grant_type: str = "authorization_code"


class GraphErrorResponse(BaseModel):
    """Graph API error response model."""
    error: str
    error_description: Optional[str] = None
    error_codes: List[int] = []
    timestamp: Optional[str] = None
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None