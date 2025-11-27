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
from twilio.rest import Client as TwilioRestClient # Renamed import to avoid naming conflict
from twilio.base.exceptions import TwilioRestException
from supabase import create_client, Client as SupabaseClient
import sentry_sdk
from datetime import datetime, timezone # Added import for datetime
import threading
from typing import Dict, List
import hashlib # Import for hashing if needed, though built-in 'hash' is used for session ID

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
from bot.rag.retriever import Retriever
from monitoring.sentry_config import SentryManager
from monitoring.performance import PerformanceTracker

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
    # Declare global variables that will be assigned here
    global twilio_client, supabase, prompt_engine, response_enhancer, retriever, performance_tracker

    logger.info("🚀 Starting up College WhatsApp Bot API...")

    # --- Initialize Shared Resources ---

    # Twilio Client
    twilio_client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) # Assign to global variable
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
    response_enhancer = ResponseEnhancer(trusted_domains=[f"{BOT_BEHAVIOR['college_name'].replace(' ', '').lower()}.edu"])
    logger.info("✅ ResponseEnhancer initialized.")

    # RAG Retriever
    retriever = Retriever()
    logger.info("✅ RAG Retriever initialized.")

    # Performance Tracker
    performance_tracker = PerformanceTracker(supabase_client=supabase)
    logger.info("✅ PerformanceTracker initialized.")

    # Initialize Sentry (if DSN is provided)
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=ENVIRONMENT,
            traces_sample_rate=1.0 if ENVIRONMENT == "production" else 0.1,
        )
        logger.info("✅ Sentry initialized.")
        # Assuming SentryManager.initialize is defined to accept the environment string only
        SentryManager.initialize(ENVIRONMENT)
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
async def call_groq_async(system_prompt: str, user_prompt: str) -> str: # Renamed function to match call
    """
    Asynchronously calls the Groq API with the system and user prompts.
    """
    import httpx
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 500
    }
    start_time = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
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
async def log_interaction_to_supabase_async( # Renamed function to match call
    user_phone: str, user_message: str, bot_response: str, context_used: str,
    intent_raw, sentiment_raw, urgency_raw, session_id: str
):
    """
    Asynchronously logs the conversation interaction to Supabase.
    Includes checks to ensure Enum instances are used correctly before accessing .value.
    """
    # Ensure parameters are Enum instances, not the classes themselves
    if intent_raw is Intent:
        logger.error(f"log_interaction_to_supabase_async: 'intent_raw' is the Intent *class*, not an instance. Defaulting to Intent.OTHER.")
        intent = Intent.OTHER
    elif isinstance(intent_raw, Intent):
        intent = intent_raw
    else:
        logger.error(f"log_interaction_to_supabase_async: 'intent_raw' is neither the Intent class nor an Intent instance ({type(intent_raw)}). Defaulting to Intent.OTHER.")
        intent = Intent.OTHER

    if sentiment_raw is Sentiment:
        logger.error(f"log_interaction_to_supabase_async: 'sentiment_raw' is the Sentiment *class*, not an instance. Defaulting to Sentiment.NEUTRAL.")
        sentiment = Sentiment.NEUTRAL
    elif isinstance(sentiment_raw, Sentiment):
        sentiment = sentiment_raw
    else:
        logger.error(f"log_interaction_to_supabase_async: 'sentiment_raw' is neither the Sentiment class nor a Sentiment instance ({type(sentiment_raw)}). Defaulting to Sentiment.NEUTRAL.")
        sentiment = Sentiment.NEUTRAL

    if urgency_raw is Urgency:
        logger.error(f"log_interaction_to_supabase_async: 'urgency_raw' is the Urgency *class*, not an instance. Defaulting to Urgency.LOW.")
        urgency = Urgency.LOW
    elif isinstance(urgency_raw, Urgency):
        urgency = urgency_raw
    else:
        logger.error(f"log_interaction_to_supabase_async: 'urgency_raw' is neither the Urgency class nor an Urgency instance ({type(urgency_raw)}). Defaulting to Urgency.LOW.")
        urgency = Urgency.LOW

    # Build the log entry dictionary using the checked Enum instances
    log_entry = {
        "user_id": user_phone,
        "user_message": user_message,
        "bot_response": bot_response,
        "timestamp": datetime.now(timezone.utc).isoformat(), # ISO format for Supabase timestamp
        "context_used": context_used[:5000], # Truncate if very long, adjust size as needed
        "language_code": "en",
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
        if SENTRY_DSN: # Only if SENTRY_DSN is active and initialized
            sentry_sdk.capture_exception(e)

# --- Webhook Endpoint ---
@app.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handles incoming messages from Twilio WhatsApp webhook."""
    start_time = time.perf_counter()
    # Use 'hash' built-in for session ID, modulo to keep it short
    session_id = f"sess_{int(time.time())}_{abs(hash(request.client.host)) % 10000}" # Simple session ID, using abs to ensure positive mod result
    sender_number = None # Initialize to avoid UnboundLocalError in exception handling if form_data access fails
    message_body = None # Initialize to avoid UnboundLocalError

    try:
        form_data = await request.form()
        message_body = form_data.get('Body', '').strip() # Initialize message_body here
        sender_number = form_data.get('From', '') # e.g., whatsapp:+1234567890
        user_profile = {"role": "student", "year": "unknown"} # Placeholder, fetch from DB if available

        logger.info(f"({session_id}) Received message from {sender_number}: {message_body[:50]}...")

        # --- Rate Limiting Check ---
        is_limited, remaining_time = is_rate_limited(sender_number)
        if is_limited:
            warning_msg = f"You have sent too many messages recently. Please wait {remaining_time} seconds before sending another one."
            # Use the GLOBAL twilio_client variable assigned in lifespan
            twilio_client.messages.create( # Use the global variable name 'twilio_client'
                body=warning_msg,
                from_=TWILIO_WHATSAPP_NUMBER, # Use config variable
                to=sender_number
            )
            performance_tracker.log_rate_limit_event(sender_number)
            return PlainTextResponse("OK")

        # --- RAG: Retrieve Context (with error handling and timing) ---
        rag_start_time = time.perf_counter() # <--- ADD TIMING LOGIC
        try:
            context_list = await retriever.retrieve_async(message_body) # Gets list of dicts or other format from retriever
            # Safe extraction of context with proper error handling
            if isinstance(context_list, list) and len(context_list) > 0: # Check if it's a list AND not empty
                # Handle both dict and string items in the list
                context_parts = []
                for ctx in context_list:
                    if isinstance(ctx, dict):
                        # Safely get content from dict
                        content = ctx.get("content", "") or ctx.get("text", "") or str(ctx)
                        context_parts.append(content)
                    elif isinstance(ctx, str):
                        context_parts.append(ctx)
                    else:
                        logger.warning(f"({session_id}) Unexpected context item type: {type(ctx)}")
                        context_parts.append(str(ctx))
                context_str = "\n".join(context_parts) if context_parts else "No relevant information found in the knowledge base." # This handles case where list exists but all items resulted in empty strings
            else:
                context_str = "No relevant information found in the knowledge base."
                logger.warning(f"({session_id}) Retriever returned unexpected format or empty list: {type(context_list)}") # Clarified message
        except Exception as e:
            logger.error(f"({session_id}) Error during RAG retrieval: {e}", exc_info=True)
            context_str = "No relevant information found in the knowledge base."
            if SENTRY_DSN:
                sentry_sdk.capture_exception(e)
        rag_duration = time.perf_counter() - rag_start_time # <--- CALCULATE DURATION
        logger.debug(f"({session_id}) RAG retrieval took {rag_duration:.2f}s") # <--- LOG DURATION

        # --- Intent & Sentiment Classification (Placeholder - could be done by LLM or separate model) ---
        # For now, assume a simple classification based on keywords or use the LLM prompt
        # Let's use the LLM to help classify intent and sentiment as part of the prompt
        # intent_classification_prompt = prompt_engine.generate_intent_classification_prompt(message_body, "en")
        # This would require a separate call or be integrated into the main prompt. Let's assume a simple rule-based approach for now or fetch from RAG metadata.

        # --- CORRECTED: Ensure these are Enum *instances*, not the classes ---
        # These assignments must be Enum *members* (instances like Intent.OTHER), not the *class* objects (Intent).
        # The error 'Sentiment' indicates that one of these variables accidentally held the *class* object.
        # The code below assigns instances correctly, but let's add checks just before the logging call to be absolutely sure.

        # Placeholder logic - Implement actual classification
        # Ensure these are the *instances* of the Enum classes defined in prompt_engine.py
        # Example: from bot.prompts.prompt_engine import Intent, Sentiment, Urgency
        # Make sure these are imported correctly at the top of this file.
        detected_intent = Intent.OTHER # This should be an Enum *instance*
        detected_sentiment = Sentiment.NEUTRAL # This should be an Enum *instance*
        detected_urgency = Urgency.LOW # This should be an Enum *instance*

        # --- ADD CHECKS: Before passing to prompt_engine (or any place .value is accessed later) ---
        # Verify types just before passing to prompt_engine or any place .value is accessed later
        # These checks confirm the *type* of the variables before they are used.
        # This is a safeguard. The assignment above should be correct, but if something went wrong elsewhere, this catches it.
        if not isinstance(detected_intent, Intent):
             logger.error(f"({session_id}) handle_webhook: detected_intent is not an Intent enum member: {type(detected_intent)}, value: {detected_intent}. Defaulting to Intent.OTHER.")
             detected_intent = Intent.OTHER # Fallback to an instance
        if not isinstance(detected_sentiment, Sentiment):
             logger.error(f"({session_id}) handle_webhook: detected_sentiment is not a Sentiment enum member: {type(detected_sentiment)}, value: {detected_sentiment}. Defaulting to Sentiment.NEUTRAL.")
             detected_sentiment = Sentiment.NEUTRAL # Fallback to an instance
        if not isinstance(detected_urgency, Urgency):
             logger.error(f"({session_id}) handle_webhook: detected_urgency is not an Urgency enum member: {type(detected_urgency)}, value: {detected_urgency}. Defaulting to Urgency.LOW.")
             detected_urgency = Urgency.LOW # Fallback to an instance

        # --- Build Conversation Context Object ---
        # Ensure the ConversationContext is defined to accept Enum instances for intent, sentiment, urgency
        # in bot.prompts.prompt_engine.py. The fields should be typed like: intent: Intent, sentiment: Sentiment, urgency: Urgency
        conversation_context_obj = ConversationContext(
            user_id=sender_number, # Use phone number as user ID for simplicity, consider a real user ID from DB
            session_id=session_id,
            conversation_history=[], # Implement history lookup if needed
            retrieved_context=context_str,
            user_profile=user_profile,
            intent=detected_intent, # Pass the Enum *instance*
            sentiment=detected_sentiment, # Pass the Enum *instance*
            urgency=detected_urgency, # Pass the Enum *instance*
            timestamp=datetime.now(timezone.utc),
            language_code="en" # Adjust based on detection
        )

        # --- Prompt Engineering (with timing) ---
        prompt_start_time = time.perf_counter() # <--- ADD TIMING LOGIC
        system_prompt = prompt_engine.generate_system_prompt(conversation_context_obj)
        user_prompt = prompt_engine.build_user_message_prompt(message_body, language_code="en") # <-- Use the correct method name
        prompt_duration = time.perf_counter() - prompt_start_time # <--- CALCULATE DURATION
        logger.debug(f"({session_id}) Prompt engineering took {prompt_duration:.2f}s") # <--- LOG DURATION

        # --- AI Generation (with timing) ---
        ai_start_time = time.perf_counter() # <--- ADD TIMING LOGIC
        raw_response = await call_groq_async(system_prompt, user_prompt)
        ai_duration = time.perf_counter() - ai_start_time # <--- CALCULATE DURATION
        logger.debug(f"({session_id}) AI generation (Groq) took {ai_duration:.2f}s") # <--- LOG DURATION

        # --- Response Enhancement (with timing) ---
        enhancer_start_time = time.perf_counter() # <--- ADD TIMING LOGIC
        context_for_enhancer = {
            "language_code": "en",
            "intent": detected_intent.value # Access .value *after* confirming it's an Enum instance
        }
        enhanced_response = response_enhancer.enhance(raw_response, context_for_enhancer)
        enhancer_duration = time.perf_counter() - enhancer_start_time # <--- CALCULATE DURATION
        logger.debug(f"({session_id}) Response enhancement took {enhancer_duration:.2f}s") # <--- LOG DURATION

        # --- Truncate Response if Necessary (NEW SECTION) ---
        MAX_MESSAGE_LENGTH = 1600
        TRUNCATION_SUFFIX = "..." # Indicator that the message was shortened

        # Check length and truncate if necessary
        if len(enhanced_response) > MAX_MESSAGE_LENGTH:
            # Truncate and add suffix
            truncated_response = enhanced_response[:MAX_MESSAGE_LENGTH - len(TRUNCATION_SUFFIX)] + TRUNCATION_SUFFIX
            logger.warning(f"({session_id}) Response was too long ({len(enhanced_response)} chars) and has been truncated to {MAX_MESSAGE_LENGTH} chars.")
            message_to_send = truncated_response
        else:
            message_to_send = enhanced_response

        # --- Send Response via Twilio (using the potentially truncated message) ---
        # Use the GLOBAL twilio_client variable
        twilio_client.messages.create(
            body=message_to_send, # Send the potentially truncated message
            from_=TWILIO_WHATSAPP_NUMBER,
            to=sender_number
        )
        logger.info(f"({session_id}) Sent response to {sender_number}")

        # --- Schedule Background Logging Task ---
        # Pass the *Enum instances* (detected_intent, detected_sentiment, detected_urgency), not the classes
        # Use the correctly named function
        background_tasks.add_task(
            log_interaction_to_supabase_async,
            sender_number, message_body, message_to_send, context_str, # Use the potentially truncated message for logging too, if desired
            detected_intent, detected_sentiment, detected_urgency, session_id
        )

        # --- Log Performance Metric (with timing breakdown) ---
        duration = time.perf_counter() - start_time
        total_processing_time = rag_duration + prompt_duration + ai_duration + enhancer_duration
        logger.debug(f"({session_id}) Estimated internal processing time: {total_processing_time:.2f}s")
        performance_tracker.log_response_time(duration, detected_intent.value) # Use the *value* for tracking

        return PlainTextResponse("OK")

    except TwilioRestException as e:
        logger.error(f"({session_id}) Twilio Error for {sender_number}: {e.code} - {e.msg}")
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e) # Capture in Sentry if active
        # Optionally send an error message to user via Twilio
        # twilio_client.messages.create(...)
        raise HTTPException(status_code=400, detail=f"Twilio Error: {e.msg}")

    except Exception as e:
        logger.error(f"({session_id}) Unexpected error processing webhook for {sender_number}: {e}", exc_info=True)
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e) # Capture in Sentry if active
        # Optionally send a generic error message to user via Twilio
        # twilio_client.messages.create(...)
        # Include message_body in the error detail if it's available, otherwise log it separately
        error_detail = f"Internal Server Error"
        if message_body: # Use the variable assigned from form_data
             logger.error(f"({session_id}) Error occurred while processing message: '{message_body[:100]}...'") # Log truncated message for context
        raise HTTPException(status_code=500, detail=error_detail)
    
# --- Health Check Endpoint ---
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "environment": ENVIRONMENT}

# --- Root Endpoint (fixes the "Not Found" issue when visiting the domain) ---
@app.get("/")
async def root():
    """Root endpoint to provide information about the service."""
    return {
        "service": "College WhatsApp Bot API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "webhook": "/webhook (POST only)",
            "metrics": "/metrics"
        }
    }

# --- Metrics Endpoint (Optional, for external monitoring) ---
@app.get("/metrics")
async def get_metrics():
    """Endpoint to expose performance metrics."""
    try:
        # Assuming performance_tracker has a method get_current_metrics
        # You need to implement this method in your PerformanceTracker class if it doesn't exist
        # Example structure for PerformanceTracker class:
        # class PerformanceTracker:
        #     # ... (initialization code) ...
        #     def get_current_metrics(self):
        #         # Return a dictionary with current metrics like response times, error counts, etc.
        #         # This is an example, implement based on your needs
        #         return {
        #             "average_response_time_last_5m": 1.23, # seconds
        #             "error_count_last_5m": 0,
        #             "total_interactions_last_5m": 100,
        #             # ... other metrics ...
        #         }
        return performance_tracker.get_current_metrics() # Call the method on the global instance
    except AttributeError:
        logger.error("PerformanceTracker does not have a 'get_current_metrics' method implemented.")
        return {"error": "PerformanceTracker method 'get_current_metrics' not implemented"}
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        return {"error": "Unable to retrieve metrics"}

# --- Main Execution Block (for running with uvicorn directly) ---
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=PORT)