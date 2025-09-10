import streamlit as st
import os
import json
from datetime import datetime, timedelta
import pandas as pd


from document_processor import DocumentProcessor
from vector_store import VectorStore
from chat_manager import ChatManager
from pdf_exporter import PDFExporter
# from theme_manager import ThemeManager
from utils import ensure_directories, format_file_size
from dotenv import load_dotenv
load_dotenv()

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.documents = []
    st.session_state.chat_history = []
    st.session_state.current_document = None
    st.session_state.vector_store = None
    st.session_state.theme = 'light'
    st.session_state.api_provider = 'google'  # Default to Google Generative AI
    st.session_state.api_configured = False
    st.session_state.current_page = 'Document Upload'  # Track current page


   
            
  
     
   
       
if __name__ == "__main__":
    main()

