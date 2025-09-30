import base64
import requests
import json
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_url = settings.WHATSAPP_API_URL

def send_message(self, to_phone_number: str, message: str) -> bool:
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{self.account_sid}:{self.auth_token}'.encode()).decode()}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "To": f"whatsapp:+{to_phone_number.lstrip('+')}",
        "From": f"whatsapp:+{self.twilio_number.lstrip('+')}",
        "Body": message
    }
    try:
        response = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
            headers=headers,
            data=data
        )
        if response.status_code == 201:
            logger.info(f"📤 Twilio reply sent to {to_phone_number}")
            return True
        else:
            logger.error(f"❌ Twilio error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"💥 Twilio send failed: {e}")
        return False


# def send_message(self, to_phone_number: str, message: str) -> bool:
#     headers = {
#         "Authorization": f"Basic {base64.b64encode(f'{self.account_sid}:{self.auth_token}'.encode()).decode()}",
#         "Content-Type": "application/x-www-form-urlencoded"
#     }
#     data = {
#         "To": f"whatsapp:+{to_phone_number.lstrip('+')}",
#         "From": f"whatsapp:+{self.twilio_number.lstrip('+')}",
#         "Body": message
#     }
#     try:
#         response = requests.post(
#             "https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
#             headers=headers,
#             data=data
#         )
#         return response.status_code == 201
#     except Exception as e:
#         logger.error(f"Twilio send failed: {e}")
#         return False 

    # def send_message(self, to_phone_number: str, message: str) -> bool:
    #     """
    #     Send a text message to a WhatsApp user
        
    #     Args:
    #         to_phone_number: Recipient's phone number (with country code)
    #         message: Text message to send
            
    #     Returns:
    #         bool: True if successful, False otherwise
    #     """
    #     headers = {
    #         "Authorization": f"Bearer {self.access_token}",
    #         "Content-Type": "application/json"
    #     }
        
    #     payload = {
    #         "messaging_product": "whatsapp",
    #         "to": to_phone_number,
    #         "type": "text",
    #         "text": {
    #             "body": message
    #         }
    #     }
        
    #     try:
    #         response = requests.post(
    #             self.api_url,
    #             headers=headers,
    #             json=payload,
    #             timeout=10
    #         )
            
    #         if response.status_code == 200:
    #             logger.info(f"Message sent successfully to {to_phone_number}")
    #             return True
    #         else:
    #             logger.error(f"Failed to send message: {response.status_code} - {response.text}")
    #             return False
                
    #     except requests.RequestException as e:
    #         logger.error(f"Error sending WhatsApp message: {e}")
    #         return False
    
    def parse_incoming_message(self, webhook_data: dict) -> Optional[dict]:
        """
        Parse incoming WhatsApp webhook data
        
        Args:
            webhook_data: Raw webhook payload from WhatsApp
            
        Returns:
            dict: Parsed message data or None if invalid
        """
        try:
            # Navigate the webhook structure
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            
            if not messages:
                return None
                
            message = messages[0]
            
            return {
                "from_number": message.get("from"),
                "message_id": message.get("id"),
                "timestamp": message.get("timestamp"),
                "message_type": message.get("type"),
                "text_body": message.get("text", {}).get("body") if message.get("type") == "text" else None
            }
            
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Error parsing WhatsApp message: {e}")
            return None
    
    def mark_message_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read
        
        Args:
            message_id: ID of the message to mark as read
            
        Returns:
            bool: True if successful
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

# Global instance
whatsapp_service = WhatsAppService()