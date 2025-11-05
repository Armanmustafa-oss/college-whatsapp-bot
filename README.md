# 🚀 College WhatsApp AI Assistant

An enterprise-grade, multilingual chatbot designed to revolutionize student support via WhatsApp. Built for scalability, reliability, and compliance, this bot provides instant, accurate answers to common student inquiries, enhancing the overall college experience.

## ✨ Features

*   **🤖 AI-Powered Responses:** Leverages Groq AI for fast and contextually relevant answers.
*   **🌍 Multilingual Support:** Currently supports English, Turkish, and Arabic (easily extensible).
*   **📱 WhatsApp Business Integration:** Seamlessly connects with students on their preferred platform.
*   **📊 Real-Time Analytics Dashboard:** Monitor bot performance, user sentiment, and conversation trends with an interactive dashboard.
*   **🔒 FERPA/GDPR Compliant:** Engineered with data privacy and security at its core.
*   **🔍 Retrieval-Augmented Generation (RAG):** Provides accurate answers based on your institution's specific documents and knowledge base.
*   **⚙️ Advanced Prompt Engineering:** Dynamic, context-aware prompts for improved AI interaction.
*   **🛡️ Robust Monitoring:** Integrated error tracking (Sentry) and performance metrics.
*   **🔄 Automated CI/CD:** Streamlined testing and deployment via GitHub Actions.

## 🏗️ Architecture Overview

*   **Backend:** FastAPI for the main webhook handler and dashboard API.
*   **AI:** Groq API for language model interaction.
*   **RAG:** ChromaDB for vector storage and retrieval of knowledge base documents.
*   **Database:** Supabase (PostgreSQL) for conversation logs, metrics, and metadata.
*   **Monitoring:** Sentry for error tracking, custom performance tracking.
*   **Deployment:** Railway (or similar container-based platform).
*   **Frontend (Dashboard):** FastAPI serving Plotly charts for analytics.

For a detailed breakdown, see the [Technical Architecture Documentation](./documentation/technical/architecture_overview.md).

## 🚀 Quick Start

### Prerequisites

*   Python 3.11
*   Git
*   Access to required API keys/services (Supabase, Groq, Twilio)

### Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/college-whatsapp-bot.git
    cd college-whatsapp-bot
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   Edit `.env` with your specific credentials (Supabase, Groq, Twilio, etc.).
    *   **Important:** Never commit the `.env` file. It's included in `.gitignore`.

5.  **Set up the Database:**
    *   Create a Supabase project.
    *   Apply the enterprise schema (`database/migrations/v2_enterprise_schema.sql`) to your Supabase database instance using the SQL Editor or `psql`.

6.  **Prepare Knowledge Base:**
    *   Place your college's information documents (PDF, TXT) into the `data/` directory.
    *   Run the re-indexing script to update the RAG system:
        ```bash
        python scripts/reindex_documents.py
        ```

7.  **Run the Bot Locally:**
    ```bash
    # Start the main bot service
    uvicorn bot.main:app --host 0.0.0.0 --port 8000
    ```

8.  **Run the Dashboard Locally (in a separate terminal):**
    ```bash
    # Start the dashboard service
    uvicorn dashboard.app:app --host 0.0.0.0 --port 8001
    ```
    Access the dashboard at `http://localhost:8001`.

### Configuration

*   **Twilio Webhook:** Point your Twilio WhatsApp number's incoming message webhook to your deployed bot's `/webhook` endpoint (e.g., `https://your-app.railway.app/webhook`).

## 📋 Documentation

Comprehensive documentation is available in the `documentation/` folder:

*   **Executive:** Overview, ROI, Compliance.
*   **Operations:** Deployment, Monitoring, Incident Response.
*   **Technical:** Architecture, API, Troubleshooting.
*   **Compliance:** Data Retention, Privacy, FERPA.

## 🧪 Testing

Run the test suite using pytest:

```bash
pytest tests/ -v

🚢 Deployment
The project is configured for deployment on Railway using the railway.toml and Procfile. Ensure all required environment variables are set in your Railway project settings.

🤝 Contributing
Contributions are welcome! Please open an issue or submit a pull request.