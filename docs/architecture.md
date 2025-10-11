# College WhatsApp Bot – System Architecture

## Overview
AI-powered WhatsApp bot for international students. Answers questions in English, Turkish, Arabic using RAG + Groq.

## Data Flow
Student → Twilio → Railway (FastAPI) → Supabase (log) → ChromaDB (RAG) → Groq (LLM) → Response → Twilio → Student

## Components
- **Messaging**: Twilio WhatsApp API
- **AI**: Groq (Llama 3.1)
- **RAG**: ChromaDB (with synonym expansion)
- **Storage**: Supabase (PostgreSQL)
- **Monitoring**: Sentry + Gradio Dashboard
- **Hosting**: Railway (2 services: bot + dashboard)