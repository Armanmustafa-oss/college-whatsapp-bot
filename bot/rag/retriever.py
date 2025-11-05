"""
🔍 RAG Retrieval Orchestration Engine
=====================================
Manages the interaction between the main bot logic and the vector store,
performing semantic search and preparing context for the AI model.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from bot.rag.vector_store import VectorStore # Import the VectorStore class we created

logger = logging.getLogger(__name__)

class Retriever:
    """
    Acts as an interface between the main application and the VectorStore,
    handling retrieval logic, context formatting, and potential pre/post-processing.
    """

    def __init__(self, vector_store_path: str = "./chroma_db", collection_name: str = "college_knowledge_base"):
        """
        Initializes the Retriever by connecting to or creating the VectorStore.

        Args:
            vector_store_path (str): Path to the persistent vector store directory.
            collection_name (str): Name of the ChromaDB collection to query.
        """
        self.vector_store = VectorStore(persist_directory=vector_store_path, collection_name=collection_name)
        logger.info(f"Retriever initialized with VectorStore collection: {collection_name}")

    async def retrieve_async(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Asynchronously retrieves relevant context chunks for a given query.

        Args:
            query (str): The user's query string.
            top_k (int): Number of top context chunks to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing 'content', 'source', 'chunk_index', and 'distance'.
        """
        # In this case, ChromaDB's query is typically fast enough that making it truly async
        # might involve running it in a thread pool executor if it becomes a bottleneck.
        # For now, we treat the call as synchronous within an async wrapper.
        loop = asyncio.get_event_loop()
        # Use run_in_executor to potentially run the DB query in a separate thread if ChromaDB is slow
        # context_chunks = await loop.run_in_executor(None, self.vector_store.retrieve_context, query, top_k)
        # For simplicity and because ChromaDB is usually fast, we call it directly:
        context_chunks = self.vector_store.retrieve_context(query, top_k=top_k)
        logger.debug(f"RAG Retrieved {len(context_chunks)} chunks for query: '{query[:30]}...'")
        return context_chunks

    def retrieve_sync(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Synchronously retrieves relevant context chunks. Useful if called from a non-async context.

        Args:
            query (str): The user's query string.
            top_k (int): Number of top context chunks to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing 'content', 'source', 'chunk_index', and 'distance'.
        """
        context_chunks = self.vector_store.retrieve_context(query, top_k=top_k)
        logger.debug(f"RAG Retrieved {len(context_chunks)} chunks (sync) for query: '{query[:30]}...'")
        return context_chunks

    def get_knowledge_base_metadata(self) -> Dict[str, Any]:
        """
        Retrieves metadata about the knowledge base, e.g., last update time, number of documents.

        Returns:
            Dict[str, Any]: Metadata dictionary.
        """
        # This would require querying ChromaDB for collection info or maintaining a separate metadata file.
        # Example placeholder implementation:
        try:
            collection_info = self.vector_store.collection.count() # This gives count of embeddings
            metadata = {
                "document_count_estimate": collection_info, # Note: this is embedding count, not necessarily document count
                "last_ingestion_timestamp": "2024-01-01T00:00:00Z", # Placeholder, implement real tracking
                "model_used_for_embeddings": "all-MiniLM-L6-v2" # Placeholder
            }
        except Exception as e:
            logger.error(f"Error fetching knowledge base metadata: {e}")
            metadata = {"error": "Could not retrieve metadata"}
        return metadata

# Example usage (if run as main):
# import asyncio
# if __name__ == "__main__":
#     retriever = Retriever()
#     # Example synchronous call
#     sync_results = retriever.retrieve_sync("What are the tuition fees?")
#     print("Sync Results:", sync_results)
#
#     # Example asynchronous call
#     async def example_async():
#         async_results = await retriever.retrieve_async("How do I apply for financial aid?")
#         print("Async Results:", async_results)
#
#     asyncio.run(example_async())