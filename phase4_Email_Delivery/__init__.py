"""
Phase 4: Email Delivery
"""
from .email_service import EmailService
from .email_delivery import EmailDeliveryService
from .models.email import EmailMessage, EmailDeliveryRequest, EmailDeliveryResponse
from .config.email_templates import (
    WEEKLY_PULSE_TEMPLATE,
    HTML_TEMPLATE,
    PLAIN_TEXT_TEMPLATE
)

__all__ = [
    'EmailService',
    'EmailDeliveryService',
    'EmailMessage',
    'EmailDeliveryRequest',
    'EmailDeliveryResponse',
    'WEEKLY_PULSE_TEMPLATE',
    'HTML_TEMPLATE',
    'PLAIN_TEXT_TEMPLATE'
]

