import streamlit as st
import os
import json
from datetime import datetime, timedelta
import pandas as pd


from document_processor import DocumentProcessor
from vector_store import VectorStore
from chat_manager import ChatManager
from pdf_exporter import PDFExporter
from theme_manager import ThemeManager
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
    st.session_state.api_provider = 'openai'  # Default to OpenAI
    st.session_state.api_configured = False
    st.session_state.current_page = 'Document Upload'  # Track current page

# Ensure required directories exist
ensure_directories()

# Initialize components based on selected API provider
doc_processor = DocumentProcessor()
try:
    chat_manager = ChatManager(provider=st.session_state.api_provider)
    api_available = True
except Exception as e:
    chat_manager = None
    api_available = False

pdf_exporter = PDFExporter()
theme_manager = ThemeManager()

# Apply theme (ensure it's applied on every run)
theme_manager.apply_theme(st.session_state.theme)

def main():
    # Apply theme first thing in main function
    theme_manager.apply_theme(st.session_state.theme)
    
    st.title("🔍 DocQuery")
    
    # Sidebar with theme toggle and navigation
    with st.sidebar:
        st.header("Settings")
        
        # API Provider Selection
        st.subheader("🔧 API Configuration")
        provider_options = {
            "openai": "OpenAI (GPT-5 + Ada Embeddings)",
            "google": "Google Gemini (Gemini 2.5 + Embeddings)"
        }
        
        selected_provider = st.selectbox(
            "Choose AI Provider",
            options=list(provider_options.keys()),
            format_func=lambda x: provider_options[x],
            index=0 if st.session_state.api_provider == 'openai' else 1
        )
        
        if selected_provider != st.session_state.api_provider:
            st.session_state.api_provider = selected_provider
            st.rerun()
        
        # API Key Status
        if st.session_state.api_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                st.success("✅ OpenAI API Key configured")
                st.session_state.api_configured = True
            else:
                st.error("❌ OpenAI API Key not set")
                st.info("Please set your OPENAI_API_KEY to use this system.")
                st.session_state.api_configured = False
                
        elif st.session_state.api_provider == "google":
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                st.success("✅ Google Gemini API Key configured")
                st.session_state.api_configured = True
            else:
                st.error("❌ Google Gemini API Key not set")
                st.info("Please set your GEMINI_API_KEY to use this system.")
                st.session_state.api_configured = False
        
        st.markdown("---")
        
        # Theme toggle with current theme indicator
        # current_theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"
        # theme_text = f"{current_theme_icon} {st.session_state.theme.title()} Theme"
        
        # if st.button(theme_text, use_container_width=True):
        #     st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
        #     st.rerun()
        
        # st.header("Navigation")
        
        # Individual tab buttons instead of dropdown
        if st.button("📄 Document Upload", use_container_width=True, type="primary" if st.session_state.current_page == "Document Upload" else "secondary"):
            st.session_state.current_page = "Document Upload"
            st.rerun()
            
        if st.button("💬 Chat Interface", use_container_width=True, type="primary" if st.session_state.current_page == "Chat Interface" else "secondary"):
            st.session_state.current_page = "Chat Interface"
            st.rerun()
            
        if st.button("📚 Document History", use_container_width=True, type="primary" if st.session_state.current_page == "Document History" else "secondary"):
            st.session_state.current_page = "Document History"
            st.rerun()
            
        if st.button("💭 Chat History", use_container_width=True, type="primary" if st.session_state.current_page == "Chat History" else "secondary"):
            st.session_state.current_page = "Chat History"
            st.rerun()
        
        page = st.session_state.current_page
    
    if page == "Document Upload":
        document_upload_page()
    elif page == "Chat Interface":
        chat_interface_page()
    elif page == "Document History":
        document_history_page()
    elif page == "Chat History":
        chat_history_page()

