import streamlit as st
import numpy as np
import faiss
import os
import json
import pickle
from typing import List, Dict, Any, Tuple
from openai import OpenAI
try:
    import google.generativeai as genai
except ImportError:
    genai = None

class VectorStore:
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.index = None
        self.chunks = []
        self.metadata = {}
        
        if provider == "openai":
            # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
            # do not change this unless explicitly requested by the user
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
            else:
                self.openai_client = None
            self.embedding_model = "text-embedding-ada-002"
            self.dimension = 1536  # Ada-002 embedding dimension
            
        elif provider == "google":
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key and genai:
                try:
                    genai.configure(api_key=api_key)
                    self.google_client = genai
                except Exception:
                    self.google_client = genai
            else:
                self.google_client = None
            self.embedding_model = "models/embedding-001"  # Google's embedding model
            self.dimension = 768  # Google embedding dimension
        
    def add_document(self, chunks: List[Dict], metadata: Dict):
        """Add document chunks to vector store"""
        try:
            # Check if API client is available
            if self.provider == "openai" and not self.openai_client:
                raise Exception("OpenAI API key not configured. Please set your API key.")
            elif self.provider == "google" and not self.google_client:
                raise Exception("Google Gemini API key not configured. Please set your API key.")
            
            # Extract text from chunks
            texts = [chunk['text'] for chunk in chunks]
            
            # Generate embeddings
            embeddings = self._generate_embeddings(texts)
            
            # Create FAISS index
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to index
            self.index.add(embeddings)
            
            # Store chunks and metadata
            self.chunks = chunks
            self.metadata = metadata
            
            # Store provider info in metadata
            self.metadata['provider'] = self.provider
            
            # Save to disk
            self._save_to_disk(metadata['id'])
            
        except Exception as e:
            raise Exception(f"Error adding document to vector store: {str(e)}")
    
    def load_document(self, document_id: str):
        """Load document from disk"""
        try:
            # Load index
            index_path = f"data/vectors/{document_id}.faiss"
            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
            
            # Load chunks and metadata
            data_path = f"data/vectors/{document_id}.pkl"
            if os.path.exists(data_path):
                with open(data_path, 'rb') as f:
                    data = pickle.load(f)
                    self.chunks = data['chunks']
                    self.metadata = data['metadata']
                    
                    # Update provider if stored in metadata
                    if 'provider' in self.metadata:
                        self.provider = self.metadata['provider']
                        # Re-initialize the appropriate client
                        if self.provider == "openai":
                            api_key = os.getenv("OPENAI_API_KEY")
                            if api_key:
                                self.openai_client = OpenAI(api_key=api_key)
                        elif self.provider == "google":
                            api_key = os.getenv("GEMINI_API_KEY")
                            if api_key and genai:
                                try:
                                    genai.configure(api_key=api_key)
                                    self.google_client = genai
                                except Exception:
                                    self.google_client = genai
            
        except Exception as e:
            raise Exception(f"Error loading document from vector store: {str(e)}")
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Dict, float]]:
        """Search for relevant chunks"""
        try:
            if self.index is None:
                return []
                
            # Check if API client is available
            if self.provider == "openai" and not self.openai_client:
                raise Exception("OpenAI API key not configured for search.")
            elif self.provider == "google" and not self.google_client:
                raise Exception("Google Gemini API key not configured for search.")
            
            # Generate query embedding
            query_embedding = self._generate_embeddings([query])
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding, k)
            
            # Return results with chunks and scores
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.chunks):
                    results.append((self.chunks[idx], float(score)))
            
            return results
            
        except Exception as e:
            raise Exception(f"Error searching vector store: {str(e)}")
    
    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using the selected API provider"""
        try:
            if self.provider == "openai":
                if not self.openai_client:
                    raise Exception("OpenAI API key not configured")
                
                # Split into batches to handle API limits
                batch_size = 100
                all_embeddings = []
                
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    
                    response = self.openai_client.embeddings.create(
                        model=self.embedding_model,
                        input=batch
                    )
                    
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                
                return np.array(all_embeddings, dtype=np.float32)
                
            elif self.provider == "google":
                if not self.google_client:
                    raise Exception("Google Gemini API key not configured")
                
                # Google Gemini embedding generation
                all_embeddings = []
                
                try:
                    for text in texts:
                        # Use Google's embedding API
                        result = genai.embed_content(
                            model=self.embedding_model,
                            content=text
                        )
                        embedding = np.array(result['embedding'], dtype=np.float32)
                        all_embeddings.append(embedding)
                    
                    return np.array(all_embeddings, dtype=np.float32)
                
                except Exception as e:
                    # Fallback to a basic hash-based embedding for demo purposes
                    st.warning("Google embedding API not available, using fallback method")
                    all_embeddings = []
                    for text in texts:
                        # Simple hash-based embedding (for demo only)
                        import hashlib
                        hash_obj = hashlib.md5(text.encode())
                        hash_int = int(hash_obj.hexdigest(), 16)
                        np.random.seed(hash_int % 1000000)  # Use hash as seed for reproducibility
                        embedding = np.random.rand(self.dimension).astype(np.float32)
                        all_embeddings.append(embedding)
                    
                    
        except Exception as e:
            raise Exception(f"Error generating embeddings with {self.provider}: {str(e)}")
        
        # This should never be reached, but satisfies type checker
        return np.array([], dtype=np.float32)
    
    def _save_to_disk(self, document_id: str):
        """Save vector store to disk"""
        try:
            # Ensure directory exists
            os.makedirs("data/vectors", exist_ok=True)
            
            # Save FAISS index
            if self.index is not None:
                faiss.write_index(self.index, f"data/vectors/{document_id}.faiss")
            
            # Save chunks and metadata
            data = {
                'chunks': self.chunks,
                'metadata': self.metadata
            }
            
            with open(f"data/vectors/{document_id}.pkl", 'wb') as f:
                pickle.dump(data, f)
                
        except Exception as e:
            raise Exception(f"Error saving vector store: {str(e)}")
