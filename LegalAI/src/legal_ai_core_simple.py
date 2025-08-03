#!/usr/bin/env python3
import os
from pathlib import Path
import sys
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from ollama_client import OllamaClient

class LegalAI:
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.current_model = None
        # Simplified without ChromaDB and SentenceTransformer for now
        print("⚠️ LegalAI initialized in simplified mode (no vector database)")
    
    def retrieve_context(self, query: str):
        """Simplified context retrieval - returns basic legal context"""
        return f"Legal context for query: {query}\n\nThis is a simplified LegalAI implementation."
    
    def generate_response(self, query: str, context: str, mode: str = "research_memo", stream: bool = False):
        """Generate legal response using Ollama"""
        prompt = f"""You are a legal AI assistant. Please provide a helpful response to this legal question.

Question: {query}
Context: {context}

Please provide a clear, professional legal response:"""
        
        try:
            response = self.ollama_client.generate(prompt)
            return response
        except Exception as e:
            return f"Sorry, I encountered an error generating a response: {str(e)}"
    
    def search_cases(self, query: str):
        """Simplified case search"""
        return [{"summary": f"Simplified case result for: {query}", "relevance": 0.8}]

def query_legal_db(query: str):
    """Simplified legal database query"""
    legal_ai = LegalAI()
    context = legal_ai.retrieve_context(query)
    response = legal_ai.generate_response(query, context)
    return [{"query": query, "response": response, "relevance": 0.8}] 