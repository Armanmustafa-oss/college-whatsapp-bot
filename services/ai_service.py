# app/services/ai.py
import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from .knowledge import KnowledgeBase

class AIService:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.kb = KnowledgeBase()

    def detect_language(self, text: str) -> str:
        """Simple language detection"""
        text_lower = text.lower()
        if any(word in text_lower for word in ["merhaba", "nasıl", "teşekkür"]):
            return "tr"
        elif any(word in text_lower for word in ["مرحبا", "كيف", "شكرا"]):
            return "ar"
        elif any(word in text_lower for word in ["привет", "как", "спасибо"]):
            return "ru"
        return "en"

    def generate_response(self, user_message: str, user_phone: str):
        # Detect language
        lang = self.detect_language(user_message)
        
        # Get relevant docs
        results = self.kb.search(user_message)
        context = "\n".join([doc for doc in results["documents"][0]]) if results["documents"][0] else "No relevant information found."
        
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
        
        return {
            "message": response.content,
            "language": lang,
            "sources": [meta["source"] for meta in results["metadatas"][0]] if results["metadatas"][0] else []
        }