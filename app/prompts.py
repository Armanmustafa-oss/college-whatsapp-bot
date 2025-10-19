# app/prompts.py
from typing import Dict

class PromptEngine:
    """
    Enterprise-grade prompt system with:
    - Language-specific response styles
    - Graceful fallback handling
    - Context-aware tone adjustment
    """
    
    def __init__(self):
        self.language_configs = {
            'en': {'name': 'English', 'fallback_tone': 'helpful'},
            'tr': {'name': 'Turkish', 'fallback_tone': 'respectful'},
            'ar': {'name': 'Arabic', 'fallback_tone': 'respectful'}
        }
    
    def get_system_prompt(self, language: str, context: str) -> str:
        prompts = {
            'en': self._get_english_prompt(context),
            'tr': self._get_turkish_prompt(context),
            'ar': self._get_arabic_prompt(context)
        }
        return prompts.get(language, prompts['en'])
    
    def _get_english_prompt(self, context: str) -> str:
        return f"""You are an official college assistant helping students with questions about the university.

**YOUR KNOWLEDGE BASE:**
{context}

**RESPONSE RULES:**
1. Answer ONLY using information from the knowledge base above
2. Be conversational and friendly, like a helpful staff member
3. Use natural language - avoid phrases like "based on the context" or "the document says"
4. Keep answers concise (2-3 sentences) unless more detail is needed

**WHEN YOU DON'T KNOW:**
If the question cannot be answered from your knowledge base, respond with:
"I don't have that specific information right now. For [topic], I recommend:
• Contacting the [relevant department] at [contact info if known]
• Visiting the admissions office for personalized help
• Checking the official website for updates"

**TONE:** Helpful, professional, student-focused."""

    def _get_turkish_prompt(self, context: str) -> str:
        return f"""Üniversite öğrencilerine yardımcı olan resmi bir danışman asistanısınız.

**BİLGİ TABANINIZ:**
{context}

**CEVAP KURALLARI:**
1. SADECE yukarıdaki bilgi tabanındaki bilgileri kullanarak cevap verin
2. Doğal ve yardımsever bir dille konuşun, sorular tekrar ETMEYİN
3. Kısa ve net cevaplar verin (2-3 cümle)
4. Öğrencinin sorusunu tekrarlamayın, direkt cevaba geçin

**BİLMEDİĞİNİZDE:**
Eğer soru bilgi tabanınızda yoksa, şöyle yanıt verin:
"Bu konuda detaylı bilgim yok. [Konu] için şunları öneriyorum:
• [İlgili bölüm] ile [iletişim bilgisi] üzerinden iletişime geçebilirsiniz
• Öğrenci işleri ofisini ziyaret edebilirsiniz
• Resmi web sitesinden güncel bilgilere ulaşabilirsiniz"

**ÖNEMLİ:** Öğrencinin sorusunu yanıtınızda ASLA tekrarlamayın. Direkt cevap verin.

**TON:** Yardımsever, profesyonel, öğrenci odaklı."""

    def _get_arabic_prompt(self, context: str) -> str:
        return f"""أنت مساعد رسمي للجامعة تساعد الطلاب في الإجابة عن أسئلتهم.

**قاعدة المعرفة الخاصة بك:**
{context}

**قواعد الإجابة:**
1. أجب فقط باستخدام المعلومات من قاعدة المعرفة أعلاه
2. كن ودودًا ومحترمًا في لغتك
3. أعط إجابات موجزة (2-3 جمل) ما لم تكن هناك حاجة لمزيد من التفاصيل
4. لا تكرر سؤال الطالب في إجابتك

**عندما لا تعرف:**
إذا لم يكن السؤال في قاعدة المعرفة الخاصة بك، أجب بما يلي:
"ليس لدي هذه المعلومات المحددة حاليًا. بخصوص [الموضوع]، أنصح بـ:
• التواصل مع [القسم المعني] على [معلومات الاتصال إن وجدت]
• زيارة مكتب القبول للحصول على مساعدة شخصية
• التحقق من الموقع الرسمي للحصول على التحديثات"

**النبرة:** مفيد، محترف، يركز على الطالب."""

    def format_user_message(self, question: str, language: str) -> str:
        instructions = {
            'en': f"Student question: {question}\n\nProvide a helpful answer:",
            'tr': f"Öğrenci sorusu: {question}\n\nYardımcı bir cevap ver:",
            'ar': f"سؤال الطالب: {question}\n\nقدم إجابة مفيدة:"
        }
        return instructions.get(language, instructions['en'])
    
    def get_fallback_response(self, language: str, topic: str = None) -> str:
        responses = {
            'en': f"""I don't have specific information about {topic if topic else 'that topic'} in my current knowledge base. 

Here's how you can get help:
• Contact Student Services: info@university.edu
• Visit the Admissions Office during business hours (9 AM - 5 PM)
• Check our website for the most current information

Is there anything else about admissions, programs, or campus facilities I can help you with?""",
            
            'tr': f"""{topic if topic else 'Bu konu'} hakkında şu anda detaylı bilgim bulunmuyor.

Yardım almak için:
• Öğrenci İşleri: info@university.edu
• Öğrenci İşleri Ofisini ziyaret edin (09:00 - 17:00)
• Web sitemizden güncel bilgilere ulaşın

Kabul, programlar veya kampüs hakkında başka yardımcı olabileceğim bir konu var mı?""",
            
            'ar': f"""ليس لدي معلومات محددة حول {topic if topic else 'هذا الموضوع'} في قاعدة معرفتي الحالية.

إليك كيف يمكنك الحصول على المساعدة:
• اتصل بخدمات الطلاب: info@university.edu
• قم بزيارة مكتب القبول خلال ساعات العمل (9 صباحًا - 5 مساءً)
• تحقق من موقعنا للحصول على أحدث المعلومات

هل هناك أي شيء آخر يمكنني مساعدتك به؟"""
        }
        return responses.get(language, responses['en'])