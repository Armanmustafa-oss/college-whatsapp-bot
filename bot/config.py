"""
⚙️ Enterprise Configuration Management
=======================================
Centralized, validated, and secure configuration loader for the College WhatsApp Bot.
Handles environment variables, secrets, and runtime settings with robust error handling.
"""

import os
import logging
from typing import Optional
# Optional: support .env files if python-dotenv is installed; otherwise define a no-op loader.
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    def load_dotenv(*args, **kwargs):
        # python-dotenv is not installed; skip loading .env files.
        return False
import secrets
import string

# Load environment variables from .env file (if python-dotenv is available)
load_dotenv()

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def _validate_url(url: str, name: str) -> str:
    """Validates a URL environment variable."""
    if not url or not url.startswith(('http://', 'https://')):
        raise ConfigError(f"Invalid or missing {name}: {url}")
    return url

def _validate_api_key(key: str, name: str) -> str:
    """Validates an API key environment variable."""
    if not key or len(key) < 10: # Basic length check
        raise ConfigError(f"Invalid or missing {name}: {key}")
    return key

def _validate_twilio_number(number: str) -> str:
    """Validates a Twilio WhatsApp number format (basic check). Expects 'whatsapp:+...' format."""
    if not number:
        raise ConfigError(f"TWILIO_WHATSAPP_NUMBER is missing or empty.")

    # Check if it starts with the expected 'whatsapp:' prefix
    if number.startswith('whatsapp:'):
        # Extract the actual phone number part (after 'whatsapp:')
        phone_part = number[len('whatsapp:'):] # e.g., '+14155238886'
        if not phone_part.startswith('+'):
            raise ConfigError(f"Invalid TWILIO_WHATSAPP_NUMBER: {number}. The number part after 'whatsapp:' must start with '+'.")
    else:
        # If it doesn't start with 'whatsapp:', it might be a raw number (less common for WhatsApp)
        # If you intend to support raw numbers, check for '+' here.
        # If you only intend for WhatsApp numbers (which is standard), this branch should also fail.
        raise ConfigError(f"Invalid TWILIO_WHATSAPP_NUMBER: {number}. Must start with 'whatsapp:'.")
        # Alternatively, if raw numbers are allowed (not recommended for WhatsApp Business API):
        # if not number.startswith('+'):
        #     raise ConfigError(f"Invalid TWILIO_WHATSAPP_NUMBER: {number}. Must start with '+' or 'whatsapp:+'.")

    # If we reach here, the format is valid (either raw +... or whatsapp:+...)
    # Return the *original* number string as it was provided (e.g., 'whatsapp:+14155238886')
    # This is what your Twilio client will expect.
    return number # Return the original number string (with 'whatsapp:' prefix if it had it)

def _get_supabase_url() -> str:
    """Retrieves and validates SUPABASE_URL."""
    url = os.getenv("SUPABASE_URL")
    if not url:
        raise ConfigError("SUPABASE_URL must be set in environment variables.")
    return _validate_url(url, "SUPABASE_URL")

def _get_supabase_key() -> str:
    """Retrieves and validates SUPABASE_KEY."""
    key = os.getenv("SUPABASE_KEY")
    if not key:
        raise ConfigError("SUPABASE_KEY must be set in environment variables.")
    return _validate_api_key(key, "SUPABASE_KEY")

