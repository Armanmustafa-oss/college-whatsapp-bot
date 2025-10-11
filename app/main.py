# app/main.py
import time

import sentry_sdk
from app.services.monitoring import log_conversation
from datetime import datetime
import logging
import os

from fastapi import FastAPI, HTTPException, Request, Query, UploadFile
from fastapi.responses import PlainTextResponse, JSONResponse

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import settings

# ✅ CORRECT ABSOLUTE IMPORTS (NO ".." or ".")
from app.services.whatsapp_service import whatsapp_service
from app.services.ai_service import ai_service  
from app.services.rag_service import rag_service  


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
    """Catch accidental POST requests to root"""
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
    """Webhook verification for Twilio"""
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        logger.info("✅ Webhook verified successfully")
        return PlainTextResponse(hub_challenge)
    else:
        logger.error("❌ Webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
@limiter.limit("10/minute")
async def handle_webhook(request: Request):
    start_time = time.time()
    try:
        form_data = await request.form()
        from_number = form_data.get("From", "").replace("whatsapp:", "").lstrip("+")
        message_body = form_data.get("Body", "").strip()
        
        if not from_number or not message_body:
            return JSONResponse(content={"status": "ok"})
        
        logger.info(f"Processing message from {from_number}: {message_body}")
        
        ai_response = ai_service.generate_response(message_body, from_number)
        success = whatsapp_service.send_message(from_number, ai_response["message"])
        
        duration = time.time() - start_time
        log_conversation(from_number, message_body, ai_response["message"], duration)
        
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return JSONResponse(content={"status": "error"})


# @app.post("/upload-pdf")
# async def upload_pdf(file: UploadFile):
#     """Upload PDF to update knowledge base"""
#     os.makedirs("data/college_docs", exist_ok=True)
#     with open(f"data/college_docs/{file.filename}", "wb") as f:
#         f.write(await file.read())
#     ai_service.kb = KnowledgeBase()  # Reload knowledge base
#     return {"status": "PDF uploaded and processed"}


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
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "twilio_api": True,
            "groq_api": True,
            "chromadb": True
        },
        "metrics": {
            "total_messages": 0,
            "avg_response_time": 0.0
        }
    }