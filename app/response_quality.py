# app/response_quality.py
import re
from typing import List
from dataclasses import dataclass

@dataclass
class ResponseQuality:
    confidence_score: float
    has_question_repetition: bool
    exposes_internals: bool
    suggestions: List[str]

class ResponseEnhancer:
    def __init__(self):
        self.internal_phrases = [
            "the provided context", "the document says", "based on the context",
            "according to my knowledge base", "the information provided",
            "in the documents", "the context mentions"
        ]
    
    def enhance_response(self, question: str, response: str, language: str) -> str:
        enhanced = response
        
        # Fix 1: Remove question repetition
        enhanced = self._remove_question_repetition(question, enhanced, language)
        
        # Fix 2: Remove internal system references
        enhanced = self._remove_internal_references(enhanced)
        
        # Fix 3: Improve fallback messages
        enhanced = self._improve_fallback_messages(enhanced, language)
        
        return enhanced.strip()
    
    def _remove_question_repetition(self, question: str, response: str, language: str) -> str:
        # Remove patterns like "Question? Answer: ..."
        pattern1 = re.compile(rf"^.*{re.escape(question[:30])}.*?[:?]\s*", re.IGNORECASE)
        response = pattern1.sub('', response)
        
        # Language-specific cleanup
        if language == 'tr':
            response = re.sub(r'^.*\?\s*(Evet|Hayır|Cevap)', r'\1', response, flags=re.IGNORECASE)
        elif language == 'ar':
            response = re.sub(r'^.*؟\s*(نعم|لا|الجواب)', r'\1', response)
        
        return response
    
    def _remove_internal_references(self, response: str) -> str:
        replacements = {
            "the provided context": "our information",
            "the document says": "according to our records",
            "based on the context": "",
            "according to my knowledge base": "based on our information",
            "the information provided": "our records show",
            "in the documents": "according to our records",
            "the context mentions": "we have information that"
        }
        
        result = response
        for old, new in replacements.items():
            result = re.sub(re.escape(old), new, result, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', result).strip()
    
    def _improve_fallback_messages(self, response: str, language: str) -> str:
        dont_know_phrases = {
            'en': ["i don't have", "i don't know", "i cannot find"],
            'tr': ["bilgim yok", "bilmiyorum", "bulamıyorum"],
            'ar': ["لا أعرف", "ليس لدي", "لا أستطيع"]
        }
        
        response_lower = response.lower()
        phrases = dont_know_phrases.get(language, dont_know_phrases['en'])
        
        if any(phrase in response_lower for phrase in phrases):
            if not any(word in response_lower for word in ['email', 'office', 'contact', '@']):
                enhancements = {
                    'en': "\n\nFor personalized assistance, please contact Student Services at info@university.edu or visit the campus office.",
                    'tr': "\n\nKişisel yardım için lütfen Öğrenci İşleri ile info@university.edu adresinden iletişime geçin veya kampüs ofisini ziyaret edin.",
                    'ar': "\n\nللحصول على مساعدة شخصية، يرجى الاتصال بخدمات الطلاب على info@university.edu أو زيارة مكتب الحرم الجامعي."
                }
                response += enhancements.get(language, enhancements['en'])
        
        return response