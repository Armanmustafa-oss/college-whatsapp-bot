# app/services/whatsapp_service.py
import logging
import os
from typing import Optional
from twilio.rest import Client

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")  # e.g., "+14155238886"

        if not self.account_sid or not self.auth_token or not self.from_whatsapp_number:
            logger.error("Missing Twilio credentials in environment variables")
            raise ValueError("Twilio credentials not configured")

        self.client = Client(self.account_sid, self.auth_token)

    def send_message(self, to_phone_number: str, message: str) -> bool:
        """Send WhatsApp message via Twilio"""
        try:
            # Ensure numbers are in E.164 format: +1234567890
            to_num = to_phone_number.lstrip("+")
            from_num = self.from_whatsapp_number.lstrip("+")

            self.client.messages.create(
                from_=f"whatsapp:+{from_num}",
                to=f"whatsapp:+{to_num}",
                body=message
            )
            logger.info(f"📤 Message sent to +{to_num} via Twilio")
            return True
        except Exception as e:
            logger.error(f"❌ Twilio send failed: {e}")
            return False

    def parse_incoming_message(self, webhook_data: dict) -> Optional[dict]:
        """
        Parse incoming Twilio webhook (form-encoded, but FastAPI can parse as dict)
        Expected keys: 'From', 'MessageSid', 'Timestamp', 'Body'
        """
        try:
            from_number = webhook_data.get("From", "").replace("whatsapp:", "")
            return {
                "from_number": from_number,
                "message_id": webhook_data.get("MessageSid", ""),
                "timestamp": webhook_data.get("Timestamp", ""),
                "message_type": "text",
                "text_body": webhook_data.get("Body", "")
            }
        except Exception as e:
            logger.error(f"Error parsing Twilio webhook: {e}")
            return None

    def mark_message_as_read(self, message_id: str) -> bool:
        """
        Twilio does not require explicit read receipts.
        Messages are considered read by default.
        """
        logger.debug("Twilio does not require mark-as-read — skipping")
        return True


# Global instance
whatsapp_service = WhatsAppService()