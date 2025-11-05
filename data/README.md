# Knowledge Base Data (`data/`)

This directory houses the source document powering the bot's "brain" via the RAG (Retrieval-Augmented Generation) system. The quality, accuracy, and structure of this document directly impact the bot's ability to provide helpful and reliable answers.

## Core Document

The primary source for the bot's knowledge is:

*   **`college_comprehensive_info.pdf`**: A single, comprehensive PDF containing all essential information about the college, including:
    *   General information (mission, history, values)
    *   Tuition and fees breakdown
    *   Academic programs offered
    *   Campus life details
    *   Admissions requirements
    *   Frequently asked questions and answers
    *   Contact information for key departments

## Document Requirements & Best Practices

*   **Format:** The PDF must be text-based (not a scanned image) to allow for accurate text extraction by the RAG system.
*   **Content:** Content must be official, up-to-date, reviewed by relevant departments, and compliant with FERPA/GDPR (no embedded PII).
*   **Clarity:** Use clear, concise language. Headings and subheadings are crucial for the RAG system to retrieve relevant sections effectively.
*   **File Naming:** Use a descriptive, consistent name (e.g., `college_info_comprehensive_[year].pdf`).

## Updating the Knowledge Base

1.  **Acquire/Update Document:** Obtain the latest, official version of the comprehensive college information PDF.
2.  **Review:** Ensure the document meets the format and content requirements listed above.
3.  **Replace File:** Replace the existing `college_comprehensive_info.pdf` in this directory with the new version. Ensure the *filename remains exactly the same*.
4.  **Re-index:** Run the `scripts/reindex_documents.py` script. This script will:
    *   Read the new/updated PDF file.
    *   Process and embed the text using the system defined in `bot/rag/vector_store.py`.
    *   Store the embeddings in the vector database (ChromaDB).
    *   Update the `knowledge_base_documents` table in Supabase with metadata about the updated document.
5.  **Verify:** Test the bot to ensure it correctly retrieves and responds based on the updated information.

## Security & Compliance

*   **Access Control:** Access to this directory during the development and deployment process should be restricted.
*   **PII:** Ensure no PII is embedded within the document.
*   **Retention:** While the document itself is stored here, the bot's *interactions* with users are logged in Supabase with appropriate retention policies defined in the database schema (`database/migrations/v2_enterprise_schema.sql`).