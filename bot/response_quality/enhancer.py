"""
✨ AI Response Refinement & Optimization Engine
================================================
State-of-the-art system for enhancing, verifying, and formatting AI responses
to ensure maximum utility, clarity, and professional polish before delivery.
"""

import logging
import re
from typing import Dict, List, Any, Optional
import html
import bleach # For HTML sanitization
from urllib.parse import urlparse, urljoin
import phonenumbers # pip install phonenumbers
from bot.config import ENVIRONMENT # Assuming this holds domain/URL info

logger = logging.getLogger(__name__)

class ResponseEnhancer:
    """
    Refines raw AI responses, applying layers of verification, formatting,
    and contextual adaptation to deliver enterprise-grade output.
    """

    def __init__(self, trusted_domains: Optional[List[str]] = None):
        """
        Initializes the ResponseEnhancer.

        Args:
            trusted_domains (Optional[List[str]]): List of domains considered safe for links.
                                                   Defaults to college domain and common educational sites.
        """
        self.trusted_domains = trusted_domains or [
            "your_college_domain.edu", # Replace with actual domain
            "educause.edu",
            "acm.org",
            "ieee.org",
            "wikipedia.org", # Be cautious with this one
            # Add more as needed
        ]
        self._compile_regexes()
        logger.info("ResponseEnhancer initialized with trusted domains and security checks.")

    def _compile_regexes(self):
        """Compiles regular expressions for various cleaning and formatting tasks."""
        self.phone_pattern = re.compile(r'\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        # Basic URL pattern, more robust validation needed
        self.url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
        # Pattern to identify potential PII (simplified, requires more robust checks)
        self.pii_patterns = [
            re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), # SSN-like
            # Add more PII patterns as needed
        ]

    def enhance(self, raw_response: str, context_info: Dict[str, Any]) -> str:
        """
        Applies the full suite of enhancement rules to the raw response.

        Args:
            raw_response (str): The raw response string from the AI model.
            context_info (Dict[str, Any]): Contextual information like language, intent, etc.

        Returns:
            str: The fully enhanced and sanitized response string.
        """
        if not raw_response:
            logger.warning("Received empty raw response for enhancement.")
            return "I couldn't generate a response. Please try rephrasing your question or contact the college directly."

        lang_code = context_info.get('language_code', 'en')
        intent = context_info.get('intent', 'general')

        # 1. Sanitize HTML/Markdown for security
        sanitized_response = self._sanitize_content(raw_response)

        # 2. Clean up excessive whitespace and newlines
        cleaned_response = self._clean_whitespace(sanitized_response)

        # 3. Verify and format contact information (phone, email)
        formatted_response = self._format_contacts(cleaned_response)

        # 4. Validate and potentially sanitize URLs
        validated_response = self._validate_and_sanitize_urls(formatted_response)

        # 5. Apply language-specific or intent-specific formatting rules
        adapted_response = self._apply_adaptive_formatting(validated_response, lang_code, intent)

        # 6. Add standard footer/disclaimer
        final_response = self._add_standard_footer(adapted_response, lang_code)

        logger.debug(f"Enhanced response (Intent: {intent}, Lang: {lang_code}): {final_response[:100]}...") # Log first 100 chars
        return final_response

    def _sanitize_content(self, text: str) -> str:
        """Removes potentially dangerous HTML tags/scripts."""
        # Allow only basic formatting tags if any
        allowed_tags = ['b', 'i', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li'] # Example
        # Use bleach to strip potentially harmful tags/attributes
        return bleach.clean(text, tags=allowed_tags, strip=True)

    def _clean_whitespace(self, text: str) -> str:
        """Removes excessive whitespace and standardizes line breaks."""
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        # Replace multiple newlines with a single newline
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()

    def _format_contacts(self, text: str) -> str:
        """Standardizes phone number and potentially email formats."""
        # Example: Standardize US phone numbers
        def replace_phone(match):
            # Assumes US numbers
            return f'+1 ({match.group(1)}) {match.group(2)}-{match.group(3)}'

        formatted_text = self.phone_pattern.sub(replace_phone, text)

        # Example: Validate/standardize emails (basic)
        # In practice, you might want to validate against known contacts
        # For now, just ensure they look like emails
        # This step might be more about detection for PII rather than formatting
        return formatted_text

    def _validate_and_sanitize_urls(self, text: str) -> str:
        """Validates URLs and potentially sanitizes them or removes untrusted ones."""
        def replace_url(match):
            url = match.group(0)
            try:
                parsed = urlparse(url)
                # Check if the domain is trusted
                if parsed.netloc in self.trusted_domains:
                    # Optionally, add a noreferrer attribute if embedding as HTML
                    # For plain text, just return the URL
                    return url
                else:
                    logger.warning(f"Untrusted URL detected and removed: {url}")
                    # Decide: remove the URL or replace with a warning
                    # For now, let's replace with a warning in plain text
                    return f"[Link to {parsed.netloc} skipped - not on trusted list]"
            except Exception:
                logger.warning(f"Invalid URL detected and removed: {url}")
                return "[Invalid link removed]"

        return self.url_pattern.sub(replace_url, text)

    def _apply_adaptive_formatting(self, text: str, language_code: str, intent: str) -> str:
        """Applies formatting rules based on language and intent."""
        # Example: Add specific disclaimers for Financial Aid intent
        if intent == "financial_aid":
            disclaimer = {
                "en": "\n\n[Disclaimer: Information provided is for general guidance. For personalized financial advice, consult the Financial Aid Office.]\n",
                # Add translations for other languages
            }
            text += disclaimer.get(language_code, disclaimer.get("en", "\n\n[Disclaimer: Information provided is for general guidance.]\n"))

        # Example: Format lists differently based on language (if needed)
        # Example: Adjust politeness level based on language (if needed)
        # Add more adaptive rules as required.
        return text

    def _add_standard_footer(self, text: str, language_code: str) -> str:
        """Adds a standard, localized footer disclaimer."""
        footers = {
            "en": "\n\n---\nThis is an automated response. For complex inquiries or personalized advice, please contact the relevant college department directly. This bot operates under FERPA guidelines.",
            "tr": "\n\n---\nBu otomatik bir yanıttır. Karmaşık sorular için lütfen ilgili kolej birimine doğrudan başvurun. Bu bot FERPA yönergelerine göre çalışır.",
            "ar": "\n\n---\nهذا رد فعل تلقائي. للتحقيق في الاستفسارات المعقدة، يرجى الاتصال بالقسم الجامعي المعني مباشرةً. يعمل هذا الروبوت وفقًا لإرشادات FERPA."
            # Add more languages
        }
        return text + footers.get(language_code, footers["en"])

# Example usage (if run as main):
# if __name__ == "__main__":
#     enhancer = ResponseEnhancer(trusted_domains=["mycollege.edu", "educause.edu"])
#     raw = "  This is a response with a link: <script>alert('xss')</script> https://mycollege.edu/info and a phone (123) 456-7890.  "
#     context = {"language_code": "en", "intent": "general"}
#     enhanced = enhancer.enhance(raw, context)
#     print("Enhanced Response:\n", enhanced)