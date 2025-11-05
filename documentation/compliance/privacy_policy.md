# Privacy Policy: AI College Support Bot

## Overview
This Privacy Policy explains how [College Name] ("we", "us", "our") collects, uses, and safeguards information obtained through the AI College Support Bot ("Bot", "Service"), accessible via WhatsApp. This policy is designed to be clear, transparent, and compliant with applicable privacy laws, including the Family Educational Rights and Privacy Act (FERPA) and the General Data Protection Regulation (GDPR), where applicable.

## Information We Collect

The Bot is designed to operate with minimal collection of personal information, focusing on providing support based on the query itself and general context.

1.  **Information You Provide:**
    *   **Your Query:** The primary information collected is the text of your message sent to the Bot via WhatsApp (e.g., "What are the tuition fees?").
    *   **Your WhatsApp Number:** The Bot receives your WhatsApp number (e.g., `whatsapp:+1234567890`) from Twilio as part of the incoming message webhook. This number is used solely for:
        *   Identifying your session with the Bot.
        *   Sending the response back to your WhatsApp account.
        *   **Crucially, this number is NOT stored in its raw form in our operational database (`conversations` table). Instead, it is immediately processed into a non-reversible hash (e.g., SHA256) which is stored as the `user_id`. This significantly enhances privacy.**

2.  **Information Automatically Collected:**
    *   **Timestamp:** The date and time your message was received.
    *   **Response Context:** Information retrieved by the Bot's RAG system from our internal knowledge base documents to answer your query. This context is derived from our public-facing college information and does not contain your personal data.
    *   **Classification Data:** The Bot may classify your query's intent (e.g., 'admissions', 'fees') and sentiment (e.g., 'neutral', 'positive') internally for operational purposes (like improving responses or monitoring bot health). This classification is based on your query text and is not linked to your identity beyond the hashed `user_id`.
    *   **Technical Data:** Standard server logs may capture general information like the IP address of the request originator (Twilio's servers) for security and operational purposes, but this is not linked to individual users within our Bot application logs.

## How We Use Your Information

The information collected is used solely for the following operational purposes related to the Bot's core function:

1.  **To Provide Support:** To understand your question and generate a relevant response using our knowledge base and AI.
2.  **To Operate the Service:** To process your request, manage your session, and deliver the response via WhatsApp.
3.  **To Improve the Service:** To analyze common queries, assess bot performance (response time, accuracy), and refine the knowledge base and AI prompts. This analysis is performed on aggregated or anonymized data where possible (e.g., using the hashed `user_id`, not your phone number).
4.  **To Ensure Security and Compliance:** To monitor for abuse (e.g., spam), investigate errors, and ensure the service operates securely and in line with our policies and applicable laws.

## Information Sharing

We do **not** sell, rent, or trade your personal information collected through the Bot.

*   **Service Providers:** We use third-party services essential for the Bot's operation:
    *   **Twilio:** Facilitates communication via WhatsApp. Your phone number is shared with Twilio as part of the standard WhatsApp Business API flow, subject to Twilio's own privacy policy.
    *   **Supabase:** Hosts our database where anonymized conversation logs (using hashed `user_id`) are stored.
    *   **Groq:** Provides the AI processing power. Your query text (not your phone number) may be sent to Groq's API to generate a response, subject to Groq's privacy policy.
    *   **Sentry:** Used for error tracking and performance monitoring. Error logs may contain technical details but are configured to avoid capturing sensitive personal data like raw user messages or phone numbers. We have configured Sentry to scrub potential identifiers.
    *   These providers are contractually obligated to protect your data and use it only for providing the requested service.
*   **Legal Requirements:** We may disclose information if required to do so by law or in response to valid requests by public authorities (e.g., a court or government agency) as required by FERPA, GDPR, or other applicable laws. This would typically involve providing data to our institution's main administrative systems, not direct sharing from the bot's database which holds anonymized data.

## Data Retention

We retain the information collected through the Bot only as long as necessary for the purposes outlined in this policy or as required by law.

*   Your conversation log (including the hashed `user_id`, your query, the bot's response, and metadata like timestamp and intent) is retained in our Supabase database for a maximum of **1 year** before being automatically deleted, in accordance with our Data Retention Policy.
*   Performance and system logs are retained for a shorter period (e.g., 3-6 months).

## Your Rights (GDPR)

If you are located in the European Economic Area (EEA) or Switzerland, you may have certain rights regarding your personal data processed by this Bot:

*   **Right of Access:** You can request confirmation of whether we process your personal data and, if so, access to that data.
*   **Right to Rectification:** You can request correction of inaccurate personal data.
*   **Right to Erasure (Right to be Forgotten):** You can request deletion of your personal data under certain circumstances. *Note: Due to the anonymized nature of data storage (hashed `user_id`), direct deletion of specific conversation logs linked back to your identity *via the hash* might be challenging. However, we will consider requests and respond according to our capabilities and legal obligations. The primary mechanism for data minimization is our defined retention periods.*
*   **Right to Restriction of Processing:** In certain cases, you can request that we limit the way we process your data.
*   **Right to Data Portability:** You may have the right to receive your personal data in a structured, commonly used, and machine-readable format.
*   **Right to Object:** You can object to the processing of your personal data under certain conditions.

To exercise these rights, please contact us using the details provided below. Please note that these rights may be limited in the context of an educational support service and the anonymized data processing described here.

## FERPA Considerations

*   This Bot is designed to operate independently of your educational records held by the college. It answers questions based on a public-facing knowledge base.
*   The Bot does not access, process, or store your official educational record information (as defined by FERPA).
*   The hashed identifier (`user_id`) does not directly link to your educational record within the Bot's database.

## Security

We implement appropriate technical and organizational measures to protect the information collected by the Bot against unauthorized access, alteration, disclosure, or destruction. This includes secure transmission (TLS) and storage practices within our database and the use of reputable cloud service providers.

## Changes to This Policy

We may update this Privacy Policy from time to time. Any changes will be posted on this page, and the "Last Updated" date will be revised. Your continued use of the Bot after the changes become effective constitutes your acceptance of the updated policy.

## Contact Us

If you have questions about this Privacy Policy, the practices of this Bot, or your rights regarding your data, please contact:

[College Name] - [Department/Office Responsible for the Bot]
[Contact Email Address]
[Contact Phone Number]

Last Updated: [Date]