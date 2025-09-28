# app/services/multi_college_rag_service.py

import chromadb
from typing import Dict
from app.config import settings

class MultiCollegeRAGService:
    def __init__(self):
        # Initialize ChromaDB client (persistent)
        self.client = chromadb.PersistentClient(path="./instance/chroma")
        self.collections: Dict[str, chromadb.Collection] = {}

    def get_college_collection(self, college_id: str) -> chromadb.Collection:
        """
        Get or create a ChromaDB collection for a specific college.
        Collection name: college_{college_id}
        """
        if college_id not in self.collections:
            collection_name = f"college_{college_id}"
            try:
                # Try to get existing collection
                collection = self.client.get_collection(collection_name)
            except ValueError:
                # Create new collection if it doesn't exist
                collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            self.collections[college_id] = collection
        return self.collections[college_id]

    def add_documents_for_college(self, college_id: str, documents: list):
        """
        Add documents to a college's collection.
        `documents` should be a list of dicts with 'content', 'metadata', etc.
        """
        collection = self.get_college_collection(college_id)
        # TODO: Implement document chunking and embedding
        # This is a placeholder — you'll integrate with your existing ingestion logic
        pass

    def search_in_college(self, college_id: str, query: str, n_results: int = 3):
        """
        Search for relevant documents in a specific college's knowledge base.
        """
        collection = self.get_college_collection(college_id)
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
    
    