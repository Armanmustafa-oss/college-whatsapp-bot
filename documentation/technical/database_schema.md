# Database Schema Documentation: Supabase for College Bot

## Overview
This document details the database schema used by the College WhatsApp Bot, hosted on Supabase (PostgreSQL backend). The schema is designed for operational efficiency, analytics, auditability, and compliance with data privacy principles (FERPA/GDPR).

## Database Platform
*   **Platform:** Supabase (Utilizing PostgreSQL)
*   **Version:** Managed by Supabase (typically latest stable).

## Schema Design Principles

*   **Normalization:** Tables are normalized to reduce redundancy where appropriate.
*   **Indexing:** Critical columns for querying (timestamps, user IDs, intents) are indexed for performance.
*   **Security:** Row-Level Security (RLS) policies are defined (though example policies are provided) to enforce access control.
*   **Compliance:** PII is minimized. `user_id` is intended to be a hashed identifier or a non-PII reference. Sensitive data should not be stored directly in these tables unless encrypted.
*   **Audit Trail:** Tables include `created_at` and `updated_at` timestamps for tracking changes.
*   **Extensibility:** The schema is designed to accommodate future features and metrics.

## Tables

### 1. `conversations`

**Purpose:** Stores the core interaction data between users and the bot. This is the primary table for analyzing user queries, bot responses, and conversation flow.

**Columns:**

| Name                     | Type          | Constraints          | Description                                                                                   |
| :----------------------- | :------------ | :------------------- | :-------------------------------------------------------------------------------------------- |
| `id`                     | `BIGSERIAL`   | `PRIMARY KEY`        | Unique identifier for each conversation entry. Auto-incrementing.                             |
| `user_id`                | `TEXT`        | `NOT NULL`           | Anonymized/Hashed identifier for the user (e.g., SHA256 hash of phone number). **DO NOT store raw PII like full phone numbers or names here.** |
| `session_id`             | `TEXT`        |                      | Identifier to group messages belonging to a single user session.                              |
| `user_message`           | `TEXT`        | `NOT NULL`           | The raw text message sent by the user.                                                        |
| `bot_response`           | `TEXT`        | `NOT NULL`           | The text response sent back by the bot.                                                       |
| `context_used`           | `TEXT`        |                      | Truncated or summarized text of the context retrieved from the RAG system and used by the AI. |
| `intent`                 | `TEXT`        |                      | The classified intent of the user's message (e.g., 'admissions', 'fees', 'courses').          |
| `sentiment`              | `TEXT`        |                      | The detected sentiment of the user's message (e.g., 'positive', 'neutral', 'negative', 'very_negative'). |
| `urgency`                | `TEXT`        |                      | The assessed urgency level of the interaction (e.g., 'low', 'medium', 'high', 'critical').    |
| `response_time_seconds`  | `NUMERIC(5,3)`|                      | The time taken by the bot to process the message and generate a response (in seconds).        |
| `language_code`          | `TEXT`        | `DEFAULT 'en'`       | The language code associated with the interaction (e.g., 'en', 'tr', 'ar').                   |
| `timestamp`              | `TIMESTAMPTZ` | `DEFAULT NOW()`      | The time the interaction occurred, stored with timezone information.                          |
| `created_at`             | `TIMESTAMPTZ` | `DEFAULT NOW()`      | The time this record was created in the database.                                             |
| `updated_at`             | `TIMESTAMPTZ` | `DEFAULT NOW()`      | The time this record was last updated in the database. A trigger updates this automatically.  |

**Indexes:**

*   `idx_conversations_timestamp`: On `timestamp DESC` for time-range queries.
*   `idx_conversations_user_id`: On `user_id` for user-specific analysis.
*   `idx_conversations_intent`: On `intent` for intent-based reporting.
*   `idx_conversations_sentiment`: On `sentiment` for sentiment analysis.
*   `idx_conversations_urgency`: On `urgency` for escalation monitoring.
*   `idx_conversations_session_id`: On `session_id` for session analysis.

### 2. `performance_metrics`

**Purpose:** Stores granular performance and operational metrics collected by the application (e.g., API call durations, response times, error counts). Used for monitoring, alerting, and performance optimization.

**Columns:**

| Name        | Type          | Constraints          | Description                                                                                   |
| :---------- | :------------ | :------------------- | :-------------------------------------------------------------------------------------------- |
| `id`        | `BIGSERIAL`   | `PRIMARY KEY`        | Unique identifier for each metric entry. Auto-incrementing.                                   |
| `metric_type`| `TEXT`       | `NOT NULL`           | The type or category of the metric (e.g., 'response_time', 'api_call_duration', 'error_rate').|
| `value`     | `NUMERIC`     | `NOT NULL`           | The numeric value of the metric (e.g., duration in seconds, count, percentage).               |
| `tags`      | `JSONB`       |                      | Flexible key-value pairs for categorization (e.g., `{"intent": "admissions", "api": "groq"}`).|
| `unit`      | `TEXT`        | `DEFAULT 'count'`    | The unit of measurement for the value (e.g., 'seconds', 'count', 'percentage').               |
| `timestamp` | `TIMESTAMPTZ` | `DEFAULT NOW()`      | The time the metric was recorded, stored with timezone information.                           |

**Indexes:**

*   `idx_performance_metrics_timestamp`: On `timestamp DESC` for time-range queries.
*   `idx_performance_metrics_type`: On `metric_type` for metric-specific analysis.
*   `idx_performance_metrics_tags`: GIN index on `tags` for efficient querying within the JSONB field.

### 3. `system_logs`

