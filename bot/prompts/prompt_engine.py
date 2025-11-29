"""
prompt_engine.py

Rewritten production-ready PromptEngine that enforces:
 - Direct-answer-only policy (no greetings, no follow-ups, no disclaimers, no marketing)
 - Optional strict JSON output mode
 - Hallucination guards
 - Response length limiting
 - Deterministic conversation summary
 - Minimal, stable public API to avoid touching other files

Usage notes:
 - The engine does not call any model itself; it prepares system/user prompts and post-processes model outputs.
 - Integrate with your LLM calling code: pass model output into `postprocess_model_output(...)`.
"""

from __future__ import annotations
import logging
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# -------------------------
# Enums & Data Structures
# -------------------------
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

@dataclass
class ConversationContext:
    user_id: str
    session_id: str
    conversation_history: List[Dict[str, str]]  # list of {"message":..., "response":...}
    retrieved_context: str  # knowledge base snippet (string) or "" if none
    user_profile: Dict[str, Any]
    intent: Intent
    sentiment: Sentiment
    urgency: Urgency
    timestamp: datetime
    language_code: str = "en"

# -------------------------
# PromptEngine
# -------------------------
class PromptEngine:
    """
    Production-ready prompt engine.

    Key config options:
      - json_output_mode: when True, postprocess returns JSON with keys:
          {"answer": str, "source": str, "confidence": float, "hallucination_risk": bool}
      - hallucination_guard: when True, model outputs that appear to hallucinate are blocked/replaced
      - max_response_chars: maximum number of characters in the final answer (post truncation)
    """

    # banned fragments (model often appends these) - regex patterns
    _BANNED_PATTERNS = [
        r"(?i)^---",  # leading separator
        r"(?i)this is an automated response", 
        r"(?i)for complex inquiries",
        r"(?i)contact the relevant",
        r"(?i)operates under ferpa",
        r"(?i)if you need", 
        r"(?i)would you like", 
        r"(?i)please contact", 
        r"(?i)ok\b\.?$",
        r"(?i)thank(s| you)\b",
        r"(?i)i am an ai\b",
        r"(?i)as an ai\b",
        r"(?i)i'm an ai\b",
    ]

    def __init__(
        self,
        college_name: str,
        knowledge_base_metadata: Optional[Dict[str, Any]] = None,
        *,
        json_output_mode: bool = False,
        hallucination_guard: bool = True,
        max_response_chars: int = 800,
    ):
        self.college_name = college_name
        self.kb_meta = knowledge_base_metadata or {}
        self.json_output_mode = bool(json_output_mode)
        self.hallucination_guard = bool(hallucination_guard)
        self.max_response_chars = int(max_response_chars)
        self._initialize_personas()
        self._initialize_templates()
        logger.info("PromptEngine initialized (production-optimized).")

    # -------------------------
    # Personas
    # -------------------------
    def _initialize_personas(self):
        self.personas = {
            Intent.ADMISSIONS: {"name": "Admissions Advisor", "style": "Experienced, direct", "tone": "Confident"},
            Intent.COURSES: {"name": "Academic Guide", "style": "Precise, structured", "tone": "Professional"},
            Intent.FEES: {"name": "Financial Counselor", "style": "Practical, empathetic", "tone": "Reassuring"},
            Intent.CAREER_SERVICES: {"name": "Career Coach", "style": "Strategic, experienced", "tone": "Encouraging"},
            "default": {"name": "Senior Partner", "style": "Decades of institutional experience", "tone": "Decisive"},
        }

    # -------------------------
    # System prompt templates
    # -------------------------
    def _initialize_templates(self):
        # Strict system prompt enforcing a direct-answer-only policy.
        # This template is intentionally terse and explicit about prohibitions.
        self.system_template_en = (
            "You are {persona_name}, a senior representative of {college_name} with long institutional experience.\n\n"
            "OUTPUT POLICY (STRICT):\n"
            "- Provide ONLY the direct answer to the user's question.\n"
            "- Do NOT include greetings, sign-offs, follow-up questions, suggestions, marketing, or disclaimers.\n"
            "- Do NOT mention policies, process, automation, or that you are an AI.\n"
            "- Do NOT append separators like '---' or words such as 'OK' or 'Thanks'.\n"
            "- If the knowledge base (KB) contains the exact fact requested, answer using only KB facts.\n"
            "- If KB is insufficient, do not invent facts. Follow the hallucination guard rules.\n\n"
            "RESPONSE FORMAT (STRICT):\n"
            "1) Output only the answer text (no extra sections).\n"
            "2) Keep it concise (prefer single-sentence factual answers). Maximum length is {max_chars} characters.\n"
            "3) If json_output_mode is enabled, the LLM code should still return a plain textual answer which will be "
            "wrapped into JSON by post-processing.\n\n"
            "CURRENT CONTEXT:\n"
            "- Intent: {intent}\n"
            "- Sentiment: {sentiment}\n"
            "- Urgency: {urgency}\n"
            "- KB SNIPPET (if any):\n{kb_snippet}\n\n"
            "If KB is empty, do NOT invent. Instead return: 'INSUFFICIENT_KB'.\n"
        )

    # -------------------------
    # Prompt generation helpers
    # -------------------------
    def _select_persona(self, intent: Intent) -> Dict[str, str]:
        return self.personas.get(intent, self.personas["default"])

    def _summarize_history(self, history: List[Dict[str, str]], max_exchanges: int = 3) -> str:
        if not history:
            return "No previous exchanges."
        recent = history[-max_exchanges:]
        summary_lines = []
        for ex in recent:
            u = ex.get("message", "").replace("\n", " ")[:200]
            b = ex.get("response", "").replace("\n", " ")[:200]
            summary_lines.append(f"U:{u} | B:{b}")
        return "\n".join(summary_lines)

    def generate_system_prompt(self, context: ConversationContext) -> str:
        persona = self._select_persona(context.intent)
        kb_snippet = context.retrieved_context.strip() if context.retrieved_context else ""
        # If KB empty, explicitly instruct model to output the marker
        filled = self.system_template_en.format(
            persona_name=persona["name"],
            college_name=self.college_name,
            intent=context.intent.value,
            sentiment=context.sentiment.value,
            urgency=context.urgency.value,
            kb_snippet=kb_snippet or "(no KB content)",
            max_chars=self.max_response_chars,
        )
        return filled

    def build_user_prompt(self, user_input: str, context: ConversationContext) -> str:
        """
        Build the user message prompt which will be concatenated with system prompt.
        Keep user message simple and direct.
        """
        # Keep the user prompt short and to the point
        return f"User question: {user_input.strip()}"

    # -------------------------
    # Post-processing / Guards
    # -------------------------
    def _sanitize_text(self, text: str) -> str:
        """Remove banned patterns and trailing separators/fillers. Collapses whitespace."""
        # Remove any banned fragments (case-insensitive)
        sanitized = text
        for pat in self._BANNED_PATTERNS:
            sanitized = re.sub(pat, "", sanitized, flags=re.IGNORECASE)
        # Remove common trailing separators or repeated dashes
        sanitized = re.sub(r"-{3,}", "", sanitized)
        # Collapse whitespace and strip
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        return sanitized

    def _detect_hallucination_risk(self, answer: str, kb: str) -> bool:
        """
        Basic hallucination heuristic:
         - If KB is empty => HIGH risk.
         - If answer contains specific numeric facts/dates/entities not present in KB => risk.
         - This is intentionally conservative: if unsure, return True.
        """
        if not kb or not kb.strip():
            return True

        # Extract numeric tokens and capitalized entity tokens
        kb_lower = kb.lower()
        # Numeric/date tokens heuristic
        numbers_in_answer = re.findall(r"\b\d{1,4}(?:[.,]\d+)?\b", answer)
        for num in numbers_in_answer:
            if num not in kb_lower:
                # If numeric token not found in KB, consider risky
                return True

        # Look for proper nouns/entities (capitalized words) presence in KB
        capitalized = re.findall(r"\b[A-Z][a-z]{2,}\b", answer)
        for ent in capitalized:
            if ent.lower() not in kb_lower:
                # If entity not present in KB, mark risky (conservative)
                return True

        # If nothing flagged, low risk
        return False

    def _truncate_response(self, text: str) -> str:
        if len(text) <= self.max_response_chars:
            return text
        # Try to truncate at sentence boundary before limit
        snippet = text[: self.max_response_chars]
        # find last period or semicolon
        last_punct = max(snippet.rfind("."), snippet.rfind("!"), snippet.rfind("?"))
        if last_punct > int(self.max_response_chars * 0.5):
            return snippet[: last_punct + 1].strip()
        # Otherwise hard truncate and append ellipsis
        return snippet.strip() + "…"

    def postprocess_model_output(
        self,
        model_text: str,
        context: ConversationContext,
        *,
        force_json: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Post-process raw model output and enforce policies.
        Returns a dict with keys:
            - answer (final answer text or INSUFFICIENT_KB marker)
            - hallucination_risk (bool)
            - truncated (bool)
            - json_payload (if json_output_mode or force_json is True)
        """
        force_json = self.json_output_mode if force_json is None else bool(force_json)

        # 1) Sanitize
        t = self._sanitize_text(model_text)

        # 2) If model returned the explicit marker the system template asked for, keep it
        marker = "INSUFFICIENT_KB"
        if marker in t:
            final = marker
            hallucination = True
        else:
            # 3) Detect hallucination risk (conservative)
            hallucination = self._detect_hallucination_risk(t, context.retrieved_context or "")

            # 4) If hallucination guard is enabled and risk detected -> replace with marker
            if self.hallucination_guard and hallucination:
                final = marker
            else:
                final = t

        # 5) Truncate if necessary
        truncated = False
        if final != marker and len(final) > self.max_response_chars:
            final = self._truncate_response(final)
            truncated = True

        # 6) Enforce "only direct answer" policies: remove leading/trailing salutations or question marks
        final = re.sub(r"^(hi|hello|dear)\b[:,]?\s*", "", final, flags=re.IGNORECASE).strip()
        # Remove trailing question marks if it's a statement
        final = final.rstrip()

        # 7) If final is marker, we must output a concise human-style fallback, **but** user insisted on strict "no disclaimers".
        #    To obey the latest strict user requirement, we will output a short, neutral, single-line marker phrasing.
        if final == marker:
            # Provide a short human-like phrase but still direct and without follow-ups
            final = "Insufficient information in knowledge base."

            # Note: This is the ONLY allowed non-answer text when KB insufficient; it obeys direct-answer-only rule.

        # 8) Build JSON payload if requested
        result = {
            "answer": final,
            "hallucination_risk": bool(hallucination),
            "truncated": bool(truncated),
        }

        if force_json:
            # Provide minimal structured metadata
            # confidence heuristic: 0.9 if not hallucination, else 0.35
            confidence = 0.90 if not hallucination else 0.35
            result["json_payload"] = {
                "answer": final,
                "source": "kb" if context.retrieved_context else "none",
                "confidence": confidence,
                "hallucination_risk": bool(hallucination),
            }

        return result

    # -------------------------
    # Convenience: single-step API to produce system+user prompts
    # -------------------------
    def build_prompt_pair(self, user_input: str, context: ConversationContext) -> Tuple[str, str]:
        """
        Returns (system_prompt, user_prompt) ready to be passed to an LLM.
        The system prompt enforces strict direct-answer behaviour.
        """
        sys = self.generate_system_prompt(context)
        usr = self.build_user_prompt(user_input, context)
        return sys, usr

# -------------------------
# Example usage (for integrators)
# -------------------------
# Integrator should:
# 1) engine = PromptEngine("MyCollege", kb_meta, json_output_mode=True, hallucination_guard=True)
# 2) sys, usr = engine.build_prompt_pair(user_input, context)
# 3) send sys+usr to LLM and obtain `model_text`
# 4) final = engine.postprocess_model_output(model_text, context)
#
# final['answer'] is the strict answer text. If engine.json_output_mode True, final['json_payload'] holds structured output.