def document_upload_page():
    st.header("📄 Document Upload")
    
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=['pdf', 'md', 'html', 'htm'],
        help="Upload PDF, Markdown, or HTML files"
    )
    
    if uploaded_file is not None:
        with st.spinner("Processing document..."):
            try:
                # Check if API is configured
                if not st.session_state.api_configured:
                    st.error(f"❌ Please configure your {st.session_state.api_provider.upper()} API key first!")
                    return
                
                # Process the document
                result = doc_processor.process_document(uploaded_file)
                
                if result['success']:
                    # Create vector store with selected provider
                    vector_store = VectorStore(provider=st.session_state.api_provider)
                    vector_store.add_document(result['chunks'], result['metadata'])
                    
                    # Save document info
                    doc_info = {
                        'id': result['metadata']['id'],
                        'filename': uploaded_file.name,
                        'file_type': uploaded_file.type,
                        'upload_date': datetime.now().isoformat(),
                        'size': format_file_size(len(uploaded_file.getvalue())),
                        'chunks_count': len(result['chunks']),
                        'metadata': result['metadata']
                    }
                    
                    st.session_state.documents.append(doc_info)
                    st.session_state.vector_store = vector_store
                    st.session_state.current_document = doc_info
                    
                    # Save to persistent storage
                    save_document_info(doc_info)
                    
                    st.success(f"✅ Document processed successfully! Generated {len(result['chunks'])} chunks.")
                    
                    # Display document info
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("File Size", doc_info['size'])
                    with col2:
                        st.metric("Chunks", doc_info['chunks_count'])
                    with col3:
                        st.metric("Type", uploaded_file.type.split('/')[-1].upper())
                    
                    st.info("💡 You can now go to the Chat Interface to ask questions about this document!")
                    
                else:
                    st.error(f"❌ Error processing document: {result['error']}")
                    
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")

def chat_interface_page():
    st.header("💬 Chat Interface")
    
    if not st.session_state.api_configured:
        st.error(f"❌ Please configure your {st.session_state.api_provider.upper()} API key in the sidebar first!")
        return
    
    if st.session_state.current_document is None:
        st.warning("⚠️ Please upload a document first to start chatting!")
        return
    
    # Display current document info
    doc = st.session_state.current_document
    st.info(f"📖 Currently chatting about: **{doc['filename']}** ({doc['chunks_count']} chunks)")
    
    # Chat interface
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message:
                with st.expander("📚 Sources"):
                    for i, source in enumerate(message["sources"], 1):
                        st.markdown(f"**Source {i}:** {source}")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about the document..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Re-initialize chat manager with current provider if needed
                    if chat_manager is None or not hasattr(chat_manager, 'provider') or chat_manager.provider != st.session_state.api_provider:
                        current_chat_manager = ChatManager(provider=st.session_state.api_provider)
                    else:
                        current_chat_manager = chat_manager
                        
                    response = current_chat_manager.get_response(
                        prompt, 
                        st.session_state.vector_store,
                        st.session_state.current_document
                    )
                    
                    st.markdown(response['answer'])
                    
                    # Display sources
                    if response['sources']:
                        with st.expander("📚 Sources"):
                            for i, source in enumerate(response['sources'], 1):
                                st.markdown(f"**Source {i}:** {source}")
                    
                    # Add assistant message
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response['answer'],
                        "sources": response['sources']
                    })
                    
                    # Save chat history
                    chat_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'document_id': st.session_state.current_document['id'],
                        'document_name': st.session_state.current_document['filename'],
                        'question': prompt,
                        'answer': response['answer'],
                        'sources': response['sources']
                    }
                    st.session_state.chat_history.append(chat_entry)
                    save_chat_history(chat_entry)
                    
                except Exception as e:
                    st.error(f"❌ Error generating response: {str(e)}")
    
    # Export chat option
    if st.session_state.messages:
        if st.button("📄 Export Chat to PDF"):
            with st.spinner("Generating PDF..."):
                try:
                    pdf_path = pdf_exporter.export_chat(
                        st.session_state.messages,
                        st.session_state.current_document['filename']
                    )
                    
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="⬇️ Download Chat PDF",
                            data=pdf_file.read(),
                            file_name=f"chat_{st.session_state.current_document['filename']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
                    
                    os.remove(pdf_path)  # Clean up temporary file
                    
                except Exception as e:
                    st.error(f"❌ Error generating PDF: {str(e)}")

