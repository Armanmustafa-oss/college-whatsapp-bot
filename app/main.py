from datetime import datetime
import logging
import os

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import PlainTextResponse

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import settings
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
limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/")
async def root_post(request: Request):
    """Catch accidental POST requests to root (e.g., from misconfigured webhook)"""
    try:
        body = await request.body()
        logger.warning(f"⚠️ Ignored POST to /: {body[:200]}...")  # Log first 200 chars
    except Exception as e:
        logger.error(f"Error reading POST body: {e}")
    return {"status": "ignored"}

@app.get("/")
async def root():
    return {"message": "College WhatsApp Chatbot API is running!"}

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"), 
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    # 🔥 HARDCODED TOKEN — NO CONFIG, NO ENV
    EXPECTED_TOKEN = "edu_bot_verify_token_987"
    
    if hub_mode == "subscribe" and hub_verify_token == EXPECTED_TOKEN:
        return PlainTextResponse(hub_challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
@limiter.limit("10/minute")
async def handle_webhook(request: Request):
    try:
        # Twilio sends form-encoded data, NOT JSON
        form_data = await request.form()
        logger.info(f"Received Twilio webhook: {dict(form_data)}")
        
        # Extract message info from form data
        from_number = form_data.get("From", "").replace("whatsapp:", "")
        message_body = form_data.get("Body", "")
        message_id = form_data.get("MessageSid", "")
        
        if not message_body:
            logger.info("No message body found")
            return {"status": "ok"}
        
        logger.info(f"Processing message from {from_number}: {message_body}")
        
        # Mark message as read (Twilio auto-reads, so skip if not needed)
        
        # Generate AI response
        ai_response = ai_service.generate_response(message_body, from_number)
        
        # Send reply via Twilio
        success = whatsapp_service.send_message(from_number, ai_response["message"])
        
        if success:
            logger.info(f"✅ Reply sent to {from_number}")
        else:
            logger.error(f"❌ Failed to send reply to {from_number}")
            
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"💥 Error handling webhook: {e}")
        return {"status": "error", "message": str(e)}

# @app.post("/webhook")
# async def handle_webhook(request: Request):
#     try:
#         body = await request.json()
#         logger.info(f"Received webhook: {body}")

#         message_data = whatsapp_service.parse_incoming_message(body)

#         if not message_data:
#             logger.info("No valid message found in webhook")
#             return {"status": "ok"}

#         if not message_data.get("text_body"):
#             logger.info("No text message found in webhook")
#             return {"status": "ok"}

#         user_phone = message_data.get("from_number")
#         user_message = message_data.get("text_body")
#         message_id = message_data.get("message_id")

#         logger.info(f"Processing message from {user_phone}: {user_message}")

#         whatsapp_service.mark_message_as_read(message_id)

#         ai_response = ai_service.generate_response(user_message, user_phone)

#         success = whatsapp_service.send_message(
#             to_phone_number=user_phone,
#             message=ai_response["message"]
#         )

#         if success:
#             logger.info(f"Response sent successfully to {user_phone}")
#         else:
#             logger.error(f"Failed to send response to {user_phone}")

#         return {"status": "ok"}

#     except Exception as e:
#         logger.error(f"Error handling webhook: {e}")
#         return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "whatsapp": bool(settings.WHATSAPP_ACCESS_TOKEN),
            "openai": bool(settings.OPENAI_API_KEY)
        }
    }

@app.get("/health/detailed")
async def detailed_health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "whatsapp_api": await whatsapp_service.check_whatsapp_api(),
            "openai_api": await ai_service.check_openai_api(),
            "chromadb": await ai_service.check_chromadb(),
        },
        "metrics": {
            "total_messages": whatsapp_service.get_message_count(),
            "avg_response_time": ai_service.get_avg_response_time()
        }
    }