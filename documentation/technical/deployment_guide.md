# Deployment Guide: College WhatsApp Bot

## Overview
This guide provides step-by-step instructions for deploying the College WhatsApp Bot application to a cloud platform. The example uses Railway, but the principles apply to similar container-based platforms (e.g., Heroku, Fly.io).

## Prerequisites

*   A Git repository containing the complete project code.
*   Accounts on the following services:
    *   **Deployment Platform:** Railway (or chosen platform).
    *   **Database:** Supabase.
    *   **Communication:** Twilio (for WhatsApp).
    *   **AI Service:** Groq.
    *   **Monitoring:** Sentry (optional but recommended).
*   API keys and connection details for the above services.
*   Git client installed locally.

## Deployment Steps (Railway Example)

### 1. Set up External Services

1.  **Supabase:**
    *   Create a new project.
    *   Note down the `Project URL` and `anon key` (or create a service role key if needed for the application).
    *   Apply the Enterprise Schema (`database/migrations/v2_enterprise_schema.sql`) to your Supabase database instance using the SQL Editor or `psql`.
2.  **Twilio:**
    *   Create a Twilio account.
    *   Obtain your `Account SID` and `Auth Token`.
    *   Configure a WhatsApp Sandbox or connect a dedicated number. Note the number (format: `whatsapp:+1415...`).
3.  **Groq:**
    *   Sign up for a Groq account.
    *   Obtain your API key.
4.  **Sentry (Optional):**
    *   Create a Sentry project.
    *   Obtain the `DSN` (Data Source Name).

### 2. Prepare Your Codebase

1.  **Ensure your code is in a Git repository.**
2.  **Verify `requirements.txt`:** Ensure it lists all necessary dependencies (FastAPI, Twilio, Supabase, Groq, etc.).
3.  **Verify `Procfile`:** Ensure it correctly defines the `web` process for your bot (e.g., `web: uvicorn bot.main:app --host 0.0.0.0 --port $PORT`).
4.  **Verify `railway.toml` (if using Railway):** Ensure it specifies the correct buildpacks and start command (e.g., `startCommand = "uvicorn bot.main:app --host 0.0.0.0 --port $PORT"`).

### 3. Deploy to Railway

1.  **Install Railway CLI (Optional but recommended):**
    *   Follow instructions on [https://docs.railway.app/develop/cli](https://docs.railway.app/develop/cli)
2.  **Link your repository to Railway:**
    *   Go to [https://railway.app](https://railway.app) and create a new project.
    *   Choose "Deploy from GitHub".
    *   Select your `college-whatsapp-bot` repository.
3.  **Configure Environment Variables in Railway:**
    *   In your Railway project dashboard, navigate to the "Variables" section.
    *   Add the following variables, using the values obtained in Step 1:
        *   `SUPABASE_URL`: Your Supabase Project URL.
        *   `SUPABASE_KEY`: Your Supabase anon key (or service role key).
        *   `GROQ_API_KEY`: Your Groq API key.
        *   `TWILIO_ACCOUNT_SID`: Your Twilio Account SID.
        *   `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token.
        *   `TWILIO_WHATSAPP_NUMBER`: Your Twilio WhatsApp number.
        *   `SENTRY_DSN`: Your Sentry DSN (if using Sentry).
        *   `ENVIRONMENT`: Set to `production`.
        *   `PORT`: Railway usually sets this automatically, but you can define it (e.g., `8000`).
        *   `COLLEGE_NAME`: Your college's name (used by PromptEngine).
        *   `DEFAULT_LANGUAGE`: Default language code (e.g., `en`).
        *   `RATE_LIMIT_MESSAGES`: Number of messages allowed per window (e.g., `10`).
        *   `RATE_LIMIT_WINDOW`: Time window in seconds (e.g., `60`).
        *   `MAX_MESSAGE_LENGTH`: Max message length accepted (e.g., `1600`).
        *   `MAX_CONVERSATION_HISTORY`: Max history stored per session (e.g., `10`).
        *   `DASHBOARD_PASSWORD`: Password for the dashboard (if applicable).
        *   *(Add any other variables defined in `bot/config.py`)*
    *   **CRITICAL:** Ensure `.env` files are *not* committed and are listed in `.gitignore`.
4.  **Configure Build & Deploy Settings:**
    *   Railway will typically auto-detect the buildpack (Nixpacks for Python).
    *   Ensure the start command matches the `web` process in your `Procfile` or `railway.toml`.
5.  **Deploy:**
    *   Commit any changes to your repository (`git add .`, `git commit -m "Deploy config"`, `git push`).
    *   Railway will automatically detect the commit and start a new deployment based on your `Procfile`.
    *   Monitor the deployment logs in the Railway dashboard.

### 4. Configure Twilio Webhook

1.  **Get the Deployment URL:**
    *   Once Railway deployment is successful, note the assigned URL for your `web` service (e.g., `https://your-app-name.up.railway.app`).
2.  **Set Webhook in Twilio:**
    *   Go to your Twilio console.
    *   Navigate to your WhatsApp Sandbox or phone number settings.
    *   Set the `Webhook URL for when a message comes in` to `https://your-app-name.up.railway.app/webhook`.
    *   Ensure the HTTP method is `HTTP POST`.

### 5. Deploy the Dashboard (Optional)

*   If your `Procfile` includes a `dashboard` process (e.g., `dashboard: uvicorn dashboard.app:app --host 0.0.0.0 --port $PORT`), Railway will attempt to deploy it as a separate service.
*   You will need to add the same environment variables to this dashboard service in Railway.
*   Access the dashboard via its own Railway-assigned URL.

### 6. Verification

1.  **Check Logs:** Review logs in Railway for any startup errors.
2.  **Test Bot:** Send a message via WhatsApp to your configured number. Verify the bot responds.
3.  **Check Dashboard:** If deployed, access the dashboard URL and verify it loads metrics from Supabase.
4.  **Check Sentry:** If configured, verify no critical errors are reported immediately after deployment.

## Rollback Procedure

*   If a deployment introduces issues, Railway allows you to easily rollback to a previous successful deployment version from the dashboard.

## Post-Deployment Tasks

*   Set up monitoring alerts (platform, Sentry, Supabase).
*   Configure automated backups (Supabase).
*   Plan for regular updates and patching.
*   Document the deployment URLs and access procedures for the team.