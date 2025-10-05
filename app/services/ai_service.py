# app/services/ai_service.py
import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from app.services.rag_service import rag_service  # ✅ Also works

class AIService:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )
        # ❌ Remove this line — KnowledgeBase doesn't exist in your blueprint
        # self.kb = KnowledgeBase()

    def detect_language(self, text: str) -> str:
        """Simple language detection"""
        text_lower = text.lower()
        if any(word in text_lower for word in ["merhaba", "nasıl", "teşekkür"]):
            return "tr"
        elif any(char in text for char in ["مرحبا", "كيف", "شكرا"]):  # Arabic chars
            return "ar"
        elif any(word in text_lower for word in ["привет", "как", "спасибо"]):
            return "ru"
        return "en"

    def generate_response(self, user_message: str, user_phone: str):
        # Detect language
        lang = self.detect_language(user_message)
        
        # ✅ Use rag_service (from your blueprint) instead of KnowledgeBase
        results = rag_service.search_documents(user_message, n_results=3)
        
        # Build context from ChromaDB results
        context = "\n".join([doc["content"] for doc in results]) if results else "No relevant information found."

        # Build prompt
        prompt_template = """
You are a helpful college assistant. Answer in the SAME LANGUAGE as the question.
Use ONLY the context below to answer. If context is insufficient, say "I don't know."

Context:
{context}

Question: {question}
Answer:
"""
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        formatted_prompt = prompt.format(context=context, question=user_message)
        
        # Generate response
        response = self.llm.invoke(formatted_prompt)
        
        # Extract sources (from metadata)
        sources = [doc.get("metadata", {}).get("title", "Unknown") for doc in results] if results else []
        
        return {
            "message": response.content,
            "language": lang,
            "sources": sources
        }


# Global instance
ai_service = AIService()