**Purpose:** Stores critical system events, errors, and warnings generated by the application services. Used for debugging, auditing, and incident response.

**Columns:**

| Name        | Type          | Constraints          | Description                                                                                   |
| :---------- | :------------ | :------------------- | :-------------------------------------------------------------------------------------------- |
| `id`        | `BIGSERIAL`   | `PRIMARY KEY`        | Unique identifier for each log entry. Auto-incrementing.                                      |
| `level`     | `TEXT`        | `NOT NULL`           | The severity level of the log (e.g., 'INFO', 'WARNING', 'ERROR', 'CRITICAL').                 |
| `service`   | `TEXT`        | `NOT NULL`           | The service or component that generated the log (e.g., 'bot', 'dashboard', 'rag', 'monitoring').|
| `message`   | `TEXT`        | `NOT NULL`           | The main log message.                                                                         |
| `details`   | `JSONB`       |                      | Additional structured details related to the log event (e.g., error trace, user ID).          |
| `timestamp` | `TIMESTAMPTZ` | `DEFAULT NOW()`      | The time the log event occurred, stored with timezone information.                            |

**Indexes:**

*   `idx_system_logs_timestamp`: On `timestamp DESC` for time-range queries.
*   `idx_system_logs_level`: On `level` for filtering by severity.
*   `idx_system_logs_service`: On `service` for filtering by component.

### 4. `knowledge_base_documents`

**Purpose:** Tracks metadata about the documents ingested into the RAG system's vector store (ChromaDB). Provides auditability and helps manage the knowledge base.

**Columns:**

| Name             | Type          | Constraints          | Description                                                                                   |
| :--------------- | :------------ | :------------------- | :-------------------------------------------------------------------------------------------- |
| `id`             | `UUID`        | `PRIMARY KEY, DEFAULT gen_random_uuid()` | Unique identifier for each document record. Auto-generated UUID.                              |
| `filename`       | `TEXT`        | `NOT NULL`           | The original name of the source document file (e.g., `tuition_fees_2024.pdf`).                |
| `source_path`    | `TEXT`        | `NOT NULL`           | The file path where the original document is stored (relative to the `data/` directory or an external storage path). |
| `checksum`       | `TEXT`        | `NOT NULL`           | A cryptographic hash (e.g., SHA256) of the document content, used to detect changes.          |
| `embedding_model`| `TEXT`        | `NOT NULL`           | The name of the model used to generate the embeddings for this document.                      |
| `indexed_at`     | `TIMESTAMPTZ` | `DEFAULT NOW()`      | The time the document was successfully indexed into the vector store.                         |
| `status`         | `TEXT`        | `DEFAULT 'indexed'`  | The current status of the document in the indexing process (e.g., 'indexing', 'indexed', 'failed'). |

**Indexes:**

*   `idx_knowledge_base_checksum`: On `checksum` to quickly identify if a document has changed.
*   `idx_knowledge_base_status`: On `status` for monitoring indexing jobs.

## Views

### 1. `daily_conversation_summary`

**Purpose:** Provides a pre-aggregated view of conversation metrics grouped by day, simplifying dashboard queries for daily trends.

**Columns:**

*   `day` (DATE): The date truncated from the conversation `timestamp`.
*   `total_interactions` (BIGINT): Count of all conversations on that day.
*   `avg_response_time` (NUMERIC): Average response time for that day.
*   `positive_sentiment_rate` (NUMERIC): Percentage of positive sentiments for that day.
*   `negative_interactions` (BIGINT): Count of negative or very negative sentiments for that day.
*   `escalated_conversations` (BIGINT): Count of conversations marked as urgent or very negative for that day.
*   `unique_users` (BIGINT): Count of distinct `user_id`s for that day.

### 2. `daily_intent_breakdown`

**Purpose:** Shows the count of conversations for each intent, grouped by day.

**Columns:**

*   `day` (DATE): The date truncated from the conversation `timestamp`.
*   `intent` (TEXT): The intent category.
*   `count` (BIGINT): The number of conversations for that intent on that day.

### 3. `recent_performance_summary`

**Purpose:** Provides an aggregated view of performance metrics for the last 24 hours, grouped by metric type and tags.

**Columns:**

*   `metric_type` (TEXT): The type of metric.
*   `tags` (JSONB): The tags associated with the metric.
*   `avg_value` (NUMERIC): Average value for the group.
*   `min_value` (NUMERIC): Minimum value for the group.
*   `max_value` (NUMERIC): Maximum value for the group.
*   `sample_count` (BIGINT): Number of samples aggregated.

## Security & Access Control (RLS Example)

*   **Row Level Security (RLS)** is enabled on the `conversations` table.
*   **Example Policy:** A policy could be created allowing only users authenticated via Supabase Auth (e.g., admin users) to access data, potentially filtered by their role or department.
    ```sql
    -- Example: Only 'admin' role can read conversations
    CREATE POLICY conversations_admin_access ON conversations
        FOR SELECT
        USING (auth.role() = 'admin');
    ```
*   **Service Role Access:** The application service (the bot itself) uses a service role key to insert data, bypassing RLS for writes but respecting it for reads if needed by the application logic.

## Data Retention

*   Long-term retention is primarily handled by Supabase's built-in backup and PITR (Point-in-Time Recovery) features.
*   Manual deletion jobs (e.g., using `pg_cron`) can be scheduled *if necessary* to remove very old logs or conversation data according to the defined retention policy (see `data_retention_policy.md` in compliance folder). Exercise caution with deletion to preserve historical data for analysis and compliance.