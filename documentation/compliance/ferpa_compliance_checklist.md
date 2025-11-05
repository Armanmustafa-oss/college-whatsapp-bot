# FERPA Compliance Checklist: College WhatsApp Bot

## Overview
This checklist ensures the College WhatsApp Bot adheres to the Family Educational Rights and Privacy Act (FERPA). FERPA protects the privacy of student education records. This bot is designed to minimize interaction with direct education records, but compliance principles must be upheld.

## FERPA Compliance Checklist

### 1. Data Minimization & Purpose Limitation

*   [x] **The bot operates primarily on a public-facing knowledge base.** It answers questions based on pre-loaded documents (`data/` folder), not by accessing live student educational records held by the college.
*   [x] **The bot does not request or attempt to access direct PII** (e.g., SSN, specific grades, financial aid details tied to a student record) within its conversation flow.
*   [x] **The bot's function is limited to providing general information** (admissions, fees, programs, campus life) available to prospective and current students, aligning with a legitimate educational interest.
*   [x] **Data collected (user query, bot response, hashed user ID, timestamp, intent, sentiment) is limited to operational support and improvement.**

### 2. Storage of Potentially Identifiable Information

*   [x] **Raw phone numbers are NOT stored in the primary `conversations` table.** The `user_id` field stores a one-way hash of the phone number (e.g., `hash('sha256', 'whatsapp:+1234567890')::TEXT`).
*   [x] **If raw phone numbers are temporarily processed** (e.g., for routing within the webhook handler before hashing), they are not persisted in the main database logs.
*   [x] **No direct student identifiers** (e.g., student ID, full name linked from college systems) are stored within the bot's database (`conversations`, `performance_metrics`, `system_logs`).

### 3. Access Control

*   [x] **Database access is controlled.** Supabase RLS policies are defined (example in `database_schema.md`) to limit data access based on roles (e.g., restricting direct access for non-authorized users).
*   [x] **Application secrets (DB keys, API tokens) are stored securely** using environment variables, not hardcoded.
*   [x] **Deployment platform access is restricted** to authorized personnel.

### 4. Data Retention & Disposal

*   [x] **A clear data retention policy exists** (`data_retention_policy.md`) specifying time limits for conversation logs (1 year) and other data.
*   [x] **Automated deletion mechanisms are planned/implemented** (e.g., using `pg_cron`) to enforce retention limits.

### 5. Disclosure & Sharing

*   [x] **The bot does not share student information** collected during interactions with third parties beyond necessary service providers (Twilio, Supabase, Groq, Sentry) under standard agreements.
*   [x] **Information shared with service providers is necessary** for the bot's core function (e.g., sending messages via Twilio, storing logs in Supabase).
*   [x] **Any disclosure to college administrative systems** (e.g., for a formal FERPA request) would involve data held in the main college systems, not the anonymized bot logs. The hashed `user_id` in the bot's database cannot readily identify a student within the college's main systems.

### 6. Security

*   [x] **Data in transit is encrypted** using TLS for communication with Supabase, Groq, Twilio, and Sentry.
*   [x] **Standard security practices are followed** (dependency updates, input sanitization - `enhancer.py`, secure key storage).

### 7. Documentation & Oversight

*   [x] **This FERPA checklist exists** and is linked to other compliance documents (`privacy_policy.md`, `data_retention_policy.md`).
*   [x] **The system architecture and data flow are documented** (`architecture_overview.md`, `database_schema.md`) to demonstrate compliance efforts.
*   [x] **Staff involved in bot management are aware of FERPA obligations** (covered by operational documentation `operations_manual.md`).

### 8. Handling Requests Related to Education Records

*   [x] **The bot is not designed to retrieve or provide access to specific student education records.** If a user asks for specific personal academic information, the bot should be programmed to respond with a message directing them to the appropriate college office (e.g., Registrar, Financial Aid) and explaining that it cannot access individual records.

## Status

*   **Overall Compliance Status:** [ ] Fully Compliant [x] Compliant with noted controls [ ] Requires Action
*   **Last Reviewed:** [Date]
*   **Next Review Date:** [Date - e.g., Quarterly]

## Notes

*   This bot's design intentionally avoids direct interaction with FERPA-protected educational records stored in the college's main systems. Its primary database (`conversations`) contains anonymized interaction data linked via a hash, not direct student identifiers from the college's authoritative systems. This significantly reduces FERPA risk associated with the bot's *own* data store.
*   Compliance relies on the accuracy of the knowledge base content (ensuring it doesn't inadvertently expose record details) and the robustness of the anonymization strategy (hashing).