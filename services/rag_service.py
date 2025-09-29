import os
import chromadb
import json
import os
from typing import List, Dict
from PyPDF2 import PdfReader
import logging

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        # ... your existing init code ...
        try:
            self.collection = self.client.get_collection(self.collection_name)
            print("✅ Loaded existing ChromaDB collection")
        except (ValueError, chromadb.errors.InvalidCollectionException):
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print("🆕 Created new ChromaDB collection")
            self._load_dummy_data()  # ← This calls the method below

    def _load_dummy_data(self):
        """Load dummy college data into the vector database"""
        dummy_data = [
            {
                "id": "admission_1",
                "content": "To apply for admission, students need to submit their high school transcripts, passport copy, and English proficiency test scores (IELTS 6.0 or TOEFL 80). The application deadline is March 15th for Fall semester.",
                "category": "admission",
                "title": "Admission Requirements"
            },
            {
                "id": "immigration_1", 
                "content": "International students need a student visa to study in Cyprus. After receiving the acceptance letter, students should apply for a student visa at the nearest Cyprus consulate. Processing time is usually 4-6 weeks.",
                "category": "immigration",
                "title": "Student Visa Information"
            },
            {
                "id": "classes_1",
                "content": "Classes start in September for Fall semester and January for Spring semester. Each semester is 16 weeks long. Students must maintain a minimum GPA of 2.0 to remain in good academic standing.",
                "category": "classes",
                "title": "Academic Calendar"
            },
            {
                "id": "housing_1",
                "content": "The college provides on-campus dormitories for international students. Monthly rent is 400 EUR including utilities. Students can also find private accommodation near campus ranging from 300-600 EUR per month.",
                "category": "housing",
                "title": "Housing Options"
            },
            {
                "id": "fees_1",
                "content": "Tuition fees for international students are 8,500 EUR per year for undergraduate programs and 9,500 EUR per year for graduate programs. Payment can be made in installments.",
                "category": "fees",
                "title": "Tuition Fees"
            }
        ]
        
        # Add to ChromaDB
        self.collection.add(
            documents=[doc["content"] for doc in dummy_data],
            ids=[doc["id"] for doc in dummy_data],
            metadatas=[{
                "category": doc["category"],
                "title": doc["title"]
            } for doc in dummy_data]
        )
        print(f"📚 Loaded {len(dummy_data)} dummy documents")
    
    def search_documents(self, query: str, n_results: int = 3, filter_category: str = None):
        """
        Search for relevant documents based on user query.
        Optionally filter by category for faster, more relevant results.
        """
        try:
            # Build metadata filter
            where_clause = {"category": filter_category} if filter_category else None

            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause  # ← This speeds up search by limiting scope
            )

            documents = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    documents.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0
                    })
            return documents
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def add_pdf_document(self, pdf_path: str, category: str, title: str):
        """
        Add a PDF document to the knowledge base
        
        Args:
            pdf_path: Path to the PDF file
            category: Document category (admission, immigration, etc.)
            title: Document title
        """
        try:
            reader = PdfReader(pdf_path)
            text_content = ""
            
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
            
            # Split into chunks (simple approach - can be improved)
            chunks = self._split_text(text_content, chunk_size=500)
            
            for i, chunk in enumerate(chunks):
                doc_id = f"{category}_{title}_{i}".replace(" ", "_").lower()
                
                self.collection.add(
                    documents=[chunk],
                    ids=[doc_id],
                    metadatas=[{
                        "category": category,
                        "title": title,
                        "chunk_index": i
                    }]
                )
            
            logger.info(f"Added PDF document: {title} ({len(chunks)} chunks)")
            
        except Exception as e:
            logger.error(f"Error adding PDF document: {e}")
    
    def _split_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        Split text into chunks for better vector search
        
        Args:
            text: Full text to split
            chunk_size: Maximum characters per chunk
            
        Returns:
            List of text chunks
        """
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

# Global instance
rag_service = RAGService()