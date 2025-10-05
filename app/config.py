# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Twilio WhatsApp API (used instead of Meta)
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")  # e.g., +14155238886

    # Groq / OpenAI
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Webhook verification (still used for /webhook GET)
    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "test")

    # Supabase (optional)
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # App
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # Validation: Only require Twilio + AI key
    @classmethod
    def validate(cls):
        # Require Twilio credentials
        twilio_vars = [
            cls.TWILIO_ACCOUNT_SID,
            cls.TWILIO_AUTH_TOKEN,
            cls.TWILIO_WHATSAPP_NUMBER
        ]
        twilio_names = [
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "TWILIO_WHATSAPP_NUMBER"
        ]

        # Require at least one AI key
        ai_key = cls.GROQ_API_KEY or cls.OPENAI_API_KEY
        if not ai_key:
            raise ValueError("Missing required AI key: set GROQ_API_KEY or OPENAI_API_KEY")

        # Check Twilio vars
        missing_twilio = [name for name, val in zip(twilio_names, twilio_vars) if not val]
        if missing_twilio:
            raise ValueError(f"Missing required Twilio environment variables: {missing_twilio}")

settings = Settings()