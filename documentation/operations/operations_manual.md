# Operations Manual: College WhatsApp Bot

## Overview
This manual provides IT staff and operations personnel with the essential procedures for deploying, managing, monitoring, and maintaining the College WhatsApp Bot in a production environment.

## Prerequisites
*   Access to the project repository (`college-whatsapp-bot`).
*   Access to deployment platform (e.g., Railway).
*   Access to external services (Supabase, Twilio, Groq, Sentry).
*   Python 3.11 environment.
*   Understanding of `requirements.txt` and virtual environments.

## Deployment Process

### Initial Deployment (New Environment)
1.  **Clone Repository:**
    ```bash
    git clone <repository-url>
    cd college-whatsapp-bot
    ```
2.  **Set up Environment Variables:**
    *   Copy `.env.example` to `.env`.
    *   Fill in all required credentials (Supabase, Groq, Twilio, Sentry DSN, etc.) in the `.env` file.
    *   **CRITICAL:** Ensure `.env` is never committed to the repository (it's in `.gitignore`).
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Apply Database Schema:**
    *   Connect to your Supabase project using `psql` or the web interface.
    *   Execute the enterprise schema from `database/migrations/v2_enterprise_schema.sql`.
5.  **Configure Deployment Platform:**
    *   For Railway: Push the code to your Railway-linked repository. Railway will automatically read `Procfile` and `requirements.txt`. Ensure environment variables are set in the Railway dashboard.
    *   For other platforms: Follow the platform's specific deployment instructions, ensuring the `web` process defined in `Procfile` (`web: uvicorn bot.main:app --host 0.0.0.0 --port $PORT`) is started.
6.  **Configure Twilio Webhook:**
    *   Log into your Twilio console.
    *   Navigate to your WhatsApp number settings.
    *   Set the webhook URL to point to your deployed bot's `/webhook` endpoint (e.g., `https://your-app.railway.app/webhook`).
7.  **Initial Test:** Send a test message via WhatsApp to verify the bot receives and responds.

### Updating the Application
1.  **Pull Latest Code:**
    ```bash
    git pull origin main
    ```
2.  **Update Dependencies (if `requirements.txt` changed):**
    ```bash
    pip install -r requirements.txt --upgrade
    ```
3.  **Apply Database Migrations (if any new `.sql` files exist in `database/migrations/`):**
    *   Manually execute the new migration file against your Supabase instance.
4.  **Redeploy:**
    *   Push changes to the repository (if using CI/CD like Railway).
    *   Or manually redeploy the application package to your platform.
5.  **Verify Deployment:** Check logs and send a test message.

## Daily Operations

### Monitoring System Health
*   **Check Logs:** Monitor application logs on your deployment platform (Railway dashboard) for errors or warnings.
*   **Check Sentry:** Review Sentry dashboard for exceptions and performance issues.
*   **Check Dashboard:** Access the FastAPI dashboard (`/` endpoint) to view real-time metrics (interactions, response times, sentiment).
*   **Check Supabase:** Monitor Supabase connection health and query performance.

### Managing the Knowledge Base
*   See `content_management.md` for detailed instructions on updating the `data/` folder and re-indexing.

### Managing Users/Access (if applicable)
*   If using Supabase Auth for dashboard access, manage user roles and permissions via the Supabase dashboard.

## Maintenance Tasks

### Regular Backup
*   **Database:** Rely on Supabase's automated backup and PITR (Point-in-Time Recovery) features.
*   **Code & Config:** Ensure the repository and `.env` file (stored securely separately) are the source of truth.

### Performance Tuning
*   Monitor response times via the dashboard and Sentry.
*   Review database queries if performance degrades (check Supabase logs/metrics).
*   Consider adjusting Groq model or prompt complexity if API costs or latency become an issue.

### Security Audits
*   Periodically review environment variable access and permissions.
*   Check for updates in dependencies (`pip list --outdated`).
*   Review Supabase RLS policies and access logs.

## Troubleshooting

### Common Issues
*   **Bot not responding:** Check Twilio webhook configuration, application logs, and Supabase connectivity.
*   **Slow responses:** Check Groq API status, database query performance, and application logs for bottlenecks.
*   **Incorrect answers:** Verify the knowledge base (`data/` folder) content and consider refining prompts in `prompt_engine.py`.
*   **Sentry errors:** Review error details in Sentry for debugging clues.
*   **Dashboard not loading:** Check application logs and Supabase connectivity from the dashboard's perspective.

### Escalation
*   For critical issues affecting service, follow the procedures outlined in `incident_response.md`.