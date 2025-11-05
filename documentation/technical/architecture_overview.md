# Technical Architecture Overview: Enterprise College WhatsApp Bot

## Vision & Purpose
This document outlines the technical architecture of the College WhatsApp Bot, designed for scalability, security, performance, and maintainability. It serves as the foundational blueprint for developers, architects, and technical stakeholders, ensuring the system operates as a robust, mission-critical platform.

## System Overview
The bot is a distributed, microservice-inspired application built primarily in Python. It leverages cloud-native technologies to provide a reliable, 24/7 AI-powered support channel for students via WhatsApp.

## High-Level Architecture

[User (WhatsApp)] <===> [Twilio (WhatsApp API)] <===> [Load Balancer (Platform)] <===> [Bot API Service (FastAPI)]
|
v
[Dashboard Service (FastAPI)] <===> [Supabase (PostgreSQL)] <===> [ChromaDB (Vector Store)]
| | |
v v v
[Browser] [Logs, Metrics] [Knowledge Base (data/)]
|
v
[Sentry (Error Tracking)]


## Component Breakdown

### 1. Interaction Layer
*   **Platform:** WhatsApp Business API, facilitated by Twilio.
*   **Responsibility:** Receives user messages and delivers bot responses.
*   **Technology:** Twilio's REST API and webhook mechanism.

### 2. Application Layer (Bot Core)
*   **Framework:** FastAPI (`bot/main.py`).
*   **Responsibility:** Orchestrates the entire message processing pipeline.
*   **Key Components:**
    *   **Webhook Handler (`bot/main.py`):** Receives requests from Twilio, performs initial validation, and initiates the processing flow.
    *   **Configuration Manager (`bot/config.py`):** Centralizes environment variable loading and application settings.
    *   **Rate Limiter:** Prevents abuse by limiting requests per user/session.
    *   **Session Context Builder:** Aggregates user identity, history (if applicable), and current message into a context object.

### 3. Intelligence Layer
*   **Prompt Engineering Engine (`bot/prompts/prompt_engine.py`):** Dynamically constructs system and user prompts for the AI model, incorporating context (user query, RAG context, intent, sentiment, user profile) and institutional identity.
*   **RAG (Retrieval-Augmented Generation) System (`bot/rag/`):**
    *   **Retriever (`bot/rag/retriever.py`):** Interfaces with the Vector Store to find relevant information based on the user's query.
    *   **Vector Store (`bot/rag/vector_store.py`):** Uses ChromaDB to store and search document embeddings for contextual information retrieval.
*   **AI Interaction Layer:** Calls the Groq API with the engineered prompts to generate responses.
*   **Response Quality Enhancer (`bot/response_quality/enhancer.py`):** Sanitizes, formats, and applies post-processing rules to the AI's raw response before sending it back to the user.

### 4. Data Layer
*   **Operational Data Store:** Supabase (PostgreSQL backend).
    *   **Purpose:** Stores conversation logs, performance metrics, system logs, and knowledge base metadata.
    *   **Key Tables:**
        *   `conversations`: Stores user messages, bot responses, context used, classification results (intent, sentiment, urgency), and timestamps.
        *   `performance_metrics`: Stores application performance metrics (response times, API call durations).
        *   `system_logs`: Stores critical system events and errors.
        *   `knowledge_base_documents`: Tracks metadata about documents ingested into the RAG system.
    *   **Security:** Row-Level Security (RLS) policies enforce access control.
*   **Knowledge Base:** Source documents (PDF, TXT) stored in the `data/` directory. Processed and indexed by the RAG system.

### 5. Analytics & Presentation Layer
*   **Dashboard Service (`dashboard/app.py`):** A FastAPI application that queries Supabase to retrieve metrics and logs, then renders them using Plotly for interactive visualizations. Provides real-time operational visibility.

### 6. Observability & Monitoring Layer
*   **Error Tracking:** Sentry SDK integrated via `monitoring/sentry_config.py`. Captures exceptions, provides performance tracing, and allows for rich context attachment.
*   **Performance Tracking:** Custom utilities in `monitoring/performance.py` collect metrics and can log them to Supabase.

### 7. Deployment & Infrastructure
*   **Platform:** Railway (or similar container-based platform).
*   **Runtime:** Python 3.11.
*   **Dependencies:** Managed via `requirements.txt`.
*   **Configuration:** Environment variables (`.env`).
*   **Process Management:** `Procfile` defines the `web` and `dashboard` processes for deployment.

## Data Flow (Detailed)

1.  **Message Ingress:** A user sends a message via WhatsApp. Twilio receives it and sends an HTTP POST request (webhook) to the `/webhook` endpoint of the Bot API Service.
2.  **Initial Processing:** `bot/main.py` receives the request, extracts message content and sender ID, performs rate limiting checks, and prepares a `ConversationContext` object.
3.  **RAG Retrieval:** The `Retriever` queries the `VectorStore` (ChromaDB) using the user's query to find relevant context chunks from the `data/` documents.
4.  **Prompt Construction:** The `PromptEngine` uses the `ConversationContext` and retrieved context to build a detailed system prompt and user prompt for the AI.
5.  **AI Generation:** The system and user prompts are sent to the Groq API. The AI model generates a raw text response.
6.  **Response Enhancement:** The `ResponseEnhancer` processes the raw AI response, applying sanitization, formatting, and standard footers/disclaimers.
7.  **Message Egress:** `bot/main.py` sends the enhanced response back to the user via Twilio's API.
8.  **Data Persistence:** Asynchronously (or in the background), `bot/main.py` logs the full interaction (user query, bot response, context, metadata) to the `conversations` table in Supabase. Performance metrics are also logged to `performance_metrics`.
9.  **Monitoring:** Sentry captures any errors or performance traces. The Dashboard service polls Supabase to display metrics.

## Security Considerations
*   **API Security:** Secrets (Supabase keys, Twilio tokens, Groq API key) are stored in environment variables.
*   **Data Security:** Data in transit is encrypted (TLS). Supabase handles database encryption at rest.
*   **Input Sanitization:** The `ResponseEnhancer` sanitizes output. Input validation should occur where necessary (e.g., phone number format via Twilio).
*   **Access Control:** Supabase RLS policies control data access. Environment variables are not committed to the repository.
*   **Compliance:** Architecture designed with FERPA/GDPR principles (data minimization, purpose limitation, storage limitation) in mind.

## Scalability Considerations
*   **Stateless Core:** The main bot service (`bot/main.py`) is designed to be stateless, allowing for horizontal scaling.
*   **Database Scaling:** Supabase provides managed scaling for PostgreSQL.
*   **Vector Store Scaling:** ChromaDB's performance and scaling depend on the underlying storage and hardware. For massive scale, consider managed vector DBs.
*   **API Limits:** Be aware of rate limits on external APIs (Twilio, Groq) and implement backoff/retry logic if necessary.

## Maintainability Considerations
*   **Modular Design:** Components (Prompts, RAG, Enhancement) are separated into distinct modules/files.
*   **Configuration Management:** Centralized configuration via `config.py`.
*   **Comprehensive Logging & Monitoring:** Facilitates debugging and proactive issue resolution.
*   **Documentation:** This document and others provide clear guidance.
*   **Testing:** A test suite (`tests/`) is planned for ensuring code quality and preventing regressions.