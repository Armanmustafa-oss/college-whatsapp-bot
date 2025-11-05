# Data Retention Policy: College WhatsApp Bot

## Overview
This policy defines the duration for which data related to the College WhatsApp Bot is retained and the procedures for its secure deletion. It aligns with legal requirements (FERPA, GDPR) and operational best practices, ensuring data minimization and privacy protection.

## Scope
This policy applies to all data generated, processed, or stored by the College WhatsApp Bot system, including:

*   Conversation logs stored in the Supabase `conversations` table.
*   Performance metrics stored in the Supabase `performance_metrics` table.
*   System logs stored in the Supabase `system_logs` table.
*   Metadata about knowledge base documents stored in the `knowledge_base_documents` table.
*   Source documents stored in the `data/` directory (managed separately, but referenced here for completeness).

## Policy Principles

*   **Data Minimization:** Only collect and retain data necessary for the bot's operational purpose (answering student queries, improving service, monitoring performance).
*   **Purpose Limitation:** Data collected for operational support shall not be used for unrelated purposes without explicit legal basis or user consent.
*   **Storage Limitation:** Data shall be retained only for as long as necessary to fulfill its purpose or as required by law.
*   **Security:** Data must be securely stored and deleted according to established procedures.

## Retention Periods

### 1. Conversation Logs (`conversations` table)

*   **Purpose:** To analyze bot performance, user needs, improve responses, and for limited audit trails.
*   **Retention Period:** **1 year** from the `timestamp` of the conversation.
*   **Rationale:** Provides sufficient time for analysis and improvement while minimizing the amount of historical personal data stored. Aligns with typical data minimization principles under GDPR and supports operational review cycles. FERPA considerations are met by not storing direct PII within these logs (user identity is via hashed ID).
*   **Deletion Method:** Scheduled job (e.g., using `pg_cron` in Supabase) to delete rows older than 1 year. *Example SQL: `DELETE FROM conversations WHERE timestamp < NOW() - INTERVAL '1 year';`*

### 2. Performance Metrics (`performance_metrics` table)

*   **Purpose:** To monitor application health, performance trends, and identify bottlenecks.
*   **Retention Period:** **6 months** from the `timestamp` of the metric.
*   **Rationale:** Performance data is primarily needed for short to medium-term trend analysis and capacity planning. Older data becomes less relevant for operational decisions.
*   **Deletion Method:** Scheduled job to delete rows older than 6 months. *Example SQL: `DELETE FROM performance_metrics WHERE timestamp < NOW() - INTERVAL '6 months';`*

### 3. System Logs (`system_logs` table)

*   **Purpose:** To debug issues, investigate errors, and monitor system health.
*   **Retention Period:** **3 months** from the `timestamp` of the log.
*   **Rationale:** Critical for incident response and debugging. 3 months allows for sufficient time to investigate issues that might surface with a delay, while limiting storage of potentially sensitive operational data.
*   **Deletion Method:** Scheduled job to delete rows older than 3 months. *Example SQL: `DELETE FROM system_logs WHERE timestamp < NOW() - INTERVAL '3 months';`*

### 4. Knowledge Base Document Metadata (`knowledge_base_documents` table)

*   **Purpose:** To track the status and history of documents ingested into the RAG system.
*   **Retention Period:** **Indefinite** or until the corresponding source document is removed from the `data/` directory.
*   **Rationale:** This metadata is essential for managing the knowledge base and understanding the bot's information source. It is low-risk and directly tied to active data.
*   **Deletion Method:** Manual deletion when a source document is permanently removed from the `data/` directory, or via a script that cleans up metadata for non-existent source files.

### 5. Source Knowledge Base Documents (`data/` directory)

*   **Purpose:** To provide the bot with information to answer user queries.
*   **Retention Period:** **As long as the information is current and relevant to the bot's function.**
*   **Rationale:** These are the source documents. Their lifecycle is managed by the content owners (e.g., Admissions, Registrar). The bot's RAG system reflects the current state of these documents.
*   **Deletion Method:** Managed by content owners. When a document is removed, the `scripts/reindex_documents.py` script should be run to update the vector store and the `knowledge_base_documents` table will be updated accordingly.

## Deletion Procedures

1.  **Automated Deletion:** For conversation logs, performance metrics, and system logs, automated jobs (e.g., `pg_cron`) will execute the defined SQL `DELETE` statements based on the retention periods.
2.  **Verification:** The effectiveness of the automated deletion process should be periodically verified by checking table sizes and sample data timestamps.
3.  **Manual Deletion:** For exceptional circumstances (e.g., removal of specific user data upon request), manual deletion procedures will be followed, ensuring compliance with FERPA/GDPR rights (e.g., right to erasure). This will involve identifying and deleting related entries across relevant tables (e.g., all conversations for a specific `user_id` if it can be traced back to an individual, which it shouldn't be by design).
4.  **Secure Deletion:** Deletion from the database relies on the underlying database management system (Supabase/PostgreSQL). For physical media disposal (if applicable to the hosting provider), standard secure deletion protocols of the cloud provider apply.

## Compliance & Review

*   **Legal Review:** This policy should be reviewed by the institution's legal counsel to ensure full compliance with FERPA, GDPR, and any other applicable laws or regulations.
*   **Regular Review:** This policy will be reviewed annually or whenever there are significant changes to the bot's function, data processing, or relevant laws.
*   **Documentation:** Any changes to this policy will be documented and communicated to relevant staff (IT, operations, legal).