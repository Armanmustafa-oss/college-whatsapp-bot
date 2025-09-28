# Add to app/services/analytics_service.py
from supabase import create_client
from app.config import settings

class AnalyticsService:
    def __init__(self):
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    def log_conversation(self, user_phone: str, message: str, response: str, language: str):
        """Log conversation for analytics"""
        data = {
            "user_phone": user_phone,
            "user_message": message,
            "bot_response": response,
            "language": language,
            "timestamp": "now()"
        }
        self.supabase.table("conversations").insert(data).execute()