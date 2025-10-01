import re
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from typing import List, Dict
import logging
from app.config import settings
from services.rag_service import rag_service
from functools import lru_cache
import hashlib
import re
import os
import openai


logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",  # Free, fast, powerful
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.system_prompt = """
You are a helpful college assistant chatbot for international students. You help students with questions about:
- Admissions and application processes
- Immigration and visa requirements  
- Class schedules and academic information
- Housing and accommodation
- Tuition fees and payments
- General college life

Guidelines:
1. Always be friendly, helpful, and encouraging
2. If you don't know something specific, admit it and suggest they contact the college directly
3. Provide accurate information based on the context provided
4. Support multiple languages - if a student asks in another language, respond in that language
5. Keep responses concise but informative
6. If a question is not related to college matters, politely redirect them back to college-related topics

Use the provided context documents to answer questions accurately.
"""
    
    def generate_response(self, user_message: str, user_phone: str) -> Dict[str, any]:
        """
        Generate AI response to user message using RAG
        
        Args:
            user_message: The user's question
            user_phone: User's phone number for logging
            
        Returns:
            Dict with response, confidence, and sources
        """
        try:
            # Step 1: Search for relevant documents
            relevant_docs = rag_service.search_documents(user_message, n_results=3)
            
            # Step 2: Build context from retrieved documents
            context = self._build_context(relevant_docs)
            
            # Step 3: Detect language and generate response
            language = self._detect_language(user_message)
            
            # Step 4: Create prompt with context
            user_prompt = f"""
Context Information:
{context}

User Question: {user_message}

Please answer the user's question based on the context provided. If the context doesn't contain relevant information, say so and suggest they contact the college directly.
"""
            
            # Step 5: Generate response using LangChain
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            return {
                "message": response.content,
                "language": language,
                "confidence": self._calculate_confidence(relevant_docs),
                "sources": [doc.get("metadata", {}).get("title", "Unknown") for doc in relevant_docs]
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return {
                "message": "I'm sorry, I'm having trouble processing your request right now. Please try again later or contact the college directly.",
                "language": "en",
                "confidence": 0.0,
                "sources": []
            }
    
    def _build_context(self, documents: List[Dict]) -> str:
        """Build context string from retrieved documents"""
        if not documents:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        for doc in documents:
            title = doc.get("metadata", {}).get("title", "Unknown Document")
            content = doc.get("content", "")
            context_parts.append(f"Document: {title}\nContent: {content}\n")
        
        return "\n".join(context_parts)
    
    def _detect_language(self, text: str) -> str:
        """
        Simple language detection - can be improved with proper language detection library
        For now, we'll use a basic approach
        """
        # Simple keyword-based detection (you can improve this)
        turkish_keywords = ["merhaba", "nasıl", "nedir", "teşekkürler", "lütfen"]
        arabic_keywords = ["مرحبا", "كيف", "ماذا", "شكرا", "من فضلك"]
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in turkish_keywords):
            return "tr"
        elif any(keyword in text for keyword in arabic_keywords):
            return "ar"
        else:
            return "en"  # Default to English
    
    def _calculate_confidence(self, documents: List[Dict]) -> float:
        """
        Calculate confidence score based on document relevance
        This is a simple implementation - can be improved
        """
        if not documents:
            return 0.0
        
        # Use the average distance/similarity score
        distances = [doc.get("distance", 1.0) for doc in documents]
        avg_distance = sum(distances) / len(distances)
        
        # Convert distance to confidence (lower distance = higher confidence)
        confidence = max(0.0, min(1.0, 1.0 - avg_distance))
        return confidence

# Global instance
ai_service = AIService()

class AIService:
    # ... your existing __init__ and methods ...

    @lru_cache(maxsize=100)
    def _get_cached_response(self, message_hash: str):
        """
        Internal method to cache responses by message hash.
        Returns None if not cached.
        """
        return None  # We'll use this as a cache check

    def generate_response(self, user_message: str, user_phone: str):
        # Sanitize and hash the message for caching
        user_message = self.sanitize_input(user_message)
        clean_message = re.sub(r'[^\w\s\-.,!?]', '', user_message.lower())
        message_hash = hashlib.md5(clean_message.encode()).hexdigest()

        # Try to get from cache
        cached = self._get_cached_response(message_hash)
        if cached:
            return cached

        # Step 1: Search for relevant documents
        relevant_docs = rag_service.search_documents(user_message, n_results=3)

        # Step 2: Build context from retrieved documents
        context = self._build_context(relevant_docs)

        # Step 3: Detect language and generate response
        language = self._detect_language(user_message)

        # Step 4: Create prompt with context
        user_prompt = f"""
Context Information:
{context}

User Question: {user_message}

Please answer the user's question based on the context provided. If the context doesn't contain relevant information, say so and suggest they contact the college directly.
"""

        # Step 5: Generate response using LangChain
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self.llm(messages)

        response_data = {
            "message": response.content,
            "language": language,
            "confidence": self._calculate_confidence(relevant_docs),
            "sources": [doc.get("metadata", {}).get("title", "Unknown") for doc in relevant_docs]
        }

        # Cache the result by overriding the cached method (simulate cache set)
        self._get_cached_response.cache_clear()  # Optional: clear if needed
        return response_data
  
    def sanitize_input(text: str) -> str:
        """Remove potentially harmful characters and limit length."""
        text = re.sub(r'[^\w\s\-.,!?]', '', text)
        return text[:500]  # Prevent abuse via huge inputs
