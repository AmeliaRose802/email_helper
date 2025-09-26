"""Pydantic models for FastAPI Email Helper API."""

from .user import User, UserCreate, UserLogin, UserInDB, Token, TokenData
from .email import Email, EmailCreate, EmailUpdate, EmailInDB, EmailClassification, EmailBatch, EmailBatchResult
from .task import Task, TaskCreate, TaskUpdate, TaskInDB
from .graph_email import (
    GraphMessage, GraphMailFolder, GraphEmailAddress, GraphRecipient, 
    GraphEmailBody, EmailNormalizer, GraphAuthResponse, GraphAuthRequest, 
    GraphErrorResponse
)

__all__ = [
    "User", "UserCreate", "UserLogin", "UserInDB", "Token", "TokenData",
    "Email", "EmailCreate", "EmailUpdate", "EmailInDB", 
    "EmailClassification", "EmailBatch", "EmailBatchResult",
    "Task", "TaskCreate", "TaskUpdate", "TaskInDB",
    "GraphMessage", "GraphMailFolder", "GraphEmailAddress", "GraphRecipient",
    "GraphEmailBody", "EmailNormalizer", "GraphAuthResponse", "GraphAuthRequest",
    "GraphErrorResponse"
]
