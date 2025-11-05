# Incident Response Plan: College WhatsApp Bot

## Overview
This plan defines the procedures to follow when a significant incident occurs with the College WhatsApp Bot, potentially impacting service availability or user experience.

## Incident Classification

*   **Critical:** Bot is completely down/unresponsive, or a security breach is suspected. Affects all users.
*   **High:** Bot is responding slowly (e.g., >5 seconds average), or a specific functionality (like RAG) is broken, significantly impacting user experience. Affects many users.
*   **Medium:** Specific features are degraded (e.g., dashboard temporarily unavailable), or error rate has increased but bot still responds. Affects some users.
*   **Low:** Minor errors logged in Sentry or logs, but overall service is functional. Affects few users or internal processes.

## Incident Response Team

*   **Primary On-Call:** [Name/Contact] - IT Operations
*   **Secondary On-Call:** [Name/Contact] - Developer
*   **Manager/Lead:** [Name/Contact] - For escalation and communication decisions.

## Response Procedures

### 1. Detection & Initial Assessment
*   An incident is detected via monitoring tools (logs, Sentry, dashboard, user reports).
*   The on-call person acknowledges the alert and performs an initial assessment:
    *   What is the symptom? (e.g., bot not responding, slow responses, errors)
    *   What is the potential impact? (Refer to classification above)
    *   When did it start?

### 2. Communication
*   **Critical/High Incidents:**
    *   Immediately notify the Manager/Lead and Secondary On-Call.
    *   If the bot is down for more than 15 minutes, consider sending a brief status update to a designated internal communication channel (e.g., Slack/Teams) or a status page if available.
*   **Medium/Low Incidents:**
    *   Log the incident (see Step 3).
    *   Address during normal working hours or schedule for later.

### 3. Logging & Documentation
*   Create an incident log entry with:
    *   **Timestamp:** When the incident was detected.
    *   **Symptoms:** What was observed.
    *   **Impact:** Classification and potential effect on users.
    *   **Initial Assessment:** Suspected cause (if any).
    *   **Status:** Active, Investigating, Identified, Resolved, Closed.
    *   **Actions Taken:** Steps performed to diagnose/fix.
    *   **Resolution Time:** When the issue was resolved.
    *   **Root Cause:** Determined cause of the incident (filled in later).

### 4. Investigation & Diagnosis
*   Gather more information from all monitoring tools (logs, Sentry, dashboard, Supabase).
*   Check external service status pages (Twilio, Groq, Supabase).
*   Reproduce the issue if possible.
*   Identify the root cause (e.g., dependency failure, code bug, resource exhaustion, network issue).

### 5. Resolution
*   Apply the fix based on the root cause:
    *   **Code Bug:** Deploy a hotfix.
    *   **Configuration Issue:** Correct the configuration.
    *   **External Service Down:** Wait for resolution or implement a temporary workaround if possible.
    *   **Resource Exhaustion:** Scale resources or optimize code/processes.
*   Verify the fix resolves the issue by checking monitoring tools and sending test messages.

### 6. Post-Incident Review (for Critical/High Incidents)
*   After resolution, schedule a brief meeting with the team.
*   Review the incident log.
*   Discuss what went well and what could be improved in the response process.
*   Identify any required follow-up actions (e.g., code changes, monitoring improvements, documentation updates) to prevent similar incidents or reduce their impact.
*   Update the incident log with the root cause and lessons learned.

### 7. Communication (Upon Resolution)
*   **Critical/High Incidents:** Send a follow-up communication confirming the service is restored and a brief statement on the cause/resolution if appropriate.

## Contact Information

*   **Primary On-Call:** [Contact Details]
*   **Secondary On-Call:** [Contact Details]
*   **Manager/Lead:** [Contact Details]
*   **Emergency Escalation:** [Contact Details, if applicable]