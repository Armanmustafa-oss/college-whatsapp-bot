# app/services/ai_service.py
import sentry_sdk  # Add this import at top

import os
import time
from groq import Groq
from app.prompts import PromptEngine
from app.response_quality import ResponseEnhancer
from app.services.rag_service import rag_service
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.prompt_engine = PromptEngine()
        self.enhancer = ResponseEnhancer()

    def detect_language(self, text: str) -> str:
        text_lower = text.lower()
        if any(word in text_lower for word in ["merhaba", "nasıl", "teşekkür"]):
            return "tr"
        elif any(char in text for char in ["مرحبا", "كيف", "شكرا"]):
            return "ar"
        return "en"

    def _calculate_quality_score(self, response: str, had_fallback: bool, documents_retrieved: int) -> float:
        """Calculate quality score 0.0-1.0"""
        if had_fallback:
            return 0.3
        if documents_retrieved == 0:
            return 0.4
        if len(response) > 50:
            return 0.9
        elif len(response) > 20:
            return 0.7
        else:
            return 0.5

    def _calculate_confidence(self, documents: list) -> float:
        """Calculate confidence based on document relevance"""
        if not documents:
            return 0.0
        distances = [doc.get("distance", 1.0) for doc in documents]
        avg_distance = sum(distances) / len(distances)
        return max(0.0, min(1.0, 1.0 - avg_distance))

    def generate_response(self, user_message: str, user_phone: str):
        start_time = time.time()
        
        # Detect language
        lang = self.detect_language(user_message)
        
        # Get relevant docs
        results = rag_service.search_documents(user_message, n_results=3)
        documents_retrieved = len(results)
        context = "\n".join([doc["content"] for doc in results]) if results else "No relevant information found."
        
        # Check for fallback
        had_fallback = "don't know" in context.lower() or "I don't have" in context
        
        # Get professional prompts
        system_prompt = self.prompt_engine.get_system_prompt(lang, context)
        user_prompt = self.prompt_engine.format_user_message(user_message, lang)
        
        # Generate response
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama3-8b-8192",
            temperature=0.3,
            max_tokens=500
        )
        
        raw_response = chat_completion.choices[0].message.content
        enhanced_response = self.enhancer.enhance_response(user_message, raw_response, lang)
        duration = time.time() - start_time
        
        # Calculate metrics
        quality_score = self._calculate_quality_score(enhanced_response, had_fallback, documents_retrieved)
        confidence_score = self._calculate_confidence(results)
        response_time_ms = int(duration * 1000)
        
        return {
            "message": enhanced_response,
            "language": lang,
            "confidence": confidence_score,
            "quality_score": quality_score,
            "had_fallback": had_fallback,
            "documents_retrieved": documents_retrieved,
            "response_time_ms": response_time_ms,
            "sources": [doc.get("metadata", {}).get("title", "Unknown") for doc in results] if results else []
        }

# Global instance
ai_service = AIService()