# app/services/monitoring.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
import os
import hashlib
from supabase import create_client
from datetime import datetime

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", ""),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="production"
)

# Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", "")
)

def log_conversation(
    phone: str,
    message: str,
    response: str,
    language: str,
    quality_score: float,
    confidence_score: float,
    had_fallback: bool,
    documents_retrieved: int,
    response_time_ms: int
):
    """Log to enterprise-grade conversations table"""
    phone_hash = hashlib.sha256(phone.encode()).hexdigest()
    
    try:
        supabase.table("conversations").insert({
            "phone_hash": phone_hash,
            "message_text": message[:1000],
            "bot_response": response[:1000],
            "language": language,
            "quality_score": quality_score,
            "confidence_score": confidence_score,
            "had_fallback": had_fallback,
            "documents_retrieved": documents_retrieved,
            "response_time_ms": response_time_ms,
            "model_used": "mixtral-8x7b-32768"
        }).execute()
    except Exception as e:
        sentry_sdk.capture_exception(e)