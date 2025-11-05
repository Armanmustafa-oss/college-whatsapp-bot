"""
🧩 Advanced Knowledge Base & Vector Retrieval System
====================================================
Enterprise-grade Retrieval-Augmented Generation (RAG) system using ChromaDB
for semantic search and context provision to the AI model.
"""

import logging
import os
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from chromadb.api.types import QueryResult
from sentence_transformers import SentenceTransformer
import PyPDF2 # For PDF processing
import docx # For Word processing
from bot.config import ENVIRONMENT # For environment-specific settings

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Manages the ChromaDB collection, document ingestion, embedding, and retrieval.
    """

    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "college_knowledge_base"):
        """
        Initializes the VectorStore with ChromaDB client and a SentenceTransformer model.

        Args:
            persist_directory (str): Directory to persist the ChromaDB data.
            collection_name (str): Name of the ChromaDB collection.
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )
        # Load a pre-trained sentence transformer model for embeddings
        # Consider using a model fine-tuned for domain-specific tasks if available
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2') # Or a larger model like 'all-mpnet-base-v2'
        logger.info(f"VectorStore initialized with collection '{collection_name}' in '{persist_directory}'.")

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extracts text content from a PDF file."""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
        return text

    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extracts text content from a DOCX file."""
        text = ""
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {e}")
        return text

    def _extract_text_from_txt(self, file_path: str) -> str:
        """Extracts text content from a TXT file."""
        text = ""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except Exception as e:
            logger.error(f"Error reading TXT file {file_path}: {e}")
        return text

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Splits text into overlapping chunks for better retrieval."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        return chunks

    def _generate_document_id(self, content: str, source: str) -> str:
        """Generates a unique ID for a document chunk based on content and source."""
        # Create a hash of the content and source for a unique but deterministic ID
        content_hash = hashlib.md5(content.encode()).hexdigest()
        source_hash = hashlib.md5(source.encode()).hexdigest()
        return f"{source_hash[:8]}_{content_hash[:8]}"

    def ingest_documents(self, data_directory: str):
        """
        Ingests documents from a specified directory into the ChromaDB collection.
        Supports .pdf, .docx, .txt files.
        """
        logger.info(f"Starting ingestion from directory: {data_directory}")
        for filename in os.listdir(data_directory):
            file_path = os.path.join(data_directory, filename)
            if os.path.isfile(file_path):
                extension = os.path.splitext(filename)[1].lower()
                text = ""
                if extension == '.pdf':
                    text = self._extract_text_from_pdf(file_path)
                elif extension == '.docx':
                    text = self._extract_text_from_docx(file_path)
                elif extension == '.txt':
                    text = self._extract_text_from_txt(file_path)
                else:
                    logger.info(f"Skipping unsupported file type: {filename}")
                    continue

                if text.strip(): # Only process if text was extracted
                    logger.info(f"Processing file: {filename}")
                    chunks = self._chunk_text(text)
                    documents = []
                    metadatas = []
                    ids = []
                    for i, chunk in enumerate(chunks):
                        doc_id = self._generate_document_id(chunk, filename)
                        documents.append(chunk)
                        metadatas.append({"source": filename, "chunk_index": i})
                        ids.append(doc_id)

                    # Upsert documents into ChromaDB
                    self.collection.upsert(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    logger.info(f"Ingested {len(chunks)} chunks from {filename}")
                else:
                    logger.warning(f"No text extracted from {filename}")

        logger.info("Document ingestion complete.")

    def retrieve_context(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves the most relevant document chunks for a given query.

        Args:
            query (str): The user's query.
            top_k (int): Number of top results to retrieve.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing 'content', 'source', 'chunk_index', and 'distance'.
        """
        query_embedding = self.embedder.encode([query]).tolist()[0]
        results: QueryResult = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            # You can add filters here if needed, e.g., filter by source document
            # where={"source": "specific_file.pdf"}
        )

        # ChromaDB returns nested lists; extract the relevant information
        documents = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        distances = results['distances'][0] if results['distances'] else []

        context_list = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            context_list.append({
                "content": doc,
                "source": meta.get("source", "unknown"),
                "chunk_index": meta.get("chunk_index", -1),
                "distance": dist # Lower distance means more similar
            })

        logger.debug(f"Retrieved {len(context_list)} context chunks for query: '{query[:50]}...'")
        return context_list

# Example usage (if run as main):
# if __name__ == "__main__":
#     vs = VectorStore(persist_directory="./chroma_db_new", collection_name="my_college_kb")
#     # Ingest documents (run once)
#     # vs.ingest_documents("./data/")
#     # Retrieve context
#     context = vs.retrieve_context("What are the tuition fees for international students?")
#     print("Retrieved Context:", context)