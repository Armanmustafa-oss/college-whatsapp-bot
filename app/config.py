import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # WhatsApp Business API
    WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID") 
    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "your_custom_verify_token")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # App
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # WhatsApp API endpoints
    WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    # Validate required settings
    @classmethod
    def validate(cls):
        required = [
            cls.WHATSAPP_ACCESS_TOKEN,
            cls.WHATSAPP_PHONE_NUMBER_ID,
            cls.OPENAI_API_KEY
        ]
        missing = [name for name, value in zip(
            ["WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "OPENAI_API_KEY"],
            required
        ) if not value]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")

settings = Settings()