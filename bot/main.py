"""
🚀 Enterprise WhatsApp Bot API Gateway
=======================================
FastAPI-based webhook handler orchestrating the entire bot interaction flow.
Integrates RAG, Prompt Engineering, AI Generation, Response Enhancement, and Monitoring.
"""

import logging
import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from twilio.rest import Client as TwilioRestClient
from twilio.base.exceptions import TwilioRestException
from supabase import create_client, Client as SupabaseClient
import sentry_sdk
from datetime import datetime, timezone
import threading
from typing import Dict, List

# Import your custom modules and configurations
from bot.config import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER,
    SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY,
    SENTRY_DSN, ENVIRONMENT, PORT,
    RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW,
    BOT_BEHAVIOR
)
from bot.prompts.prompt_engine import PromptEngine, ConversationContext, Intent, Sentiment, Urgency
from bot.response_quality.enhancer import ResponseEnhancer
from bot.rag.retriever import Retriever # Assuming you create this next
from monitoring.sentry_config import SentryManager # Assuming this is correctly implemented
from monitoring.performance import PerformanceTracker # Assuming you create this

# --- Initialize Logging ---
logging.basicConfig(
    level=logging.INFO if ENVIRONMENT != "development" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Application Lifecycle Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown tasks.
    Initializes shared resources like clients, engines, etc.
    """
    logger.info("🚀 Starting up College WhatsApp Bot API...")
    
    # --- Initialize Shared Resources ---
    global twilio_client, supabase, prompt_engine, response_enhancer, retriever, performance_tracker
    
    # Twilio Client
    twilio_client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    logger.info("✅ Twilio client initialized.")

    # Supabase Client
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Connected to Supabase successfully.")
    except Exception as e:
        logger.critical(f"❌ Failed to connect to Supabase: {e}")
        raise e

    # Prompt Engine
    prompt_engine = PromptEngine(college_name=BOT_BEHAVIOR["college_name"], knowledge_base_metadata={})
    logger.info("✅ PromptEngine initialized.")

    # Response Enhancer
    response_enhancer = ResponseEnhancer(trusted_domains=[f"{BOT_BEHAVIOR['college_name'].replace(' ', '').lower()}.edu"]) # Example domain
    logger.info("✅ ResponseEnhancer initialized.")

    # RAG Retriever
    retriever = Retriever() # Initialize with path to vector store or client
    logger.info("✅ RAG Retriever initialized.")

    # Performance Tracker
    performance_tracker = PerformanceTracker(supabase_client=supabase) # Pass Supabase client for metrics logging
    logger.info("✅ PerformanceTracker initialized.")

    # Initialize Sentry (if DSN is provided)
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=ENVIRONMENT,
            traces_sample_rate=1.0 if ENVIRONMENT == "production" else 0.1, # Lower sample rate for non-prod
        )
        logger.info("✅ Sentry initialized.")
        SentryManager.initialize(sentry_sdk) # Assuming a static init method
    else:
        logger.warning("⚠️ SENTRY_DSN not found. Sentry monitoring is disabled.")

    yield # Hand over control to the application

    # --- Shutdown tasks ---
    logger.info("🛑 Shutting down College WhatsApp Bot API...")

# --- Initialize FastAPI app with lifespan ---
app = FastAPI(
    title="College WhatsApp Bot API",
    description="Enterprise-grade AI assistant for college support via WhatsApp.",
    version="2.0.0",
    lifespan=lifespan
)

# --- Rate Limiting State (Simple In-Memory - Consider Redis for Production) ---
# A dictionary to store message counts per phone number
message_counts: Dict[str, List[float]] = {}
message_counts_lock = threading.Lock() # Thread-safe access

def is_rate_limited(phone_number: str) -> tuple[bool, int]:
    """Checks if a phone number has exceeded the rate limit. Returns (is_limited, remaining_time_seconds)."""
    current_time = time.time()
    with message_counts_lock:
        if phone_number not in message_counts:
            message_counts[phone_number] = []
        # Filter out timestamps older than the window
        message_counts[phone_number] = [
            t for t in message_counts[phone_number]
            if current_time - t <= RATE_LIMIT_WINDOW
        ]
        # Check if count exceeds the limit
        current_count = len(message_counts[phone_number])
        if current_count >= RATE_LIMIT_MESSAGES:
            # Calculate remaining time until oldest message expires
            oldest_time = min(message_counts[phone_number])
            remaining_time = int(RATE_LIMIT_WINDOW - (current_time - oldest_time))
            logger.warning(f"Rate limit exceeded for {phone_number}. Remaining time: {remaining_time}s")
            return True, max(remaining_time, 0)
        # Add current timestamp
        message_counts[phone_number].append(current_time)
        remaining_count = RATE_LIMIT_MESSAGES - current_count
    return False, remaining_count

# --- Groq AI Interaction Helper ---
async def call_groq_async(system_prompt: str, user_prompt: str) -> str:
    """
    Asynchronously calls the Groq API with the system and user prompts.
    This is a placeholder - implement the actual API call logic here using httpx or groq library.
    """
    import httpx
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "mixtral-8x7b-32768", # Use configured model if available
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3, # Lower for more factual responses
        "max_tokens": 500
    }
    start_time = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client: # 30s timeout
            response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            raw_response = result['choices'][0]['message']['content']
            duration = time.perf_counter() - start_time
            logger.debug(f"Groq API call took {duration:.2f}s")
            return raw_response
    except httpx.RequestError as e:
        logger.error(f"Network error calling Groq API: {e}")
        raise
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP {e.response.status_code} error from Groq API: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error calling Groq API: {e}")
        raise

# --- Background Task: Log Interaction to Supabase ---
async def log_interaction_to_supabase_async(
    user_phone: str, user_message: str, bot_response: str, context_used: str,
    intent: Intent, sentiment: Sentiment, urgency: Urgency, session_id: str
):
    """Asynchronously logs the conversation interaction to Supabase."""
    log_entry = {
        "user_phone": user_phone,
        "user_message": user_message,
        "bot_response": bot_response,
        "timestamp": datetime.now(timezone.utc).isoformat(), # ISO format for Supabase timestamp
        "context_used": context_used[:5000], # Truncate if very long, adjust size as needed
        "language_code": "en", # Adjust based on detection
        "session_id": session_id,
        "intent": intent.value,
        "sentiment": sentiment.value,
        "urgency": urgency.value
    }
    try:
        # Use Supabase client to insert
        supabase.table("conversations").insert(log_entry).execute() # Adjust table name if different
        logger.debug(f"Interaction logged for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to log conversation to Supabase: {e}")
        # Optionally, capture this error in Sentry if logging fails critically
        sentry_sdk.capture_exception(e) # Only if SENTRY_DSN is active

# --- Webhook Endpoint ---
@app.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handles incoming messages from Twilio WhatsApp webhook."""
    start_time = time.perf_counter()
    session_id = f"sess_{int(time.time())}_{hash(request.client.host) % 10000}" # Simple session ID
    sender_number = None
    try:
        form_data = await request.form()
        message_body = form_data.get('Body', '').strip()
        sender_number = form_data.get('From', '') # e.g., whatsapp:+1234567890
        user_profile = {"role": "student", "year": "unknown"} # Placeholder, fetch from DB if available

        logger.info(f"({session_id}) Received message from {sender_number}: {message_body[:50]}...")

        # --- Rate Limiting Check ---
        is_limited, remaining_time = is_rate_limited(sender_number)
        if is_limited:
            warning_msg = f"You have sent too many messages recently. Please wait {remaining_time} seconds before sending another one."
            twilio_client.messages.create(
                body=warning_msg,
                from_=TWILIO_WHATSAPP_NUMBER,
                to=sender_number
            )
            performance_tracker.log_rate_limit_event(sender_number)
            return PlainTextResponse("OK")

        # --- RAG: Retrieve Context ---
        context_list = await retriever.retrieve_async(message_body) # Gets list of dicts
        context_str = "\n".join([ctx["content"] for ctx in context_list]) if context_list else "No relevant information found in the knowledge base."

        # --- Intent & Sentiment Classification (Placeholder - could be done by LLM or separate model) ---
        # For now, assume a simple classification based on keywords or use the LLM prompt
        # Let's use the LLM to help classify intent and sentiment as part of the prompt
        intent_classification_prompt = prompt_engine.generate_intent_classification_prompt(message_body, "en")
        # This would require a separate call or be integrated into the main prompt. Let's assume a simple rule-based approach for now or fetch from RAG metadata.
        detected_intent = Intent.OTHER # Placeholder - Implement logic
        detected_sentiment = Sentiment.NEUTRAL # Placeholder - Implement logic
        detected_urgency = Urgency.LOW # Placeholder - Implement logic based on keywords/sentiment

        # --- Build Conversation Context Object ---
        conversation_context_obj = ConversationContext(
            user_id=sender_number, # Use phone number as user ID for simplicity, consider a real user ID from DB
            session_id=session_id,
            conversation_history=[], # Implement history lookup if needed
            retrieved_context=context_str,
            user_profile=user_profile,
            intent=detected_intent,
            sentiment=detected_sentiment,
            urgency=detected_urgency,
            timestamp=datetime.now(timezone.utc),
            language_code="en" # Adjust based on detection
        )

        # --- Prompt Engineering ---
        system_prompt = prompt_engine.generate_system_prompt(conversation_context_obj)
        user_prompt = prompt_engine.build_user_prompt(message_body, language_code="en") # Assuming build_user_prompt exists or adapt

        # --- AI Generation ---
        raw_response = await call_groq_async(system_prompt, user_prompt)

        # --- Response Enhancement ---
        context_for_enhancer = {
            "language_code": "en",
            "intent": detected_intent.value
        }
        enhanced_response = response_enhancer.enhance(raw_response, context_for_enhancer)

        # --- Send Response via Twilio ---
        twilio_client.messages.create(
            body=enhanced_response,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=sender_number
        )
        logger.info(f"({session_id}) Sent response to {sender_number}")

        # --- Schedule Background Logging Task ---
        background_tasks.add_task(
            log_interaction_to_supabase_async,
            sender_number, message_body, enhanced_response, context_str,
            detected_intent, detected_sentiment, detected_urgency, session_id
        )

        # --- Log Performance Metric ---
        duration = time.perf_counter() - start_time
        performance_tracker.log_response_time(duration, detected_intent.value)

        return PlainTextResponse("OK")

    except TwilioRestException as e:
        logger.error(f"({session_id}) Twilio Error for {sender_number}: {e.code} - {e.msg}")
        sentry_sdk.capture_exception(e) # Capture in Sentry if active
        # Optionally send an error message to user via Twilio
        # twilio_client.messages.create(...)
        raise HTTPException(status_code=400, detail=f"Twilio Error: {e.msg}")

    except Exception as e:
        logger.error(f"({session_id}) Unexpected error processing webhook for {sender_number}: {e}")
        sentry_sdk.capture_exception(e) # Capture in Sentry if active
        # Optionally send a generic error message to user via Twilio
        # twilio_client.messages.create(...)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# --- Health Check Endpoint ---
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "environment": ENVIRONMENT}

# --- Metrics Endpoint (Optional, for external monitoring) ---
@app.get("/metrics")
async def get_metrics():
    """Endpoint to expose performance metrics (if not using Prometheus, adapt as needed)."""
    # Example: Return last N response times, error counts, etc.
    # This would typically integrate with a metrics library like prometheus-client
    return performance_tracker.get_current_metrics()

# --- Main Execution Block (for running with uvicorn directly) ---
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=PORT)