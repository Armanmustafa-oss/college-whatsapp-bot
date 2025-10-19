
---

### 🔹 Step 4: Create Technical Documents

#### File: `docs/technical/1_architecture_overview.md`

```markdown
# System Architecture Overview

## Architecture Diagram

┌─────────────────────────────────────────────────────────────┐
│ STUDENT │
│ (WhatsApp User) │
└────────────────────────┬────────────────────────────────────┘
│
▼
┌───────────────────────────────┐
│ Twilio WhatsApp Business │
│ (Message Gateway) │
└───────────────┬───────────────┘
│
▼
┌───────────────────────────────┐
│ FastAPI Webhook Handler │
│ (Railway.app hosting) │
└───────────────┬───────────────┘
│
┌───────────────┴───────────────┐
│ │
▼ ▼
┌─────────────────┐ ┌──────────────────┐
│ Language │ │ Phone Number │
│ Detection │ │ Hashing (SHA256)│
│ (langdetect) │ │ (Privacy Layer) │
└────────┬────────┘ └────────┬─────────┘
│ │
▼ ▼
┌─────────────────────────────────────────────┐
│ RAG Pipeline │
│ ┌─────────────────────────────┐ │
│ │ ChromaDB Vector Search │ │
│ │ (Semantic similarity) │ │
│ └──────────┬──────────────────┘ │
│ ▼ │
│ ┌─────────────────────────────┐ │
│ │ Context Assembly │ │
│ │ (Top 5 relevant docs) │ │
│ └──────────┬──────────────────┘ │
└─────────────┼──────────────────────────────┘
│
▼
┌─────────────────────────────────┐
│ Groq API (LLM Generation) │
│ Model: Mixtral-8x7b-32768 │
│ (Fast, cost-effective) │
└─────────────┬───────────────────┘
│
▼
┌─────────────────────────────────┐
│ Response Enhancement │
│ - Remove question repetition │
│ - Sanitize internal references│
│ - Quality scoring │
└─────────────┬───────────────────┘
│
├──────────────────┬──────────────────┐
▼ ▼ ▼
┌────────────────┐ ┌────────────────┐ ┌────────────┐
│ Supabase DB │ │ Sentry Logs │ │ WhatsApp │
│ (Analytics) │ │ (Monitoring) │ │ (Reply) │
└────────────────┘ └────────────────┘ └────────────┘

## Technology Stack

| Component | Technology | Purpose | Cost |
|-----------|-----------|---------|------|
| **Backend** | FastAPI (Python) | Webhook handler, API | Free |
| **LLM** | Groq (Mixtral-8x7b) | Response generation | $24.50/mo |
| **Vector DB** | ChromaDB | Semantic search | Free |
| **Database** | Supabase (PostgreSQL) | Analytics storage | Free tier |
| **Hosting** | Railway.app | 24/7 deployment | $25/mo |
| **Messaging** | Twilio WhatsApp | Student communication | $35.67/mo |
| **Monitoring** | Sentry | Error tracking | Free tier |
| **Dashboard** | FastAPI HTML | Admin interface | Included |