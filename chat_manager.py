import streamlit as st
import os
from typing import Dict, List, Any, Optional
from openai import OpenAI
try:
    import google.generativeai as genai
except ImportError:
    genai = None

class ChatManager:
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.max_context_length = 8000
        
        if provider == "openai":
            # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
            # do not change this unless explicitly requested by the user
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                self.model = "gpt-5"
            else:
                self.openai_client = None
                self.model = None
        elif provider == "google":
            # Note that the newest Gemini model series is "gemini-2.5-flash" or gemini-2.5-pro"
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key and genai:
                try:
                    genai.configure(api_key=api_key)
                    self.google_client = genai
                    self.model = "gemini-2.5-flash"
                except Exception:
                    # Fallback to available model
                    self.google_client = genai
                    self.model = "gemini-pro"
            else:
                self.google_client = None
                self.model = None
    
    def get_response(self, query: str, vector_store, document_info: Dict) -> Dict[str, Any]:
        """Generate response using RAG approach"""
        try:
            # Check if API client is available
            if self.provider == "openai" and not self.openai_client:
                return {
                    'answer': "OpenAI API key not configured. Please set your API key in the settings.",
                    'sources': []
                }
            elif self.provider == "google" and not self.google_client:
                return {
                    'answer': "Google Gemini API key not configured. Please set your API key in the settings.",
                    'sources': []
                }
            
            # Retrieve relevant chunks
            search_results = vector_store.search(query, k=5)
            
            if not search_results:
                return {
                    'answer': "I couldn't find relevant information in the document to answer your question.",
                    'sources': []
                }
            
            # Prepare context and sources
            context_chunks = []
            sources = []
            
            for chunk, score in search_results:
                context_chunks.append(chunk['text'])
                sources.append(f"Chunk {chunk['chunk_id']}: \"{chunk['text'][:100]}...\" (Relevance: {score:.2f})")
            
            context = "\n\n".join(context_chunks)
            
            # Create system prompt
            system_prompt = f"""You are an AI assistant helping users understand a document titled "{document_info['filename']}".

You will be provided with relevant excerpts from the document and a user question. Your task is to:
1. Answer the question based ONLY on the provided context
2. Be accurate and specific
3. If the context doesn't contain enough information to answer the question, say so clearly
4. Cite specific parts of the context when possible
5. Keep your answer concise but comprehensive

Document context:
{context}

Remember: Only use information from the provided context. Do not add information from your general knowledge."""
            
            answer = ""
            if self.provider == "openai":
                # Generate response with OpenAI
                if self.openai_client and self.model:
                    response = self.openai_client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Question: {query}"}
                        ],
                        max_tokens=1000,
                        temperature=0.1
                    )
                    answer = response.choices[0].message.content or "No response generated."
                else:
                    answer = "OpenAI not properly configured."
                
            elif self.provider == "google":
                # Generate response with Google Gemini
                if self.google_client and self.model:
                    try:
                        prompt = f"{system_prompt}\n\nQuestion: {query}"
                        model = self.google_client.GenerativeModel(self.model)
                        response = model.generate_content(prompt)
                        answer = response.text or "I couldn't generate a response."
                    except Exception as e:
                        answer = f"Google Gemini error: {str(e)}"
                else:
                    answer = "Google Gemini not properly configured."
            
            return {
                'answer': answer,
                'sources': sources,
                'context_used': len(context_chunks)
            }
            
        except Exception as e:
            return {
                'answer': f"I encountered an error while processing your question: {str(e)}",
                'sources': []
            }
    
    def get_follow_up_response(self, query: str, chat_history: List[Dict], vector_store, document_info: Dict) -> Dict[str, Any]:
        """Generate response with chat history context"""
        try:
            # Check if API client is available
            if self.provider == "openai" and not self.openai_client:
                return {
                    'answer': "OpenAI API key not configured. Please set your API key in the settings.",
                    'sources': []
                }
            elif self.provider == "google" and not self.google_client:
                return {
                    'answer': "Google Gemini API key not configured. Please set your API key in the settings.",
                    'sources': []
                }
            
            # Retrieve relevant chunks
            search_results = vector_store.search(query, k=5)
            
            # Prepare context
            context_chunks = []
            sources = []
            
            for chunk, score in search_results:
                context_chunks.append(chunk['text'])
                sources.append(f"Chunk {chunk['chunk_id']}: \"{chunk['text'][:100]}...\" (Relevance: {score:.2f})")
            
            context = "\n\n".join(context_chunks)
            
            # Prepare chat history
            history_text = ""
            for msg in chat_history[-5:]:  # Last 5 messages for context
                if msg['role'] == 'user':
                    history_text += f"User: {msg['content']}\n"
                elif msg['role'] == 'assistant':
                    history_text += f"Assistant: {msg['content']}\n"
            
            # Create system prompt with history
            system_prompt = f"""You are an AI assistant helping users understand a document titled "{document_info['filename']}".

Previous conversation:
{history_text}

Current document context:
{context}

Answer the user's follow-up question based on the document context and previous conversation. Maintain consistency with previous responses while providing accurate information from the document."""
            
            answer = ""
            if self.provider == "openai":
                # Generate response with OpenAI
                if self.openai_client and self.model:
                    response = self.openai_client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Follow-up question: {query}"}
                        ],
                        max_tokens=1000,
                        temperature=0.1
                    )
                    answer = response.choices[0].message.content or "No response generated."
                else:
                    answer = "OpenAI not properly configured."
                
            elif self.provider == "google":
                # Generate response with Google Gemini
                if self.google_client and self.model:
                    try:
                        prompt = f"{system_prompt}\n\nFollow-up question: {query}"
                        model = self.google_client.GenerativeModel(self.model)
                        response = model.generate_content(prompt)
                        answer = response.text or "I couldn't generate a response."
                    except Exception as e:
                        answer = f"Google Gemini error: {str(e)}"
                else:
                    answer = "Google Gemini not properly configured."
            
            return {
                'answer': answer,
                'sources': sources,
                'context_used': len(context_chunks)
            }
            
        except Exception as e:
            return {
                'answer': f"I encountered an error while processing your question: {str(e)}",
                'sources': []
            }
