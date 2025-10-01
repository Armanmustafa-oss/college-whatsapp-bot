# app/main.py
from datetime import datetime
import logging
import os

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import PlainTextResponse, JSONResponse

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import settings

# Import services correctly (absolute paths)
from services.whatsapp_service import whatsapp_service
from services.ai_service import ai_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="College WhatsApp Chatbot",
    description="AI-powered multilingual chatbot for international students",
    version="1.0.0"
)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.post("/")
async def root_post(request: Request):
    """Catch accidental POST requests to root (e.g., from misconfigured webhook)"""
    try:
        body = await request.body()
        logger.warning(f"⚠️ Ignored POST to /: {body[:200].decode('utf-8', errors='ignore')}...")
    except Exception as e:
        logger.error(f"Error reading POST body: {e}")
    return JSONResponse(content={"status": "ignored"})


@app.get("/")
async def root():
    return {"message": "College WhatsApp Chatbot API is running!"}


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"), 
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    """Webhook verification endpoint for Twilio (not Meta)"""
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully")
        return PlainTextResponse(hub_challenge)
    else:
        logger.error("❌ Webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
@limiter.limit("10/minute")
async def handle_webhook(request: Request):
    """Handle incoming WhatsApp messages from Twilio"""
    try:
        # Twilio sends form-encoded data, NOT JSON
        form_data = await request.form()
        logger.info(f"Received Twilio webhook: {dict(form_data)}")
        
        # Safely extract phone number
        from_number = form_data.get("From", "")
        if not from_number:
            logger.error("No 'From' field in webhook")
            return JSONResponse(content={"status": "ok"})
        
        # Clean phone number (remove whatsapp: prefix and leading +)
        clean_number = from_number.replace("whatsapp:", "").lstrip("+")
        if not clean_number:
            logger.error("Empty phone number after cleaning")
            return JSONResponse(content={"status": "ok"})
            
        message_body = form_data.get("Body", "").strip()
        if not message_body:
            logger.info("No message body")
            return JSONResponse(content={"status": "ok"})
        
        logger.info(f"Processing message from {clean_number}: {message_body}")
        
        # Generate AI response
        ai_response = ai_service.generate_response(message_body, clean_number)
        
        # Send reply via Twilio
        success = whatsapp_service.send_message(clean_number, ai_response["message"])
        if success:
            logger.info(f"✅ Reply sent to {clean_number}")
        else:
            logger.error(f"❌ Failed to send reply to {clean_number}")
            
        return JSONResponse(content={"status": "ok"})
        
    except Exception as e:
        logger.error(f"💥 Error handling webhook: {e}", exc_info=True)
        return JSONResponse(content={"status": "error", "message": str(e)})


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "twilio": bool(settings.TWILIO_ACCOUNT_SID),
            "groq": bool(settings.GROQ_API_KEY)
        }
    }


@app.get("/health/detailed")
async def detailed_health():
    # Note: These methods should be implemented in your service classes
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "twilio_api": True,  # Implement real check if needed
            "groq_api": True,
            "chromadb": True
        },
        "metrics": {
            "total_messages": 0,
            "avg_response_time": 0.0
        }
    }