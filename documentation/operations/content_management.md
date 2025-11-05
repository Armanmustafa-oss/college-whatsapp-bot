# Content Management Guide for the Bot Knowledge Base

## Overview
This document explains how to update the information the bot uses to answer questions, ensuring accuracy and relevance. The bot's knowledge is sourced from documents in the `data/` directory.

## Location of Source Documents
The bot's knowledge is sourced from documents stored in the `data/` directory of the application repository:
`/path/to/college-whatsapp-bot/data/`

## Supported Document Types
*   **PDF:** Text-based PDFs are preferred for detailed information (e.g., `college_comprehensive_info.pdf`).
*   **TXT:** Simple text files for frequently updated lists or specific Q&As (e.g., `faq.txt`).

## Updating the Knowledge Base

### 1. Obtain Updated Content
*   Acquire the latest, official, and approved content from the relevant department (e.g., Admissions, Registrar, Finance).
*   Ensure the content is FERPA/GDPR compliant (no PII).

### 2. Prepare the Document
*   Format the document clearly with headings and subheadings if possible (especially for PDFs).
*   Save it in a supported format (PDF, TXT).
*   **CRITICAL:** If replacing an existing file, the *filename must remain exactly the same* for the re-indexing script to correctly identify and update it.

### 3. Replace or Add the File
*   Navigate to the `data/` directory on the server or in the code repository.
*   **Replace** the existing file (e.g., `college_comprehensive_info.pdf`) with the new version, keeping the *exact same filename*.
    *   OR **Add** a new file if it's supplementary content (e.g., a new FAQ section in `faq.txt`).

### 4. Re-index the Knowledge Base (Critical Step)
*   **Run the `scripts/reindex_documents.py` script.** This script is essential. It reads the updated/added files from the `data/` directory, processes them (extracts text, chunks, embeds), and updates the vector store (ChromaDB) and the `knowledge_base_documents` table in Supabase.
    *   **Command:** `python scripts/reindex_documents.py` (Run from the project root directory).
    *   **Ensure the script runs to completion.** Monitor its output for any errors.
*   **Verify:** Check the bot's responses related to the updated content to ensure it reflects the changes. Test specific queries that should now yield information from the new/updated document.

## Important Notes
*   **Accuracy:** Only official, approved content should be added.
*   **File Naming:** Consistent and descriptive file names are important for management. Crucially, replacing a file *requires* the same filename.
*   **Version Control:** While the system tracks document checksums, internal departmental version control is also recommended.
*   **Testing:** After re-indexing, perform spot checks to confirm the bot provides correct answers based on the new data.
*   **Permissions:** Ensure the application process has read access to the `data/` directory and write access to the ChromaDB directory and Supabase.