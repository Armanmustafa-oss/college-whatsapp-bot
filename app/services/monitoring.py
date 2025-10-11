# app/services/monitoring.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
import os
from supabase import create_client
from datetime import datetime

# Initialize Sentry (FREE)
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", ""),  # Get from sentry.io
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="production"
)

# Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", "")
)

def log_conversation(phone: str, message: str, response: str, duration: float):
    """Log to Supabase with GDPR-safe phone hash"""
    import hashlib
    phone_hash = hashlib.sha256(phone.encode()).hexdigest()
    try:
        supabase.table("conversations").insert({
            "phone_hash": phone_hash,
            "message_text": message[:500],
            "bot_response": response[:500],
            "response_time": duration,
            "timestamp": datetime.now().isoformat(),
            "language": "auto"  # enhance later
        }).execute()
    except Exception as e:
        sentry_sdk.capture_exception(e)