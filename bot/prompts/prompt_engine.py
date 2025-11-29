"""
🤖 Advanced AI Prompt Orchestration Engine (Humanized, Senior Partner Version)
============================================================================
Rewritten to provide professional, human-like, problem-solving responses.
The bot behaves like a senior institute partner with 50+ years experience.
Fallbacks and prompts are natural, authoritative, and actionable.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

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
    user_profile: Dict[str, Any]
    intent: Intent
    sentiment: Sentiment
    urgency: Urgency
    timestamp: datetime
    language_code: str

# --- Main Prompt Engine Class ---
class PromptEngine:
    """
    Orchestrates prompt generation using advanced context,
    intent analysis, sentiment scoring, and dynamic persona adaptation.
    """

    def __init__(self, college_name: str, knowledge_base_metadata: Dict[str, Any]):
        self.college_name = college_name
        self.knowledge_base_metadata = knowledge_base_metadata
        self._initialize_personas()
        self._initialize_prompts()
        logger.info(f"PromptEngine initialized for '{college_name}' with senior-partner persona.")

    def _initialize_personas(self):
        """Defines AI personas."""
        self.personas = {
            Intent.ADMISSIONS: {
                "name": "Admissions Advisor",
                "style": "Experienced, welcoming, persuasive. Offers clear guidance and pathways.",
                "tone": "Confident, approachable"
            },
            Intent.COURSES: {
                "name": "Academic Guide",
                "style": "Authoritative, structured, precise. Explains prerequisites and outcomes clearly.",
                "tone": "Professional, insightful"
            },
            Intent.FEES: {
                "name": "Financial Counselor",
                "style": "Clear, empathetic, practical. Addresses concerns confidently.",
                "tone": "Supportive, reassuring"
            },
            Intent.CAREER_SERVICES: {
                "name": "Career Coach",
                "style": "Motivational, strategic, experience-driven. Connects academics to careers naturally.",
                "tone": "Encouraging, solution-oriented"
            },
            "default": {
                "name": "Senior Assistant",
                "style": "Knowledgeable, decisive, professional. Resolves queries efficiently.",
                "tone": "Calm, confident"
            }
        }

    def _initialize_prompts(self):
        """Initializes system prompt templates."""
        self.system_prompt_templates = {
            "en": """
You are {persona_name}, a senior official AI representative for {college_name} with decades of experience managing student and institutional matters.

CORE PRINCIPLES:
- Always provide practical, actionable, and professional answers.
- Avoid repeating "I don't know" or default disclaimers.
- Even when the knowledge base is incomplete, offer useful context, approximate guidance, or practical next steps.
- No follow-ups, no suggestions, no filler phrases. Answer directly, confidently, and clearly.
- Adapt tone to sentiment and urgency.
- Maintain authority and professionalism; your responses reflect 50+ years experience.

CURRENT CONTEXT:
- User Profile: {user_profile}
- Intent: {detected_intent}
- Sentiment: {detected_sentiment}
- Urgency: {detected_urgency}
- Session ID: {session_id}
- Current Time: {current_time} (UTC)

KNOWLEDGE BASE CONTEXT:
{retrieved_context}

PREVIOUS CONVERSATION (Last 3 exchanges):
{conversation_summary}

RESPONSE FORMAT RULES:
1. Answer directly, professionally, and concisely.
2. Use one or two sentences if possible; longer only if essential.
3. Provide guidance or context if exact data is missing, phrased naturally (e.g., "Based on prior experience...").
4. Do NOT repeat the question or apologize unnecessarily.
5. Do NOT add automated disclaimers, follow-ups, or "Would you like..." statements.

PERSONA:
- Name: {persona_name}
- Style: {persona_style}
- Tone: {persona_tone}
"""
        }

    def _summarize_conversation_history(self, history: List[Dict[str, str]], max_exchanges: int = 3) -> str:
        if not history:
            return "No previous conversation history in this session."
        recent = history[-max_exchanges:]
        return "\n".join(
            [f"User: {e.get('message', '')[:120]}\nBot: {e.get('response', '')[:120]}" for e in recent]
        )

    def _select_persona(self, intent: Intent) -> Dict[str, str]:
        return self.personas.get(intent, self.personas["default"])

    def generate_system_prompt(self, context: ConversationContext) -> str:
        persona = self._select_persona(context.intent)
        history_summary = self._summarize_conversation_history(context.conversation_history)
        template = self.system_prompt_templates.get("en")
        format_dict = {
            "college_name": self.college_name,
            "detected_intent": context.intent.value,
            "detected_sentiment": context.sentiment.value,
            "detected_urgency": context.urgency.value,
            "retrieved_context": context.retrieved_context if context.retrieved_context else "Based on available information, full details are not present; the following context is provided for guidance.",
            "user_profile": json.dumps(context.user_profile),
            "conversation_summary": history_summary,
            "persona_name": persona["name"],
            "persona_style": persona["style"],
            "persona_tone": persona["tone"],
            "session_id": context.session_id,
            "current_time": datetime.now(timezone.utc).isoformat()
        }
        return template.format(**format_dict)

    def generate_intent_classification_prompt(self, message: str, language: str = "en") -> str:
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
        return f"""
Classify the intent of the following user message into one of these categories:

{intent_list}

Message: "{message}"

Respond with only the category name.
""".strip()

    def generate_sentiment_analysis_prompt(self, message: str, language: str = "en") -> str:
        return f"""
Analyze the sentiment of this message, considering user's emotions like frustration, happiness, urgency, or anxiety.

Message: "{message}"

Respond with only: '{Sentiment.POSITIVE.value}', '{Sentiment.NEUTRAL.value}', '{Sentiment.NEGATIVE.value}', '{Sentiment.VERY_NEGATIVE.value}'.
""".strip()

    def generate_escalation_prompt(self, context: ConversationContext) -> str:
        history_summary = self._summarize_conversation_history(context.conversation_history)
        return f"""
Based on the conversation history and current state, should this conversation be escalated to a human agent?

Current State:
- Sentiment: {context.sentiment.value}
- Urgency: {context.urgency.value}
- Intent: {context.intent.value}
- User Profile: {json.dumps(context.user_profile)}

Conversation History:
{history_summary}

Escalation Rules:
- Escalate if sentiment is '{Sentiment.VERY_NEGATIVE.value}'.
- Escalate if urgency is '{Urgency.CRITICAL.value}'.
- Escalate if intent is '{Intent.COMPLAINT.value}' and sentiment is '{Sentiment.NEGATIVE.value}' or worse.
- Escalate if user explicitly requests human help.

Respond with only: 'ESCALATE' or 'CONTINUE'.
""".strip()

    def get_fallback_response(self, language: str = "en", error_type: str = "general", context: Optional[ConversationContext] = None) -> str:
        fallbacks = {
            "en": {
                "general": "Based on available knowledge, here’s the closest guidance I can provide.",
                "no_context": "Full details are currently unavailable; however, here’s what is known from our resources.",
                "rate_limit": "Processing is taking a moment, please retry shortly.",
                "error": "An unexpected issue occurred, but I can still assist with available information.",
                "escalation_triggered": "I’m connecting you to the right person to provide precise guidance."
            }
        }
        return fallbacks.get(language, fallbacks["en"]).get(error_type, fallbacks["en"]["general"])

    def build_user_message_prompt(self, user_input: str, language_code: str = "en") -> str:
        if language_code == "tr":
            return f"(Respond in Turkish) {user_input}"
        elif language_code == "ar":
            return f"(Respond in Arabic) {user_input}"
        else:
            return user_input
