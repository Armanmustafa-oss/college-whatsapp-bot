# app/services/whatsapp_service.py

import base64
import requests
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "")  # e.g., "whatsapp:+14155238886"

    def send_message(self, to_phone_number: str, message: str) -> bool:
        """Send WhatsApp message via Twilio"""
        if not to_phone_number:
            logger.error("to_phone_number is empty")
            return False

        # Clean Twilio number from env
        twilio_num = self.twilio_number.replace("whatsapp:", "").lstrip("+")
        if not twilio_num:
            logger.error("TWILIO_WHATSAPP_NUMBER is not set or invalid")
            return False

        # Clean recipient number
        clean_to = to_phone_number.lstrip("+")
        if not clean_to:
            logger.error("Recipient phone number is invalid")
            return False

        # Prepare auth
        auth_str = f"{self.account_sid}:{self.auth_token}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "To": f"whatsapp:+{clean_to}",
            "From": f"whatsapp:+{twilio_num}",
            "Body": message
        }

        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            response = requests.post(url, headers=headers, data=data, timeout=10)
            
            if response.status_code == 201:
                logger.info(f"📤 Twilio reply sent to +{clean_to}")
                return True
            else:
                logger.error(f"❌ Twilio error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"💥 Twilio send failed: {e}")
            return False

    def parse_incoming_message(self, webhook_data: dict) -> Optional[dict]:
        """Parse incoming Twilio webhook data"""
        try:
            # Twilio sends form data, but we handle JSON in main.py
            # This method is kept for compatibility
            return {
                "from_number": webhook_data.get("From", "").replace("whatsapp:", ""),
                "message_id": webhook_data.get("MessageSid", ""),
                "timestamp": webhook_data.get("Timestamp", ""),
                "message_type": "text",
                "text_body": webhook_data.get("Body", "")
            }
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None

    def mark_message_as_read(self, message_id: str) -> bool:
        """Twilio auto-reads messages — this is a no-op"""
        logger.info("Twilio auto-reads messages — skipping mark-as-read")
        return True


# Global instance
whatsapp_service = WhatsAppService()