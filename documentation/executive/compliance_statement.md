# FERPA and GDPR Compliance Statement: AI College Support Bot

## Overview
This document outlines the commitment of [College Name] to ensuring that the AI College Support Bot ("the Bot") fully complies with the Family Educational Rights and Privacy Act (FERPA) and the General Data Protection Regulation (GDPR) regarding the handling of student data.

## FERPA Compliance
*   **Data Minimization:** The Bot is designed to collect and process only the minimum necessary information required to answer student queries. It does not request or store PII like SSNs or specific academic records.
*   **Purpose Limitation:** Data collected through interactions (e.g., phone numbers for identification, query content) is used solely for providing support and improving the bot's responses, strictly within the educational context.
*   **Access Control:** Access to conversation logs and performance data stored in Supabase is strictly controlled and limited to authorized personnel. Row-Level Security (RLS) is implemented.
*   **Data Retention:** A defined data retention policy exists (see `data_retention_policy.md`) ensuring student interaction data is kept only as long as necessary and then securely deleted.
*   **Security:** Data is transmitted and stored securely using industry-standard encryption (TLS, database encryption).

## GDPR Compliance
*   **Lawfulness, Fairness, Transparency:** The Bot's data processing is lawful under the legitimate interest of providing educational support. Users are informed about data use (likely via the college's general privacy policy).
*   **Purpose Limitation:** Consistent with FERPA, data use is limited to support purposes.
*   **Data Minimization:** Consistent with FERPA.
*   **Accuracy:** Mechanisms are in place to correct inaccuracies if identified (e.g., through user feedback).
*   **Storage Limitation:** Consistent with FERPA and the retention policy.
*   **Integrity and Confidentiality:** Consistent with FERPA's security measures.

## Conclusion
The AI College Support Bot has been architected and deployed with FERPA and GDPR compliance as fundamental requirements. Regular audits and reviews ensure continued adherence to these critical privacy regulations.