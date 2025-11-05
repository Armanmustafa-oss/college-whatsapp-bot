"""
Unit & Integration Tests for the Core Bot Logic (`bot/main.py`, `bot/config.py`, etc.)

These tests verify the core message processing pipeline,
configuration loading, rate limiting, and interaction with
external services (mocked) without requiring a full database or RAG setup.
"""
import asyncio
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from twilio.rest import Client as TwilioRestClient
from supabase import Client as SupabaseClient
import sentry_sdk
from bot.main import app, is_rate_limited, message_counts
from bot.config import ConfigError
from monitoring.sentry_config import SentryManager

# --- Test Client for FastAPI ---
client = TestClient(app)

# --- Test Configuration Loading ---
def test_config_loading_success(monkeypatch):
    """Test that config loads correctly with all required variables."""
    # Set required environment variables
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "fake-key")
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACfake")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "fake-token")
    monkeypatch.setenv("TWILIO_WHATSAPP_NUMBER", "+1234567890")
    monkeypatch.setenv("ENVIRONMENT", "test")

    # Reload config module to pick up patched env vars
    import importlib
    import bot.config
    importlib.reload(bot.config)

    # Assertions based on the loaded values
    assert bot.config.SUPABASE_URL == "https://fake.supabase.co"
    assert bot.config.GROQ_API_KEY == "fake-groq-key"
    assert bot.config.TWILIO_ACCOUNT_SID == "ACfake"
    assert bot.config.ENVIRONMENT == "test"

def test_config_loading_missing_var(monkeypatch):
    """Test that config raises an error if a required variable is missing."""
    # Remove a required variable
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.setenv("SUPABASE_KEY", "fake-key")
    monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACfake")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "fake-token")
    monkeypatch.setenv("TWILIO_WHATSAPP_NUMBER", "+1234567890")

    # Reload config module - this should raise ConfigError
    import importlib
    import bot.config
    with pytest.raises(ConfigError):
        importlib.reload(bot.config)

# --- Test Rate Limiting Logic ---
def test_rate_limiting_within_limit():
    """Test that a user within the rate limit is not blocked."""
    # Clear counts for a clean test
    message_counts.clear()
    phone_number = "whatsapp:+1234567890"

    # Add 4 messages (less than limit of 10)
    for _ in range(4):
        is_limited, _ = is_rate_limited(phone_number)
        assert not is_limited # Should not be limited yet

def test_rate_limiting_exceeded():
    """Test that a user exceeding the rate limit is blocked."""
    # Clear counts for a clean test
    message_counts.clear()
    phone_number = "whatsapp:+1234567890"

    # Add 10 messages (equal to limit)
    for _ in range(10):
        is_limited, _ = is_rate_limited(phone_number)
        assert not is_limited # Should not be limited until the 11th call

    # The 11th call should be limited
    is_limited, remaining_time = is_rate_limited(phone_number)
    assert is_limited
    assert remaining_time >= 0 # Should have some time remaining

# --- Test Webhook Endpoint (Mock External Dependencies) ---
@patch("bot.main.twilio_client") # Mock Twilio client
@patch("bot.main.supabase") # Mock Supabase client
@patch("bot.main.prompt_engine") # Mock PromptEngine
@patch("bot.main.response_enhancer") # Mock ResponseEnhancer
@patch("bot.main.retriever") # Mock Retriever
@patch("bot.main.call_groq_async", new_callable=AsyncMock) # Mock Groq call
@pytest.mark.asyncio
async def test_webhook_success(mock_groq_call, mock_retriever, mock_enhancer, mock_prompt_eng, mock_supabase, mock_twilio_client):
    """Test successful message processing via the webhook."""
    # Mock return values
    mock_retriever.retrieve_async = AsyncMock(return_value=[{"content": "Mock context from RAG"}])
    mock_prompt_eng.generate_system_prompt.return_value = "Mock System Prompt"
    mock_prompt_eng.build_user_prompt.return_value = "Mock User Prompt"
    mock_groq_call.return_value = "Mock AI Response"
    mock_enhancer.enhance.return_value = "Enhanced Mock AI Response"
    mock_supabase.table.return_value.insert.return_value.execute = MagicMock()

    # Simulate a request
    response = client.post("/webhook", data={
        "From": "whatsapp:+1234567890",
        "Body": "Hello, what are the tuition fees?"
    })

    # Assertions
    assert response.status_code == 200
    assert response.text == "OK"
    mock_twilio_client.messages.create.assert_called_once()
    sent_call_args = mock_twilio_client.messages.create.call_args
    assert sent_call_args[1]["body"] == "Enhanced Mock AI Response"
    assert sent_call_args[1]["to"] == "whatsapp:+1234567890"

@patch("bot.main.twilio_client")
def test_health_check(mock_twilio_client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["environment"] in ["development", "staging", "production"]