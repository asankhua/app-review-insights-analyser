"""
Email service for Phase 4: SMTP (local) or Resend API (Render free tier).
Resend works on Render because SMTP ports are blocked on free tier.
"""
import smtplib
import ssl
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from typing import Dict, Any

from .models.email import EmailMessage, EmailStatus
from src.config.settings import Config

logger = logging.getLogger(__name__)


class EmailService:
    """Email service: Resend API (preferred on Render) or SMTP"""
    
    def __init__(self):
        self.config = Config()
        self.smtp_host = self.config.SMTP_HOST
        self.smtp_port = self.config.SMTP_PORT
        self.sender_email = self.config.EMAIL_SENDER
        self.sender_password = self.config.EMAIL_PASSWORD
        self.resend_api_key = self.config.RESEND_API_KEY
        
        if self.resend_api_key:
            if not self.sender_email:
                raise ValueError("EMAIL_SENDER required for Resend (used as From address)")
            logger.info("Using Resend API for email (Render-friendly)")
        elif not self.sender_email or not self.sender_password:
            raise ValueError("EMAIL_SENDER and EMAIL_PASSWORD required, or set RESEND_API_KEY for Render")
    
    def send_email(
        self, 
        email_message: EmailMessage,
        mode: str = "dry_run"
    ) -> Dict[str, Any]:
        """
        Send email or create draft
        
        Args:
            email_message: Email message to send
            mode: "send" to actually send, "dry_run" to create draft
            
        Returns:
            Dictionary with send results
        """
        try:
            logger.info(f"Email service: mode={mode}, recipient={email_message.to_email}")
            
            if mode == "dry_run":
                return self._create_draft(email_message)
            elif self.resend_api_key:
                return self._send_resend(email_message)
            else:
                return self._send_smtp(email_message)
                
        except Exception as e:
            logger.error(f"Email service failed: {str(e)}")
            raise
    
    def _send_resend(self, email_message: EmailMessage) -> Dict[str, Any]:
        """Send via Resend API (HTTPS; works on Render free tier)."""
        try:
            import resend
            resend.api_key = self.resend_api_key
            params = {
                "from": self.sender_email,
                "to": [email_message.to_email],
                "subject": email_message.subject,
                "html": email_message.html_body,
            }
            result = resend.Emails.send(params)
            logger.info(f"Email sent via Resend to {email_message.to_email}")
            return {
                'status': EmailStatus.SENT,
                'message_id': result.get('id', f"resend_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                'sent_at': datetime.now().isoformat(),
                'processing_time': 0.5,
                'recipient': email_message.to_email,
                'subject': email_message.subject,
            }
        except Exception as e:
            logger.error(f"Resend send failed: {str(e)}")
            return {
                'status': EmailStatus.FAILED,
                'error_message': str(e),
                'message_id': f"failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'sent_at': None,
                'processing_time': 0,
                'recipient': email_message.to_email,
                'subject': email_message.subject,
            }

    def _send_smtp(self, email_message: EmailMessage) -> Dict[str, Any]:
        """Send email via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = email_message.subject
            msg['From'] = email_message.from_email
            msg['To'] = email_message.to_email
            
            if email_message.cc_emails:
                msg['Cc'] = ', '.join(email_message.cc_emails)
            
            if email_message.reply_to:
                msg['Reply-To'] = email_message.reply_to
            
            # Add body parts
            text_part = MIMEText(email_message.text_body, 'plain', 'utf-8')
            html_part = MIMEText(email_message.html_body, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add attachments
            for attachment in email_message.attachments:
                self._add_attachment(msg, attachment)
            
            # Send email
            start_time = datetime.now()
            
            # Create SMTP context
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                
                # Prepare recipients
                recipients = [email_message.to_email] + email_message.cc_emails + email_message.bcc_emails
                
                # Send email
                server.sendmail(self.sender_email, recipients, msg.as_string())
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Email sent successfully to {email_message.to_email}")
            
            return {
                'status': EmailStatus.SENT,
                'message_id': f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'sent_at': datetime.now().isoformat(),
                'processing_time': processing_time,
                'recipient': email_message.to_email,
                'subject': email_message.subject
            }
            
        except Exception as e:
            logger.error(f"SMTP send failed: {str(e)}")
            return {
                'status': EmailStatus.FAILED,
                'error_message': str(e),
                'message_id': f"failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'sent_at': None,
                'processing_time': 0,
                'recipient': email_message.to_email,
                'subject': email_message.subject
            }
    
    def _create_draft(self, email_message: EmailMessage) -> Dict[str, Any]:
        """Create email draft file"""
        try:
            # Ensure drafts directory exists
            drafts_dir = Path("data/drafts")
            drafts_dir.mkdir(exist_ok=True)
            
            # Create draft filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            draft_filename = f"draft_{timestamp}.eml"
            draft_path = drafts_dir / draft_filename
            
            # Create message content
            draft_content = self._create_eml_content(email_message)
            
            # Write draft file
            with open(draft_path, 'w', encoding='utf-8') as f:
                f.write(draft_content)
            
            logger.info(f"Email draft created: {draft_path}")
            
            return {
                'status': EmailStatus.DRAFT,
                'message_id': f"draft_{timestamp}",
                'draft_path': str(draft_path),
                'sent_at': None,
                'processing_time': 0.1,
                'recipient': email_message.to_email,
                'subject': email_message.subject
            }
            
        except Exception as e:
            logger.error(f"Draft creation failed: {str(e)}")
            raise
    
    def _create_eml_content(self, email_message: EmailMessage) -> str:
        """Create .eml file content"""
        lines = []
        
        # Headers
        lines.append(f"Subject: {email_message.subject}")
        lines.append(f"From: {email_message.from_email}")
        lines.append(f"To: {email_message.to_email}")
        
        if email_message.cc_emails:
            lines.append(f"Cc: {', '.join(email_message.cc_emails)}")
        
        if email_message.reply_to:
            lines.append(f"Reply-To: {email_message.reply_to}")
        
        lines.append(f"Date: {datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')}")
        lines.append("MIME-Version: 1.0")
        lines.append('Content-Type: multipart/alternative; boundary="----=_Part_123456789"')
        lines.append("")
        
        # Plain text part
        lines.append("----=_Part_123456789")
        lines.append("Content-Type: text/plain; charset=utf-8")
        lines.append("Content-Transfer-Encoding: 7bit")
        lines.append("")
        lines.append(email_message.text_body)
        lines.append("")
        
        # HTML part
        lines.append("----=_Part_123456789")
        lines.append("Content-Type: text/html; charset=utf-8")
        lines.append("Content-Transfer-Encoding: 7bit")
        lines.append("")
        lines.append(email_message.html_body)
        lines.append("")
        
        lines.append("----=_Part_123456789--")
        
        return '\n'.join(lines)
    
    def _add_attachment(self, msg: MIMEMultipart, attachment) -> None:
        """Add attachment to email message"""
        try:
            # Create attachment part
            part = MIMEApplication(attachment.content, Name=attachment.filename)
            
            # Add headers
            part['Content-Disposition'] = f'attachment; filename="{attachment.filename}"'
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment.filename}: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
            
            logger.info("SMTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {str(e)}")
            return False
    
    def get_configuration_info(self) -> Dict[str, Any]:
        """Get email service configuration"""
        info = {
            'smtp_host': self.smtp_host,
            'smtp_port': self.smtp_port,
            'sender_email': self.sender_email,
            'sender_configured': bool(self.sender_email),
            'password_configured': bool(self.sender_password),
            'resend_configured': bool(self.resend_api_key),
        }
        if not self.resend_api_key:
            info['connection_test'] = self.test_connection()
        return info
