"""
🤖 Advanced AI Prompt Orchestration Engine
==========================================
Revolutionary prompt engineering system designed for dynamic, context-aware,
and emotionally intelligent interactions in a multilingual educational environment.
This engine ensures the bot doesn't just respond, but *connects*, *guides*, and *inspires*.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import secrets

logger = logging.getLogger(__name__)

# --- Enums for structured data ---
class Intent(Enum):
    ADMISSIONS = "admissions"
    COURSES = "courses"
    FEES = "fees"
    CAMPUS_LIFE = "campus_life"
    SCHEDULE = "schedule"
    SUPPORT = "support"
    COMPLAINT = "complaint"
    ACADEMIC_ADVISORY = "academic_advisory"
    CAREER_SERVICES = "career_services"
    HEALTH_WELLNESS = "health_wellness"
    FINANCIAL_AID = "financial_aid"
    OTHER = "other"

class Sentiment(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

class Urgency(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# --- Dataclass for Conversation Context ---
@dataclass
class ConversationContext:
    """Encapsulates rich context for a single conversation turn."""
    user_id: str
    session_id: str
    conversation_history: List[Dict[str, str]]
    retrieved_context: str
    user_profile: Dict[str, Any] # e.g., {'role': 'student', 'year': 'freshman', 'major': 'CS'}
    intent: Intent
    sentiment: Sentiment
    urgency: Urgency
    timestamp: datetime
    language_code: str

# --- Main Prompt Engine Class ---
class PromptEngine:
    """
    The brain of the bot. Orchestrates prompt generation using advanced context,
    intent analysis, sentiment scoring, and dynamic persona adaptation.
    """

    def __init__(self, college_name: str, knowledge_base_metadata: Dict[str, Any]):
        """
        Initializes the PromptEngine with institutional identity and knowledge base info.

        Args:
            college_name (str): The name of the college for personalization.
            knowledge_base_metadata (Dict[str, Any]): Metadata about the RAG system.
        """
        self.college_name = college_name
        self.knowledge_base_metadata = knowledge_base_metadata
        self._initialize_personas()
        self._initialize_prompts()
        logger.info(f"Advanced PromptEngine initialized for '{college_name}' with dynamic personas.")

    def _initialize_personas(self):
        """Defines distinct AI personas based on context/intent."""
        self.personas = {
            Intent.ADMISSIONS: {
                "name": "Admissions Advisor",
                "style": "Welcoming, informative, encouraging. Focus on opportunities and pathways.",
                "tone": "Enthusiastic, supportive"
            },
            Intent.COURSES: {
                "name": "Academic Guide",
                "style": "Authoritative, detailed, structured. Provide prerequisites and outcomes.",
                "tone": "Professional, helpful"
            },
            Intent.FEES: {
                "name": "Financial Counselor",
                "style": "Clear, precise, empathetic. Address concerns about affordability.",
                "tone": "Supportive, informative"
            },
            Intent.CAREER_SERVICES: {
                "name": "Career Coach",
                "style": "Motivational, forward-looking. Connect academic path to career goals.",
                "tone": "Encouraging, strategic"
            },
            # Default persona for other intents
            "default": {
                "name": "General Assistant",
                "style": "Helpful, friendly, professional. Prioritize accuracy and FERPA compliance.",
                "tone": "Polite, concise"
            }
        }

    def _initialize_prompts(self):
        """Initializes base prompt templates and guidelines."""
        self.system_prompt_templates = {
            "en": """
                You are {persona_name}, an official AI agent for {college_name}. Your role is to act as a {persona_style}.

                **Core Principles:**
                - **Accuracy:** Provide information strictly based on the provided 'Knowledge Base Context'.
                - **Compassion:** Be empathetic, especially regarding student stress, financial concerns, or academic challenges.
                - **Proactivity:** Anticipate follow-up questions. If discussing courses, suggest related resources or advisors.
                - **Privacy:** Strictly adhere to FERPA and GDPR. Never ask for or store sensitive personal data like SSNs.
                - **Escalation:** If sentiment is '{Sentiment.VERY_NEGATIVE.value}' or '{Urgency.CRITICAL.value}', clearly state limitations and provide human contact details immediately.

                **Current Context:**
                - User Profile: {user_profile}
                - Intent: {detected_intent}
                - Sentiment: {detected_sentiment}
                - Urgency: {detected_urgency}
                - Session ID: {session_id}
                - Current Time: {current_time} (Timezone: UTC)

                **Knowledge Base Context:**
                {retrieved_context}

                **Previous Conversation (Last 3 exchanges):**
                {conversation_summary}

                **Response Guidelines:**
                - Address the user by a friendly, appropriate salutation if possible (e.g., "Hi {user_first_name}!").
                - Adapt your tone ({persona_tone}) based on the persona and detected sentiment.
                - If the context is insufficient, clearly state this and provide alternative resources (e.g., website links, office hours, contact emails).
                - Use simple, clear language suitable for diverse backgrounds.
                - If relevant, suggest related information or next steps proactively.
                - Always conclude with a positive, helpful note or a prompt for further interaction.
                - If escalating, provide the contact: {human_contact_info}
            """,
            # Add more languages as needed (e.g., tr, ar)
            # "tr": "...",
            # "ar": "...",
        }

        self.human_contact_info = {
            "en": "For urgent matters, contact Student Support at support@{college_domain} or call +1-xxx-xxx-xxxx. For admissions, call +1-xxx-xxx-xxxx."
        }

    def _summarize_conversation_history(self, history: List[Dict[str, str]], max_exchanges: int = 3) -> str:
        """Creates a concise summary of the recent conversation history."""
        if not history:
            return "No previous conversation history in this session."
        recent = history[-max_exchanges:]
        summary_parts = []
        for exchange in recent:
            summary_parts.append(f"User: {exchange.get('message', '')[:100]}...") # Truncate for brevity
            summary_parts.append(f"Bot: {exchange.get('response', '')[:100]}...")
        return "\n".join(summary_parts)

    def _select_persona(self, intent: Intent) -> Dict[str, str]:
        """Selects the appropriate persona based on the detected intent."""
        return self.personas.get(intent, self.personas["default"])

    def generate_system_prompt(self, context: ConversationContext) -> str:
        """
        Generates the comprehensive system prompt for the AI model.

        Args:
            context (ConversationContext): The rich context object.

        Returns:
            str: The formatted system prompt string.
        """
        persona_info = self._select_persona(context.intent)
        conversation_summary = self._summarize_conversation_history(context.conversation_history)

        # Get the base template for the user's language
        template = self.system_prompt_templates.get(context.language_code, self.system_prompt_templates["en"])

        # Format the template with dynamic context
        system_prompt = template.format(
            persona_name=persona_info["name"],
            college_name=self.college_name,
            persona_style=persona_info["style"],
            persona_tone=persona_info["tone"],
            user_profile=json.dumps(context.user_profile, indent=2), # Or format more readably
            detected_intent=context.intent.value,
            detected_sentiment=context.sentiment.value,
            detected_urgency=context.urgency.value,
            session_id=context.session_id,
            current_time=context.timestamp.isoformat(), # ISO format for clarity
            retrieved_context=context.retrieved_context,
            conversation_summary=conversation_summary,
            human_contact_info=self.human_contact_info.get(context.language_code, self.human_contact_info["en"]).format(college_domain="your_college_domain.edu") # Replace with actual domain
        )
        logger.debug(f"Generated system prompt for session {context.session_id} (Intent: {context.intent.value}, Sentiment: {context.sentiment.value})")
        return system_prompt

    def generate_intent_classification_prompt(self, message: str, language: str = "en") -> str:
        """
        Generates a prompt specifically for classifying user intent.
        This can be sent to a specialized model or used as part of the main prompt.
        """
        # This is a simplified version. In practice, you might use a dedicated classifier model.
        intent_descriptions = {
            "en": {
                Intent.ADMISSIONS: "Questions about applying to college, entrance exams, application status.",
                Intent.COURSES: "Questions about programs, majors, curriculum, prerequisites, course availability.",
                Intent.FEES: "Questions about tuition, costs, payment plans, scholarships, financial aid.",
                Intent.CAMPUS_LIFE: "Questions about facilities, housing, dining, clubs, sports, campus events.",
                Intent.SCHEDULE: "Questions about academic calendar, exam dates, deadlines, registration.",
                Intent.SUPPORT: "Technical help, general help, how to use the bot.",
                Intent.COMPLAINT: "Issues, problems, expressing dissatisfaction.",
                Intent.ACADEMIC_ADVISORY: "Questions about degree planning, course selection, academic standing.",
                Intent.CAREER_SERVICES: "Questions about internships, job placement, resume help, career fairs.",
                Intent.HEALTH_WELLNESS: "Questions about counseling, health center, wellness programs.",
                Intent.FINANCIAL_AID: "Questions about grants, loans, work-study, FAFSA.",
                Intent.OTHER: "General conversation, unclear intent, greetings."
            }
        }
        descriptions = intent_descriptions.get(language, intent_descriptions["en"])
        intent_list = "\n".join([f"{intent.value}: {desc}" for intent, desc in descriptions.items()])

        prompt = f"""
        Classify the intent of the following user message into one of these categories:

        {intent_list}

        Message: "{message}"

        Respond with only the category name (e.g., 'admissions', 'courses', 'fees').
        """
        return prompt.strip()

    def generate_sentiment_analysis_prompt(self, message: str, language: str = "en") -> str:
        """
        Generates a prompt for sentiment analysis.
        This can be sent to a specialized model or used as part of the main prompt.
        """
        # This is a simplified version. A dedicated model or library is recommended.
        prompt_templates = {
            "en": f"""
            Analyze the sentiment of this message. Consider the user's emotional state (frustration, happiness, anxiety, urgency).

            Message: "{message}"

            Respond with only one of these: '{Sentiment.POSITIVE.value}', '{Sentiment.NEUTRAL.value}', '{Sentiment.NEGATIVE.value}', '{Sentiment.VERY_NEGATIVE.value}'.
            """
        }
        return prompt_templates.get(language, prompt_templates["en"]).strip()

    def generate_escalation_prompt(self, context: ConversationContext) -> str:
        """
        Generates a prompt to determine if escalation to a human is needed.
        This logic could also be implemented directly in the main application logic using context fields.
        """
        # A more sophisticated system might use ML, but here's a rule-based prompt for an LLM classifier.
        # Often, the decision is made programmatically based on context.sentiment, context.urgency, etc.
        # This prompt is illustrative if a complex LLM analysis was desired.
        history_summary = self._summarize_conversation_history(context.conversation_history)
        prompt = f"""
        Based on the conversation history and current state, should this conversation be escalated to a human agent?

        **Current State:**
        - Sentiment: {context.sentiment.value}
        - Urgency: {context.urgency.value}
        - Intent: {context.intent.value}
        - User Profile: {json.dumps(context.user_profile)}

        **Conversation History:**
        {history_summary}

        **Escalation Rules:**
        - Escalate if sentiment is '{Sentiment.VERY_NEGATIVE.value}'.
        - Escalate if urgency is '{Urgency.CRITICAL.value}'.
        - Escalate if intent is '{Intent.COMPLAINT.value}' and sentiment is '{Sentiment.NEGATIVE.value}' or worse.
        - Escalate if user explicitly requests human help.

        Respond with only: 'ESCALATE' or 'CONTINUE'.
        """
        logger.debug(f"Generated escalation prompt for session {context.session_id}")
        return prompt.strip()

    def get_fallback_response(self, language: str = "en", error_type: str = "general", context: Optional[ConversationContext] = None) -> str:
        """
        Provides intelligent fallback responses based on context and error type.
        """
        fallbacks = {
            "en": {
                "general": "I'm currently processing your request. Could you please rephrase your question or try again?",
                "no_context": f"I don't have specific information on that topic in my knowledge base. Please check the {self.college_name} website or contact our support team at support@your_college_domain.edu for detailed assistance.",
                "rate_limit": "You've reached the message limit for this session. Please wait a moment before sending another message.",
                "error": "An unexpected error occurred on my end. My team has been notified. Please try again shortly. If the problem persists, contact support.",
                "escalation_triggered": f"Your concern seems important. I'm connecting you to a human advisor. In the meantime, you can reach Student Support at support@your_college_domain.edu or call +1-xxx-xxx-xxxx."
            }
        }
        # Potentially adapt fallback based on context.sentiment or context.intent
        if error_type == "escalation_triggered" and context:
             logger.info(f"Escalation triggered for session {context.session_id} (Intent: {context.intent.value}, Sentiment: {context.sentiment.value}). Providing escalation fallback.")
        return fallbacks.get(language, fallbacks["en"]).get(error_type, fallbacks["en"]["general"])

# Example usage (if run as main):
# if __name__ == "__main__":
#     pe = PromptEngine(college_name="InnovateU", knowledge_base_metadata={"last_updated": "2024-01-01"})
#     context_obj = ConversationContext(
#         user_id="user123",
#         session_id="sess456",
#         conversation_history=[{"message": "Hi", "response": "Hello!"}],
#         retrieved_context="Tuition fees are $20,000 per year.",
#         user_profile={"role": "prospect", "year": "freshman"},
#         intent=Intent.FEES,
#         sentiment=Sentiment.NEUTRAL,
#         urgency=Urgency.LOW,
#         timestamp=datetime.now(timezone.utc),
#         language_code="en"
#     )
#     sys_prompt = pe.generate_system_prompt(context_obj)
#     print("Generated System Prompt:\n", sys_prompt)