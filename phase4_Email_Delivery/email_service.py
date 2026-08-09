"""
Email service: SMTP (local) or Resend API (Render free tier).
Resend uses HTTPS, so it works where SMTP ports are blocked.
Timestamps stored in IST for consistent UI display.
"""
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
import json
import logging
import os
from pathlib import Path

# Load .env before any Config/env reads (ensures EMAIL_SENDER/EMAIL_PASSWORD exist)
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path, override=True)
    except ImportError:
        pass

import smtplib
import sys
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from typing import Dict, Any

from .models.email import EmailMessage, EmailStatus
from src.config.settings import Config

logger = logging.getLogger(__name__)


class EmailService:
    """Email: Resend API (Render free tier) or SMTP (local)"""
    
    def __init__(self):
        self.config = Config()
        # Read env fresh (Config may have been cached before .env loaded)
        self.smtp_host = (os.getenv("SMTP_HOST") or self.config.SMTP_HOST or "").strip().lower()
        self.smtp_port = int(os.getenv("SMTP_PORT") or "587")
        self.sender_email = (os.getenv("EMAIL_SENDER") or self.config.EMAIL_SENDER or "").strip() or None
        self.sender_password = (os.getenv("EMAIL_PASSWORD") or self.config.EMAIL_PASSWORD or "").strip() or None
        _resend = (os.getenv("RESEND_API_KEY") or self.config.RESEND_API_KEY or "").strip().replace("\n", "").replace("\r", "")
        # Use Resend when key is set (HTTPS; works when SMTP/DNS is blocked). Else use SMTP.
        self.resend_api_key = _resend or None
        
        if self.resend_api_key:
            if not self.sender_email:
                raise ValueError("EMAIL_SENDER required (used as From address with Resend)")
            logger.info("Using Resend API for email")
        elif not self.sender_email or not self.sender_password or not self.smtp_host:
            # Reload .env and fallback to manual parse (handles dotenv quirks with long/SMTP keys)
            _root = Path(__file__).resolve().parent.parent
            _env = _root / ".env"
            if _env.exists():
                try:
                    from dotenv import load_dotenv
                    load_dotenv(_env, override=True)
                except Exception:
                    pass
            self.sender_email = (os.getenv("EMAIL_SENDER") or "").strip() or None
            self.sender_password = (os.getenv("EMAIL_PASSWORD") or "").strip() or None
            self.smtp_host = (os.getenv("SMTP_HOST") or self.config.SMTP_HOST or "").strip().lower() or self.smtp_host
            # Manual parse if dotenv didn't load (e.g. long Brevo SMTP key or SMTP_HOST)
            if (not self.sender_email or not self.sender_password or not self.smtp_host) and _env.exists():
                try:
                    text = _env.read_text(encoding="utf-8")
                    for line in text.splitlines():
                        line = line.strip()
                        if line.startswith("#") or "=" not in line:
                            continue
                        k, _, v = line.partition("=")
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k == "EMAIL_SENDER" and v:
                            self.sender_email = self.sender_email or v
                        elif k == "EMAIL_PASSWORD" and v:
                            self.sender_password = self.sender_password or v
                        elif k == "SMTP_HOST" and v:
                            self.smtp_host = self.smtp_host or v.strip().lower()
                except Exception:
                    pass
            if not self.sender_email or not self.sender_password:
                raise ValueError(
                    "EMAIL_SENDER and EMAIL_PASSWORD required for SMTP. "
                    "Check .env has EMAIL_SENDER, EMAIL_PASSWORD (no spaces around =). Or set RESEND_API_KEY."
                )
            if not self.smtp_host:
                raise ValueError(
                    "SMTP_HOST required for SMTP. Add SMTP_HOST=smtp-relay.brevo.com to .env for Brevo."
                )
    
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
            if email_message.attachments:
                import base64
                params["attachments"] = [
                    {"filename": att.filename, "content": base64.b64encode(att.content).decode("ascii")}
                    for att in email_message.attachments
                ]
            result = resend.Emails.send(params)
            msg_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", None)
            logger.info(f"Email sent via Resend to {email_message.to_email}")
            return {
                'status': EmailStatus.SENT,
                'message_id': msg_id or f"resend_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'sent_at': datetime.now(IST).isoformat(),
                'processing_time': 0.5,
                'recipient': email_message.to_email,
                'subject': email_message.subject,
            }
        except Exception as e:
            err_msg = str(e)
            if "invalid" in err_msg.lower() and "api" in err_msg.lower():
                err_msg = (
                    "Resend API key invalid. On Render: add RESEND_API_KEY in Environment. "
                    "Create a new key at resend.com → API Keys. Remove spaces/newlines when pasting."
                )
            logger.error(f"Resend send failed: {err_msg}")
            return {
                'status': EmailStatus.FAILED,
                'error_message': err_msg,
                'message_id': f"failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'sent_at': None,
                'processing_time': 0,
                'recipient': email_message.to_email,
                'subject': email_message.subject,
            }

    def _send_smtp(self, email_message: EmailMessage) -> Dict[str, Any]:
        """Send email via SMTP"""
        if not self.smtp_host:
            return {
                'status': EmailStatus.FAILED,
                'error_message': (
                    "SMTP_HOST is empty. Add SMTP_HOST=smtp-relay.brevo.com to .env and restart."
                ),
                'message_id': f"failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'sent_at': None,
                'processing_time': 0,
                'recipient': email_message.to_email,
                'subject': email_message.subject
            }
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
                'sent_at': datetime.now(IST).isoformat(),
                'processing_time': processing_time,
                'recipient': email_message.to_email,
                'subject': email_message.subject
            }
            
        except smtplib.SMTPAuthenticationError as e:
            err = str(e).lower()
            if "535" in err or "password" in err or "badcredentials" in err or "username" in err:
                msg = (
                    "Gmail login failed: use an App Password, not your normal password. "
                    "In Google Account → Security → 2-Step Verification → App passwords, create one and set EMAIL_PASSWORD in .env"
                )
            else:
                msg = str(e)
            logger.error(f"SMTP auth failed: {msg}")
            return {
                'status': EmailStatus.FAILED,
                'error_message': msg,
                'message_id': f"failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'sent_at': None,
                'processing_time': 0,
                'recipient': email_message.to_email,
                'subject': email_message.subject
            }
        except OSError as e:
            err_str = str(e)
            if "nodename nor servname" in err_str.lower() or getattr(e, "errno", None) == 8:
                host_info = f"'{self.smtp_host}'" if self.smtp_host else "(empty)"
                err_str = (
                    f"SMTP host {host_info} cannot be resolved. Check: "
                    "1) SMTP_HOST in .env (e.g. smtp-relay.brevo.com) — save and restart. "
                    "2) Your network/DNS — corporate firewall may block SMTP. "
                    "3) Try Resend (HTTPS) instead: set RESEND_API_KEY in .env."
                )
            logger.error(f"SMTP send failed: {err_str}")
        except Exception as e:
            err_str = str(e)
            if "535" in err_str and ("password" in err_str.lower() or "username" in err_str.lower() or "badcredentials" in err_str.lower()):
                err_str = (
                    "Gmail login failed: use an App Password, not your normal password. "
                    "Google Account → Security → 2-Step Verification → App passwords; set EMAIL_PASSWORD in .env"
                )
            logger.error(f"SMTP send failed: {err_str}")
        return {
                'status': EmailStatus.FAILED,
                'error_message': err_str,
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
