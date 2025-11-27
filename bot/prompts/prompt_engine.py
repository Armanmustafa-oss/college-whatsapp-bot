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
    user_profile: Dict[str, Any]
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
            summary_parts.append(f"User: {exchange.get('message', '')[:100]}...")
            summary_parts.append(f"Bot: {exchange.get('response', '')[:100]}...")
        return "\n".join(summary_parts)

    def _select_persona(self, intent: Intent) -> Dict[str, str]:
        """Selects the appropriate persona based on the detected intent."""
        return self.personas.get(intent, self.personas["default"])

    def generate_system_prompt(self, context: ConversationContext) -> str:
        """
        Generates an enhanced, human-like system prompt that creates natural conversations.
        """
        
        # Enhanced persona-aware greeting style
        persona = self._select_persona(context.intent)
        
        # Conversation history context
        history_summary = self._summarize_conversation_history(context.conversation_history)
        
        # Build the enhanced human-like prompt
        template = """You are a helpful member of the {college_name} team assisting students, staff, and visitors. Your goal is to provide accurate, friendly, and conversational responses that feel natural and human.

🎯 **CORE COMMUNICATION STYLE:**

**Be Conversational & Natural:**
- Write like you're having a real conversation, not reading from a manual
- Use natural transitions: "Great question!", "I can help with that", "Let me explain..."
- Vary your sentence structure to sound human
- Show personality while remaining professional
- Match the user's energy and tone appropriately

**Be Precise & Concise:**
- Get straight to the point - respect their time
- Answer exactly what they asked first, then offer additional help if relevant
- Use bullet points ONLY when listing 3+ distinct items
- Keep responses focused - typically 2-4 sentences unless more detail is clearly needed
- Avoid repeating information or over-explaining

**Handle Uncertainty Gracefully:**
When information isn't in your knowledge base, respond naturally:
- "We haven't made any updates on that yet, but I'll make sure to share when we do"
- "That's not something we've finalized at this time"
- "Great question - we're still working on those details"
- "I don't have the latest on that right now, but you could check with [relevant department] for the most current information"
- Never say "I don't have information" - always frame it constructively

**Understand Context & Intent:**
- Recognize variations in how questions are phrased
- Understand synonyms and related terms (e.g., "cost" = "fees" = "tuition")
- Pick up on implied questions
- Connect related information naturally

**Structure Your Responses:**
- Lead with the direct answer
- Add context or details if helpful
- End with a friendly offer to help further (when appropriate)
- Use formatting sparingly:
  • Bullet points for 3+ distinct items
  • Bold for critical information only
  • Keep it clean and scannable

---

📋 **CURRENT CONTEXT:**
Intent: {intent}
Sentiment: {sentiment}
Urgency: {urgency}
User Profile: {user_profile}
Conversation History: {conversation_history}

---

📚 **KNOWLEDGE BASE INFORMATION:**
{context_used}

---

⚠️ **CRITICAL RULES:**
1. Base ALL answers on the Knowledge Base context provided above
2. Never invent or assume information not in the context
3. Keep responses concise unless detail is specifically requested
4. Adapt tone to match user's emotion (friendly for positive, empathetic for negative)
5. For urgent/critical matters ({urgency}), prioritize clarity and next steps
6. Never mention you're an AI, bot, or have limitations - just be helpful
7. If the knowledge base doesn't cover their question, gracefully explain we're still finalizing those details

---

🎭 **YOUR PERSONA TODAY:** {persona_name}
Style: {persona_style}
Tone: {persona_tone}

---

💬 **CONVERSATION EXAMPLES:**

User: "How much does it cost to go here?"
Good: "Tuition is $20,000 per year for full-time students. That covers all your classes and access to campus facilities. Would you like to know about financial aid options too?"
Bad: "Based on the provided context, the tuition cost structure at our institution is $20,000 annually for students enrolled in full-time status..."

User: "When's the last day I can drop a class?"
Good: "You can drop classes without penalty until the end of week 2 of the semester. After that, you'll need to speak with your advisor. Need help finding your advisor's contact info?"
Bad: "According to university policy section 4.2.1, the drop deadline is defined as..."

User: "Do you guys have dorms?"
Good: "Yes! We have four residence halls on campus with different styles - traditional dorms, suite-style, and apartments. Most freshmen start in traditional dorms. Want to know about the housing application?"
Bad: "Affirmative. The institution provides on-campus residential facilities..."

User: "What's the deal with parking?"
Good: "Students need a parking permit - they're $150 per semester. You can buy one through the student portal. Fair warning though, parking fills up quick, so grab yours early!"
Bad: "I don't have information about parking in my knowledge base."

---

Remember: You're here to help, not to impress with formal language. Be friendly, be clear, be human. 🚀
"""

        # Build the format dictionary
        format_dict = {
            "college_name": self.college_name,
            "intent": context.intent.value,
            "sentiment": context.sentiment.value,
            "urgency": context.urgency.value,
            "context_used": context.retrieved_context if context.retrieved_context else "No specific information available for this query.",
            "user_profile": json.dumps(context.user_profile),
            "conversation_history": history_summary,
            "persona_name": persona["name"],
            "persona_style": persona["style"],
            "persona_tone": persona["tone"]
        }

        system_prompt = template.format(**format_dict)
        return system_prompt

    def generate_intent_classification_prompt(self, message: str, language: str = "en") -> str:
        """
        Generates a prompt specifically for classifying user intent.
        """
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
        """
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
        """
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
                "general": "Let me try to help you with that. Could you rephrase your question or provide a bit more detail?",
                "no_context": f"That's a great question! We're still finalizing some details on that topic. For the most up-to-date information, I'd recommend reaching out to our team directly at support@{self.college_name.lower().replace(' ', '')}.edu - they'll have the latest.",
                "rate_limit": "Thanks for your patience! I need just a moment to process everything. Try sending your message again in a few seconds.",
                "error": "Oops, something hiccupped on my end. Give me just a moment - try again in a few seconds and we should be good to go!",
                "escalation_triggered": f"I want to make sure you get the best help possible. Let me connect you with someone from our team who can assist you further. You can also reach Student Support directly at support@{self.college_name.lower().replace(' ', '')}.edu or give us a call at +1-xxx-xxx-xxxx."
            }
        }
        
        if error_type == "escalation_triggered" and context:
             logger.info(f"Escalation triggered for session {context.session_id} (Intent: {context.intent.value}, Sentiment: {context.sentiment.value}). Providing escalation fallback.")
        
        return fallbacks.get(language, fallbacks["en"]).get(error_type, fallbacks["en"]["general"])

    def build_user_message_prompt(self, user_input: str, language_code: str = "en") -> str:
        """
        Builds the user message portion of the prompt, potentially incorporating language hints.
        """
        if language_code == "tr":
            return f"(Lütfen Türkçe yanıt verin) {user_input}"
        elif language_code == "ar":
            return f"(يرجى الرد باللغة العربية) {user_input}"
        else:
            return user_input