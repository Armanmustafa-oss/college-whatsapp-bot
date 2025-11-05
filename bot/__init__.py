"""
College WhatsApp Bot - Enterprise Edition
========================================
Production-grade multilingual AI assistant for college student support.

Version: 2.0.0
License: Proprietary
Compliance: FERPA, GDPR
"""

__version__ = "2.0.0"
__author__ = "College IT Department"
__compliance__ = ["FERPA", "GDPR", "CCPA"]

# Package-level imports for convenience
from bot.config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    GROQ_API_KEY,
    ENVIRONMENT
)

__all__ = [
    '__version__',
    'SUPABASE_URL',
    'SUPABASE_KEY', 
    'GROQ_API_KEY',
    'ENVIRONMENT'
]
