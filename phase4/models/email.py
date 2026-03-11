"""
Email delivery data models for Phase 4
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum

class EmailMode(str, Enum):
    """Email delivery modes"""
    DRY_RUN = "dry_run"
    SEND = "send"

class EmailStatus(str, Enum):
    """Email delivery status"""
    DRAFT = "draft"
    SENT = "sent"
    FAILED = "failed"
    PENDING = "pending"

@dataclass
class EmailAttachment:
    """Email attachment model"""
    filename: str
    content: bytes
    content_type: str
    size: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "filename": self.filename,
            "content_type": self.content_type,
            "size": self.size
        }

class EmailMessage(BaseModel):
    """Email message model"""
    subject: str = Field(..., description="Email subject line")
    from_email: str = Field(..., description="Sender email address")
    to_email: str = Field(..., description="Recipient email address")
    cc_emails: List[str] = Field(default_factory=list, description="CC recipients")
    bcc_emails: List[str] = Field(default_factory=list, description="BCC recipients")
    html_body: str = Field(..., description="HTML email body")
    text_body: str = Field(..., description="Plain text email body")
    attachments: List[EmailAttachment] = Field(default_factory=list, description="Email attachments")
    reply_to: Optional[str] = Field(None, description="Reply-to address")
    
    @validator('from_email', 'to_email')
    def validate_email(cls, v):
        """Basic email validation"""
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError(f'Invalid email address: {v}')
        return v
    
    @validator('cc_emails', 'bcc_emails')
    def validate_email_lists(cls, v):
        """Validate email lists"""
        for email in v:
            if '@' not in email or '.' not in email.split('@')[-1]:
                raise ValueError(f'Invalid email address: {email}')
        return v

class EmailDeliveryRequest(BaseModel):
    """Email delivery request model"""
    weekly_note_path: str = Field(..., description="Path to weekly note file")
    recipient_email: Optional[str] = Field(None, description="Override recipient email")
    recipient_name: Optional[str] = Field(None, description="Recipient name for greeting")
    mode: EmailMode = Field(default=EmailMode.DRY_RUN, description="Email delivery mode")
    include_attachments: bool = Field(default=True, description="Include report attachments")
    custom_subject: Optional[str] = Field(None, description="Custom email subject")
    
    @validator('weekly_note_path')
    def validate_weekly_note_path(cls, v):
        """Validate weekly note file path"""
        if not v.endswith('.md') and not v.endswith('.json'):
            raise ValueError('Weekly note path must be .md or .json file')
        return v

class EmailDeliveryResponse(BaseModel):
    """Email delivery response model"""
    message_id: str = Field(..., description="Unique message identifier")
    status: EmailStatus = Field(..., description="Email delivery status")
    sent_at: Optional[datetime] = Field(None, description="Email sent timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    draft_path: Optional[str] = Field(None, description="Draft file path for dry-run")
    recipient: str = Field(..., description="Email recipient")
    subject: str = Field(..., description="Email subject")
    processing_time: float = Field(..., description="Processing time in seconds")

class EmailDeliveryFile(BaseModel):
    """Email delivery file model for storage"""
    message_id: str = Field(..., description="Unique message identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    request: EmailDeliveryRequest = Field(..., description="Delivery request")
    response: EmailDeliveryResponse = Field(..., description="Delivery response")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class EmailStats(BaseModel):
    """Email statistics model"""
    total_sent: int = Field(default=0, description="Total emails sent")
    total_drafts: int = Field(default=0, description="Total drafts created")
    last_sent: Optional[datetime] = Field(None, description="Last email sent timestamp")
    success_rate: float = Field(default=0.0, description="Email delivery success rate")
    most_recent_file: Optional[str] = Field(None, description="Most recent delivery file")
