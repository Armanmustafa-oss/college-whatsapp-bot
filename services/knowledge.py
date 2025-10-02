# app/services/knowledge.py
from sentence_transformers import SentenceTransformer
import os
import chromadb
from chromadb.utils import embedding_functions
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class KnowledgeBase:
    def __init__(self, persist_directory="./instance/chroma"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Use free embedding model (no API key needed)
        self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="college_docs",
            embedding_function=self.embedding_func,
            metadata={"hnsw:space": "cosine"}
        )
        self._load_pdfs()

    def _load_pdfs(self):
        """Load all PDFs from data/college_docs/"""
        pdf_dir = "data/college_docs"
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
            # Add sample PDF content
            self._create_sample_docs()
            return

        for filename in os.listdir(pdf_dir):
            if filename.endswith(".pdf"):
                self._ingest_pdf(os.path.join(pdf_dir, filename))

    def _create_sample_docs(self):
        """Create sample college documents"""
        sample_docs = [
            ("Admission.pdf", "To apply for admission, students need high school transcripts, passport copy, and English test scores (IELTS 6.0). Deadline: March 15."),
            ("Visa.pdf", "International students need a student visa. Apply at Cyprus consulate after acceptance. Processing: 4-6 weeks."),
            ("Classes.pdf", "Classes start in September (Fall) and January (Spring). Maintain 2.0 GPA to stay in good standing.")
        ]
        
        for filename, content in sample_docs:
            with open(f"data/college_docs/{filename}", "w") as f:
                f.write(content)

    def _ingest_pdf(self, pdf_path):
        """Extract text from PDF and add to ChromaDB"""
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(text)
        
        # Add to ChromaDB
        ids = [f"{os.path.basename(pdf_path)}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": os.path.basename(pdf_path)} for _ in chunks]
        
        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
        print(f"✅ Ingested {len(chunks)} chunks from {pdf_path}")

    def search(self, query: str, n_results: int = 3):
        """Search for relevant documents"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results