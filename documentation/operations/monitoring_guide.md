# System Health Monitoring Guide for the College Bot

## Overview
This guide details the tools and procedures for monitoring the health, performance, and reliability of the deployed College WhatsApp Bot. Proactive monitoring is essential for maintaining high availability and user satisfaction.

## Key Monitoring Tools & Data Sources

### 1. Application Logs (Platform - e.g., Railway)
*   **Location:** Accessible via the deployment platform's dashboard.
*   **Purpose:** Captures application-level errors, warnings, info messages, and request/response details.
*   **What to Monitor:**
    *   **Errors:** Look for `ERROR` or `CRITICAL` level logs. Investigate the cause immediately.
    *   **Warnings:** `WARNING` level logs might indicate potential issues or degraded performance (e.g., rate limits hit, slow external API calls).
    *   **Traffic:** General request volume can indicate normal operation or unexpected spikes.
*   **Action:** Set up log alerts on the platform if available (e.g., alert on error count exceeding a threshold).

### 2. Sentry (Error Tracking & Performance)
*   **Location:** Sentry dashboard (URL configured via `SENTRY_DSN`).
*   **Purpose:** Provides detailed error reports (stack traces), performance transaction traces, and custom metrics.
*   **What to Monitor:**
    *   **New Issues:** Check for any new errors reported.
    *   **Issue Frequency:** Monitor how often existing errors occur. Spikes indicate problems.
    *   **Performance Transactions:** Review slow transactions (e.g., webhook processing time, Groq API calls) to identify bottlenecks.
    *   **Custom Metrics:** If implemented, monitor custom metrics related to business logic.
*   **Action:** Configure Sentry alerts for critical errors or performance degradation (e.g., average transaction duration exceeding a threshold).

### 3. Integrated Dashboard (`/` endpoint)
*   **Location:** The FastAPI application running the dashboard (e.g., `https://your-app.railway.app/`).
*   **Purpose:** Provides real-time, visual analytics on user interactions, sentiment, response times, and system status.
*   **What to Monitor:**
    *   **Total Interactions:** General activity level.
    *   **Average Response Time:** Increasing times indicate performance issues.
    *   **Positive Sentiment Rate:** Dropping rates might indicate inaccurate answers or user frustration.
    *   **Escalated Conversations:** Increasing numbers might indicate the bot is struggling with certain topics.
    *   **System Status Indicator:** Should ideally be "Operational."
*   **Action:** Review the dashboard regularly (e.g., daily) for trends and anomalies.

### 4. Supabase (Database & Authentication)
*   **Location:** Supabase Dashboard (project URL).
*   **Purpose:** Monitor database health, query performance, connection pooling, and authentication logs.
*   **What to Monitor:**
    *   **Connection Pool:** Ensure connections are not exhausted.
    *   **Query Performance:** Look for slow queries in the SQL Editor logs.
    *   **Data Growth:** Monitor table sizes (e.g., `conversations`) for unexpected growth.
    *   **RLS Logs:** If configured, check for RLS policy violations.
*   **Action:** Set up database alerts within Supabase if available, or monitor logs proactively.

### 5. External Services (Twilio, Groq)
*   **Location:** Twilio Console, Groq Dashboard.
*   **Purpose:** Monitor the health and usage of external dependencies.
*   **What to Monitor:**
    *   **Twilio:** Message delivery status, webhook delivery success/failure rates, account balance/usage.
    *   **Groq:** API usage limits, request/response times, any reported service status issues.
*   **Action:** Configure alerts within these services if possible. Monitor usage quotas to avoid unexpected costs or service interruption.

## Daily Monitoring Checklist

1.  **Check Application Logs:** Scan for any `ERROR` or `WARNING` messages.
2.  **Review Sentry Dashboard:** Look for new issues or spikes in existing ones. Check performance traces if response times seem high.
3.  **Check Integrated Dashboard:** Review key metrics (interactions, response time, sentiment, status).
4.  **Quick Health Check:** Send a test message via WhatsApp to ensure the bot responds.

## Weekly Monitoring Review

1.  **Analyze Trends:** Look at the dashboard metrics over the past week for trends (e.g., increasing response times, declining sentiment on specific days).
2.  **Review Sentry Issues:** Prioritize and plan fixes for recurring or critical errors.
3.  **Check External Service Usage:** Ensure usage is within expected ranges and budgets.
4.  **Review Supabase Logs:** Look for any database performance anomalies or unusual query patterns.

## Incident Response
If monitoring indicates a significant issue (e.g., high error rate, slow response times, dashboard showing critical status), follow the procedures outlined in `incident_response.md`.