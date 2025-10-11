# app/services/rag_service.py
import chromadb
import os
from typing import List, Dict
from PyPDF2 import PdfReader
import logging
from chromadb.errors import InvalidCollectionException

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection_name = "college_documents"
        try:
            self.collection = self.client.get_collection(self.collection_name)
            logger.info("Loaded existing ChromaDB collection")
        except (ValueError, InvalidCollectionException):
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Created new ChromaDB collection")
            self._load_all_documents()

    def _load_dummy_data(self):
        """Load dummy college data into the vector database"""
        return [
            {
                "id": "admission_1",
                "content": "To apply for admission, students need to submit their high school transcripts, passport copy, and English proficiency test scores.",
                "category": "admission",
                "title": "Admission Requirements"
            },
            {
                "id": "immigration_1",
                "content": "International students need a student visa to study in Cyprus. After receiving the acceptance letter, apply at the nearest embassy.",
                "category": "immigration",
                "title": "Student Visa Information"
            },
            {
                "id": "classes_1",
                "content": "Classes start in September for Fall semester and January for Spring semester. Each semester is 16 weeks long.",
                "category": "classes",
                "title": "Academic Calendar"
            },
            {
                "id": "housing_1",
                "content": "The college provides on-campus dormitories for international students. Monthly rent is 400 EUR including utilities.",
                "category": "housing",
                "title": "Housing Options"
            },
            {
                "id": "fees_1",
                "content": "Tuition fees for international students are 8,500 EUR per year for undergraduate programs and 9,500 EUR for postgraduate.",
                "category": "fees",
                "title": "Tuition Fees"
            }
        ]

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a single PDF file"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            return ""

    def _split_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks for better vector search"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1  # +1 for space
            if current_length >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def _load_all_documents(self):
        """Load both dummy data AND real PDFs from data/college_docs/"""
        all_docs = []

        # 1. Add dummy data (always included)
        all_docs.extend(self._load_dummy_data())

        # 2. Add real PDFs
        pdf_dir = "data/college_docs"
        if os.path.exists(pdf_dir):
            for filename in os.listdir(pdf_dir):
                if filename.lower().endswith(".pdf"):
                    pdf_path = os.path.join(pdf_dir, filename)
                    logger.info(f"Loading PDF: {filename}")
                    text = self._extract_text_from_pdf(pdf_path)
                    if text.strip():
                        chunks = self._split_text(text, chunk_size=500)
                        title = os.path.splitext(filename)[0]
                        for i, chunk in enumerate(chunks):
                            doc_id = f"{title}_{i}".replace(" ", "_").lower()
                            all_docs.append({
                                "id": doc_id,
                                "content": chunk,
                                "category": "general",
                                "title": title
                            })
        else:
            logger.warning(f"PDF directory not found: {pdf_dir}")

        # 3. Add all documents to ChromaDB
        if all_docs:
            self.collection.add(
                documents=[doc["content"] for doc in all_docs],
                ids=[doc["id"] for doc in all_docs],
                metadatas=[{
                    "category": doc["category"],
                    "title": doc["title"]
                } for doc in all_docs]
            )
            logger.info(f"Loaded {len(all_docs)} documents into ChromaDB (dummy + PDFs)")
        else:
            logger.warning("No documents loaded into ChromaDB")

    # In rag_service.py, replace search_documents
    def search_documents(self, query: str, n_results: int = 3) -> List[Dict]:
        from app.services.semantic_enhancer import SemanticEnhancer
        enhancer = SemanticEnhancer()
        queries = enhancer.expand_query(query)
    
        all_results = []
        for q in queries:
            try:
                results = self.collection.query(query_texts=[q], n_results=n_results)
                if results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        all_results.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 1.0
                    })
            except Exception as e:
                continue
    
    # Sort by distance (relevance) and return top n_results
        all_results.sort(key=lambda x: x["distance"])
        return all_results[:n_results]


# Global instance (required for blueprint-style imports)
rag_service = RAGService()