def document_history_page():
    st.header("📚 Document History")
    
    if not st.session_state.documents:
        st.info("📭 No documents uploaded yet. Go to Document Upload to add some!")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get unique file types and convert to readable format
        doc_types = []
        for doc in st.session_state.documents:
            file_type = doc['file_type']
            if 'pdf' in file_type.lower():
                doc_types.append('PDF')
            elif 'html' in file_type.lower() or 'htm' in file_type.lower():
                doc_types.append('HTML')
            elif 'markdown' in file_type.lower() or file_type.lower() == 'md':
                doc_types.append('Markdown')
            else:
                doc_types.append('Other')
        
        file_types = ['All'] + sorted(list(set(doc_types)))
        selected_type = st.selectbox("Filter by type", file_types)
    
    with col2:
        date_filter = st.selectbox("Filter by date", [
            "All time", "Last 24 hours", "Last week", "Last month"
        ])
    
    with col3:
        search_term = st.text_input("Search by filename")
    
    # Apply filters
    filtered_docs = st.session_state.documents.copy()
    
    if selected_type != 'All':
        filtered_docs = []
        for doc in st.session_state.documents:  # Fixed bug: was using already filtered list
            file_type = doc['file_type']
            doc_category = 'Other'
            
            if 'pdf' in file_type.lower():
                doc_category = 'PDF'
            elif 'html' in file_type.lower() or 'htm' in file_type.lower():
                doc_category = 'HTML'
            elif 'markdown' in file_type.lower() or file_type.lower() == 'md':
                doc_category = 'Markdown'
            
            if doc_category == selected_type:
                filtered_docs.append(doc)
    
    if date_filter != "All time":
        cutoff_date = datetime.now()
        if date_filter == "Last 24 hours":
            cutoff_date -= timedelta(days=1)
        elif date_filter == "Last week":
            cutoff_date -= timedelta(weeks=1)
        elif date_filter == "Last month":
            cutoff_date -= timedelta(days=30)
        
        filtered_docs = [
            doc for doc in filtered_docs 
            if datetime.fromisoformat(doc['upload_date']) >= cutoff_date
        ]
    
    if search_term:
        filtered_docs = [
            doc for doc in filtered_docs 
            if search_term.lower() in doc['filename'].lower()
        ]
    
    # Display documents
    if not filtered_docs:
        st.info("🔍 No documents match your filters.")
        return
    
    for doc in filtered_docs:
        with st.expander(f"📄 {doc['filename']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Type:** {doc['file_type']}")
                st.write(f"**Size:** {doc['size']}")
                st.write(f"**Uploaded:** {datetime.fromisoformat(doc['upload_date']).strftime('%Y-%m-%d %H:%M')}")
            
            with col2:
                st.write(f"**Chunks:** {doc['chunks_count']}")
                if st.button(f"💬 Chat with this document", key=f"chat_{doc['id']}"):
                    if not st.session_state.api_configured:
                        st.error(f"❌ Please configure your {st.session_state.api_provider.upper()} API key first!")
                    else:
                        st.session_state.current_document = doc
                        # Load vector store for this document with current provider
                        vector_store = VectorStore(provider=st.session_state.api_provider)
                        vector_store.load_document(doc['id'])
                        st.session_state.vector_store = vector_store
                        st.session_state.messages = []  # Clear current chat
                        st.success(f"✅ Switched to {doc['filename']}. Go to Chat Interface!")

def chat_history_page():
    st.header("💭 Chat History")
    
    if not st.session_state.chat_history:
        st.info("💬 No chat history yet. Start a conversation in the Chat Interface!")
        return
    
    # Group chats by document
    chats_by_doc = {}
    for chat in st.session_state.chat_history:
        doc_name = chat['document_name']
        if doc_name not in chats_by_doc:
            chats_by_doc[doc_name] = []
        chats_by_doc[doc_name].append(chat)
    
    # Display chats
    for doc_name, chats in chats_by_doc.items():
        st.subheader(f"📖 {doc_name}")
        
        for i, chat in enumerate(chats, 1):
            with st.expander(f"Q{i}: {chat['question'][:50]}..."):
                st.write(f"**Question:** {chat['question']}")
                st.write(f"**Answer:** {chat['answer']}")
                st.write(f"**Time:** {datetime.fromisoformat(chat['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
                
                if chat['sources']:
                    st.write("**Sources:**")
                    for j, source in enumerate(chat['sources'], 1):
                        st.write(f"{j}. {source}")

def save_document_info(doc_info):
    """Save document info to persistent storage"""
    try:
        docs_file = "data/documents.json"
        documents = []
        
        if os.path.exists(docs_file):
            with open(docs_file, 'r') as f:
                documents = json.load(f)
        
        documents.append(doc_info)
        
        with open(docs_file, 'w') as f:
            json.dump(documents, f, indent=2)
            
    except Exception as e:
        st.error(f"Error saving document info: {str(e)}")

def save_chat_history(chat_entry):
    """Save chat entry to persistent storage"""
    try:
        chat_file = "data/chat_history.json"
        chats = []
        
        if os.path.exists(chat_file):
            with open(chat_file, 'r') as f:
                chats = json.load(f)
        
        chats.append(chat_entry)
        
        with open(chat_file, 'w') as f:
            json.dump(chats, f, indent=2)
            
    except Exception as e:
        st.error(f"Error saving chat history: {str(e)}")

if __name__ == "__main__":
    main()