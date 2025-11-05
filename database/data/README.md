# Knowledge Base Data

This directory contains the source documents used to populate the bot's knowledge base for the RAG system.

## Ingested Files

*   `college_info.pdf`: General information about the college.
*   `tuition_fees.pdf`: Detailed tuition and fee structures.
*   `programs.pdf`: List of available academic programs and majors.
*   `faq.txt`: Frequently asked questions and answers.

## Process

1.  Place new documents here.
2.  Run the `scripts/reindex_documents.py` script to process and index them into the vector store (ChromaDB).
3.  The `database/migrations/v2_enterprise_schema.sql` ensures metadata about these documents is tracked in the `knowledge_base_documents` table.