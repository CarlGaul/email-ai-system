import os
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from ollama_client import OllamaClient
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

class LegalAI:
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.current_model = None
        self.vector_db_client = chromadb.PersistentClient(path=Config.VECTOR_DB_DIR)
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        self.collection = self.vector_db_client.get_or_create_collection(
            name="legal_documents",
            metadata={"hnsw:space": "cosine"}
        )
        Path(Config.VECTOR_DB_DIR).mkdir(parents=True, exist_ok=True)
        if self.collection.count() == 0:
            self.ingest_cases()

    def ingest_cases(self):
        """Ingest case files from /database/cases/nys"""
        print("🔍 Ingesting cases from /database/cases/nys...")
        case_dir = Path("/Users/carlgaul/Desktop/LegalAI/database/cases/nys")
        documents = []
        metadatas = []
        ids = []
        doc_counter = 0

        for root, _, files in os.walk(case_dir):
            for file in files:
                if file.endswith((".txt", ".pdf")) and not file.endswith(".pdf_metadata.json"):
                    file_path = os.path.join(root, file)
                    try:
                        if file.endswith(".txt"):
                            with open(file_path, 'r', encoding='utf-8') as f:
                                text = f.read()
                        elif file.endswith(".pdf") and PdfReader:
                            try:
                                reader = PdfReader(file_path)
                                text = "".join(page.extract_text() for page in reader.pages if page.extract_text())
                                if not text.strip():
                                    print(f"❌ Skipping {file_path}: No text extracted from PDF")
                                    continue
                            except Exception as pdf_error:
                                print(f"❌ Skipping {file_path}: Invalid PDF ({pdf_error})")
                                continue
                        else:
                            print(f"❌ Skipping {file_path}: PDF support requires PyPDF2")
                            continue
                        
                        chunks = self.chunk_text(text, Config.CHUNK_SIZE, Config.CHUNK_OVERLAP)
                        for i, chunk in enumerate(chunks):
                            category = os.path.basename(root)
                            doc_id = f"{category}_{file}_{doc_counter}_{i}"
                            doc_counter += 1
                            
                            metadata = {
                                "source": file_path,
                                "category": category,
                                "authority_level": Config.AUTHORITY_LEVELS.get(category, 12)
                            }
                            documents.append(chunk)
                            metadatas.append(metadata)
                            ids.append(doc_id)
                    except Exception as e:
                        print(f"❌ Error processing {file_path}: {e}")

        if documents:
            embeddings = self.embedding_model.encode(documents, batch_size=32, show_progress_bar=True)
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ Ingested {len(documents)} chunks into vector database")
        else:
            print("⚠️ No valid case files found in /database/cases/nys")

    def chunk_text(self, text: str, chunk_size: int, overlap: int) -> list:
        """Split text into chunks with overlap"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks

    def retrieve_context(self, query: str):
        """Retrieve relevant context from vector database"""
        query_embedding = self.embedding_model.encode([query])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            include=["documents", "metadatas"]
        )
        context = ""
        if results["documents"] and results["documents"][0]:
            for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
                context += f"Source: {metadata['source']}\n{doc}\n\n"
        else:
            context = "No relevant case law found in the database."
        return context

    def generate_response(self, query: str, context: str, mode: str = "research_memo", stream: bool = False):
        """Generate response with context from vector database"""
        print(f"🔍 DEBUG: User prompt created, length: {len(query)} characters")
        
        system_prompt = (
            "You are a legal assistant that provides accurate responses based solely on the provided case law from /database/cases/nys. "
            "Cite and quote only from the given context. Do not generate answers from external knowledge or hallucinate. "
            "If no relevant context is found, state: 'No relevant case law found in the database' and provide a general response without specific citations."
            f"\n\nContext:\n{context}"
        )
        
        print(f"🔍 DEBUG: System prompt created, length: {len(system_prompt)} characters")
        print(f"🔍 DEBUG: Total prompt length: {len(query) + len(system_prompt)} characters")
        print(f"🔍 DEBUG: About to call ollama_client.generate_response...")
        
        response = self.ollama_client.generate_response(
            model=Config.DEFAULT_OLLAMA_MODEL,
            prompt=query,
            system_prompt=system_prompt,
            stream=stream
        )
        
        return response
