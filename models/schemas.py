# app/models/schemas.py

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class WhatsAppWebhookEntry(BaseModel):
    id: str
    changes: List[Dict[str, Any]]

class WhatsAppWebhook(BaseModel):
    object: str
    entry: List[WhatsAppWebhookEntry]

class WhatsAppMessage(BaseModel):
    from_number: str
    message_id: str
    timestamp: str
    message_type: str
    text_body: Optional[str] = None

class ChatBotResponse(BaseModel):
    message: str
    language: str = "en"
    confidence: float = 0.0
    sources: List[str] = []

class CollegeDocument(BaseModel):
    title: str
    content: str
    category: str  # "admission", "immigration", "classes", etc.
    language: str = "en"

# ✅ NEW: Represents a college in your multi-tenant system
class College(BaseModel):
    id: str
    name: str
    country: str
    webhook_token: str
    active: bool = True