def _get_groq_api_key() -> str:
    """Retrieves and validates GROQ_API_KEY."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ConfigError("GROQ_API_KEY must be set in environment variables.")
    return _validate_api_key(key, "GROQ_API_KEY")

def _get_twilio_credentials() -> tuple[str, str, str]:
    """Retrieves and validates Twilio credentials."""
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    number = os.getenv("TWILIO_WHATSAPP_NUMBER")

    if not sid:
        raise ConfigError("TWILIO_ACCOUNT_SID must be set in environment variables.")
    if not token:
        raise ConfigError("TWILIO_AUTH_TOKEN must be set in environment variables.")
    if not number:
        raise ConfigError("TWILIO_WHATSAPP_NUMBER must be set in environment variables.")

    _validate_api_key(sid, "TWILIO_ACCOUNT_SID")
    _validate_api_key(token, "TWILIO_AUTH_TOKEN")
    _validate_twilio_number(number)

    return sid, token, number

def _get_sentry_dsn() -> Optional[str]:
    """Retrieves SENTRY_DSN (optional)."""
    dsn = os.getenv("SENTRY_DSN")
    if dsn:
        try:
            _validate_url(dsn, "SENTRY_DSN")
        except ConfigError as e:
            logger.warning(f"Invalid SENTRY_DSN provided, disabling Sentry: {e}")
            return None
    return dsn

def _get_environment() -> str:
    """Retrieves environment type."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env not in ["development", "staging", "production"]:
        logger.warning(f"Unknown environment '{env}', defaulting to 'development'.")
        env = "development"
    return env

def _get_port() -> int:
    """Retrieves and validates the server port."""
    port_str = os.getenv("PORT", "8000")
    try:
        port = int(port_str)
        if not (1024 <= port <= 65535):
            raise ValueError("Port out of range.")
    except ValueError:
        raise ConfigError(f"Invalid PORT: {port_str}. Must be an integer between 1024 and 65535.")
    return port

def _get_rate_limit_config() -> tuple[int, int]:
    """Retrieves rate limiting configuration."""
    try:
        messages = int(os.getenv("RATE_LIMIT_MESSAGES", "10"))
        window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        if messages <= 0 or window <= 0:
             raise ValueError("Rate limits must be positive integers.")
    except ValueError as e:
        raise ConfigError(f"Invalid rate limit configuration: {e}")
    return messages, window

def _get_bot_behavior_config() -> dict:
    """Retrieves bot-specific behavioral settings."""
    return {
        "default_language": os.getenv("DEFAULT_LANGUAGE", "en"),
        "max_message_length": int(os.getenv("MAX_MESSAGE_LENGTH", "1600")), # Characters
        "max_conversation_history": int(os.getenv("MAX_CONVERSATION_HISTORY", "10")), # Number of exchanges
        "college_name": os.getenv("COLLEGE_NAME", "Default College"), # Used by PromptEngine
    }

# --- Load Configuration Values ---
try:
    # Core Services
    SUPABASE_URL = _get_supabase_url()
    SUPABASE_KEY = _get_supabase_key()
    GROQ_API_KEY = _get_groq_api_key()
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER = _get_twilio_credentials()

    # Monitoring
    SENTRY_DSN = _get_sentry_dsn()

    # Runtime Environment
    ENVIRONMENT = _get_environment()
    PORT = _get_port()

    # Rate Limiting
    RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW = _get_rate_limit_config()

    # Bot Behavior
    BOT_BEHAVIOR = _get_bot_behavior_config()

    logger.info(f"Configuration loaded successfully for environment: {ENVIRONMENT}")

except ConfigError as e:
    logger.critical(f"Configuration error: {e}")
    raise # Re-raise to halt application startup
except Exception as e:
    logger.critical(f"Unexpected error loading configuration: {e}")
    raise # Re-raise to halt application startup

# --- Expose Configuration ---
__all__ = [
    'SUPABASE_URL', 'SUPABASE_KEY', 'GROQ_API_KEY',
    'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_WHATSAPP_NUMBER',
    'SENTRY_DSN', 'ENVIRONMENT', 'PORT',
    'RATE_LIMIT_MESSAGES', 'RATE_LIMIT_WINDOW',
    'BOT_BEHAVIOR'
]

# Example usage (if run as main):
# if __name__ == "__main__":
#     print(f"Loaded config for environment: {ENVIRONMENT}")
#     print(f"Supabase URL: {SUPABASE_URL[:20]}...") # Print first 20 chars for safety
#     print(f"Rate Limit: {RATE_LIMIT_MESSAGES} messages per {RATE_LIMIT_WINDOW} seconds")