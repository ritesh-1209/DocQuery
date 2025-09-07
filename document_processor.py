import streamlit as st
import fitz  # PyMuPDF
import markdown
from bs4 import BeautifulSoup
import uuid
import re
from datetime import datetime
from typing import Dict, List, Any


class DocumentProcessor:

    def __init__(self):
        self.chunk_size = 500  # tokens
        self.chunk_overlap = 50  # tokens

    def process_document(self, uploaded_file) -> Dict[str, Any]:
        """Process uploaded document and return chunks with metadata"""
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()

            if file_extension == 'pdf':
                text = self._extract_pdf_text(uploaded_file)
            elif file_extension == 'md':
                text = self._extract_markdown_text(uploaded_file)
            elif file_extension in ['html', 'htm']:
                text = self._extract_html_text(uploaded_file)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {file_extension}'
                }

            if not text.strip():
                return {
                    'success': False,
                    'error': 'No text content found in document'
                }

            # Create chunks
            chunks = self._create_chunks(text)

            # Create metadata
            metadata = {
                'id': str(uuid.uuid4()),
                'filename': uploaded_file.name,
                'file_type': file_extension,
                'processed_date': datetime.now().isoformat(),
                'total_chars': len(text),
                'total_chunks': len(chunks)
            }

            return {
                'success': True,
                'text': text,
                'chunks': chunks,
                'metadata': metadata
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _extract_pdf_text(self, uploaded_file) -> str:
        """Extract text from PDF file"""
        try:
            # Read PDF bytes
            pdf_bytes = uploaded_file.read()

            # Open PDF with PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
                text += "\n\n"  # Add page separator

            doc.close()
            return text

        except Exception as e:
            raise Exception(f"Error extracting PDF text: {str(e)}")

    def _extract_markdown_text(self, uploaded_file) -> str:
        """Extract text from Markdown file"""
        try:
            # Read as string
            content = uploaded_file.read().decode('utf-8')

            # Convert Markdown to HTML
            html = markdown.markdown(content)

            # Extract plain text from HTML
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()

            return text

        except Exception as e:
            raise Exception(f"Error extracting Markdown text: {str(e)}")

    def _extract_html_text(self, uploaded_file) -> str:
        """Extract text from HTML file"""
        try:
            # Read as string
            content = uploaded_file.read().decode('utf-8')

            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines
                      for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            raise Exception(f"Error extracting HTML text: {str(e)}")

    def _create_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Split text into chunks with overlap"""
        # Simple word-based chunking (approximating tokens)
        words = text.split()
        chunks = []

        chunk_size_words = self.chunk_size // 1.3  # Rough conversion from tokens to words
        overlap_words = self.chunk_overlap // 1.3

        for i in range(0, len(words), int(chunk_size_words - overlap_words)):
            chunk_words = words[i:i + int(chunk_size_words)]
            chunk_text = ' '.join(chunk_words)

            if chunk_text.strip():
                chunks.append({
                    'text':
                    chunk_text,
                    'chunk_id':
                    len(chunks),
                    'start_word':
                    i,
                    'end_word':
                    min(i + int(chunk_size_words), len(words)),
                    'word_count':
                    len(chunk_words)
                })

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)

        return text.strip()
