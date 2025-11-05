"""
Unit Tests for the Prompt Engineering System (`bot/prompts/prompt_engine.py`).

These tests verify that prompts are generated correctly based on
context, intent, sentiment, language, and user profile.
"""
import pytest
from bot.prompts.prompt_engine import PromptEngine, ConversationContext, Intent, Sentiment, Urgency
from datetime import datetime, timezone

# --- Test Prompt Engine Initialization ---
def test_prompt_engine_initialization():
    """Test that the PromptEngine initializes correctly."""
    pe = PromptEngine(college_name="TestU", knowledge_base_metadata={})
    assert pe.college_name == "TestU"
    assert pe.knowledge_base_metadata == {}

# --- Test System Prompt Generation ---
def test_generate_system_prompt_basic():
    """Test generating a basic system prompt."""
    pe = PromptEngine(college_name="TestU", knowledge_base_metadata={})
    context = "Tuition fees are $20,000 per year."
    conv_context = ConversationContext(
        user_id="user123",
        session_id="sess456",
        conversation_history=[],
        retrieved_context=context,
        user_profile={"role": "student"},
        intent=Intent.FEES,
        sentiment=Sentiment.NEUTRAL,
        urgency=Urgency.LOW,
        timestamp=datetime.now(timezone.utc),
        language_code="en"
    )

    prompt = pe.generate_system_prompt(conv_context)

    # Check for key elements
    assert "TestU" in prompt
    assert "Tuition fees are $20,000 per year." in prompt
    assert "fees" in prompt # Intent reflected
    assert "Advisor" in prompt # Persona based on intent

def test_generate_system_prompt_multilingual():
    """Test generating a system prompt for a different language."""
    pe = PromptEngine(college_name="TestU", knowledge_base_metadata={})
    context = "Ücretler senelik 20.000$'dır."
    conv_context = ConversationContext(
        user_id="user123",
        session_id="sess456",
        conversation_history=[],
        retrieved_context=context,
        user_profile={"role": "student"},
        intent=Intent.FEES,
        sentiment=Sentiment.NEUTRAL,
        urgency=Urgency.LOW,
        timestamp=datetime.now(timezone.utc),
        language_code="tr" # Turkish
    )

    prompt = pe.generate_system_prompt(conv_context)

    # Check for Turkish-specific elements (if defined in the template)
    # This test assumes the template handles language switching correctly
    assert "TestU" in prompt # College name should be consistent
    assert "Ücretler senelik 20.000$'dır." in prompt # Context in Turkish

def test_generate_system_prompt_with_history():
    """Test generating a system prompt including conversation history."""
    pe = PromptEngine(college_name="TestU", knowledge_base_metadata={})
    context = "CS program details."
    history = [{"message": "Hi", "response": "Hello!"}, {"message": "What is CS?", "response": "Computer Science..."}]
    conv_context = ConversationContext(
        user_id="user123",
        session_id="sess456",
        conversation_history=history,
        retrieved_context=context,
        user_profile={"role": "prospect"},
        intent=Intent.COURSES,
        sentiment=Sentiment.POSITIVE,
        urgency=Urgency.MEDIUM,
        timestamp=datetime.now(timezone.utc),
        language_code="en"
    )

    prompt = pe.generate_system_prompt(conv_context)

    # Check for history summary inclusion
    assert "Hi" in prompt
    assert "Computer Science" in prompt
    assert "prospect" in prompt # User profile reflected

# --- Test Fallback Responses ---
def test_get_fallback_response():
    """Test getting a fallback response."""
    pe = PromptEngine(college_name="TestU", knowledge_base_metadata={})
    fallback = pe.get_fallback_response(language_code="en", error_type="no_context")

    assert "I don't have specific information" in fallback
    assert "TestU" in fallback # Should reference college

def test_get_fallback_response_escalation():
    """Test getting an escalation fallback response."""
    pe = PromptEngine(college_name="TestU", knowledge_base_metadata={})
    context = ConversationContext(
        user_id="user123",
        session_id="sess456",
        conversation_history=[],
        retrieved_context="",
        user_profile={"role": "student"},
        intent=Intent.COMPLAINT,
        sentiment=Sentiment.VERY_NEGATIVE,
        urgency=Urgency.CRITICAL,
        timestamp=datetime.now(timezone.utc),
        language_code="en"
    )
    fallback = pe.get_fallback_response(language_code="en", error_type="escalation_triggered", context=context)

    assert "escalation" in fallback.lower() or "support" in fallback.lower() # Check for escalation hint