import streamlit as st
import requests
import json
from typing import List, Dict, Any
import os

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# Page configuration
st.set_page_config(
    page_title="Groq PDF Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a more modern and visually appealing look
st.markdown("""
<style>
    /* General Styles */
    body {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background-color: #f9fafb;
    }

    /* Header */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #1a202c;
        text-align: center;
        margin-bottom: 2rem;
        letter-spacing: -1px;
    }

    /* Sidebar */
    .st-emotion-cache-1jicfl2 {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    .st-emotion-cache-6q9sum {
        background-color: #f9fafb;
    }

    /* Chat Messages */
    .st-emotion-cache-1wivap2 {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .user-message {
        background-color: #edf2f7;
    }
    
    .assistant-message {
        background-color: #ffffff;
    }

    /* Source Documents */
    .source-doc {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        padding: 0.75rem;
        border-radius: 0.375rem;
        margin-top: 0.5rem;
        font-size: 0.9rem;
    }

    /* Welcome Message */
    .welcome-container {
        text-align: center;
        padding: 3rem;
        background-color: #ffffff;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
    }
    
    .welcome-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #2d3748;
    }
    
    .welcome-subheader {
        font-size: 1.25rem;
        color: #718096;
    }

</style>
""", unsafe_allow_html=True)

def upload_pdf(file) -> Dict[str, Any]:
    """Upload PDF to backend and get doc_id"""
    try:
        files = {"file": (file.name, file.getvalue(), "application/pdf")}
        response = requests.post(f"{API_BASE_URL}/upload_pdf", files=files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Upload failed: {e}")
        return None

def chat_with_pdf(doc_id: str, question: str, history: List[List[str]]) -> Dict[str, Any]:
    """Send chat request to backend"""
    try:
        payload = {
            "doc_id": doc_id,
            "question": question,
            "history": history
        }
        response = requests.post(f"{API_BASE_URL}/chat", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Chat request failed: {e}")
        return None

def check_api_health() -> bool:
    """Check if backend API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "doc_id" not in st.session_state:
    st.session_state.doc_id = None
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None

# Main header
st.markdown('<h1 class="main-header">🤖 Groq PDF Chat</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")

    # API Health Check
    with st.expander("API Status", expanded=True):
        if check_api_health():
            st.success("API is running")
        else:
            st.error("API is not running")
            st.info("Start the backend with: `uvicorn backend.main:app --reload`")
            st.stop()
    
    st.header("📄 PDF Upload")
    uploaded_file = st.file_uploader(
        "Upload a PDF",
        type="pdf",
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        if st.button("Process PDF", type="primary", use_container_width=True):
            with st.spinner("Analyzing PDF..."):
                result = upload_pdf(uploaded_file)
                if result:
                    st.session_state.doc_id = result["doc_id"]
                    st.session_state.uploaded_file_name = uploaded_file.name
                    st.session_state.messages = []
                    st.success(f"Processed: {uploaded_file.name}")
                    st.rerun()
    
    if st.session_state.doc_id:
        st.markdown("---")
        st.subheader("Current Document")
        st.info(f"**File:** {st.session_state.uploaded_file_name}")
        if st.button("Clear Document", use_container_width=True):
            st.session_state.doc_id = None
            st.session_state.uploaded_file_name = None
            st.session_state.messages = []
            st.rerun()

# Main chat interface
if st.session_state.doc_id:
    st.subheader(f"Chat with: {st.session_state.uploaded_file_name}")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "source_documents" in message:
                with st.expander("Source Documents"):
                    for i, doc in enumerate(message["source_documents"]):
                        st.markdown(f"""
                        <div class="source-doc">
                            <strong>Source {i+1}:</strong><br>
                            <p>{doc['page_content']}</p>
                            <em>Metadata: {doc['metadata']}</em>
                        </div>
                        """, unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Thinking..."):
            history = [[msg["content"], ""] for msg in st.session_state.messages if msg["role"] == "user"]
            if len(history) > 1:
                 history[-2][1] = st.session_state.messages[-2]["content"]

            response = chat_with_pdf(st.session_state.doc_id, prompt, history)
            
            if response:
                with st.chat_message("assistant"):
                    st.markdown(response["answer"])
                    with st.expander("Source Documents"):
                        for i, doc in enumerate(response["source_documents"]):
                             st.markdown(f"""
                            <div class="source-doc">
                                <strong>Source {i+1}:</strong><br>
                                <p>{doc['page_content']}</p>
                                <em>Metadata: {doc['metadata']}</em>
                            </div>
                            """, unsafe_allow_html=True)

                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response["answer"],
                    "source_documents": response["source_documents"]
                })
            else:
                st.error("Failed to get response from the assistant")
else:
    # Welcome message
    st.markdown("""
    <div class="welcome-container">
        <h1 class="welcome-header">Welcome to Groq PDF Chat</h1>
        <p class="welcome-subheader">Upload a PDF to start a conversation</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    st.subheader("Features")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(" **Fast & Accurate:** Get quick and precise answers from your PDFs.")
    with col2:
        st.info(" **Source Highlighting:** See exactly where the information comes from.")
    with col3:
        st.info(" **Conversational:** Chat naturally with your documents.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888;'>Powered by Groq, LangChain, and Streamlit</div>",
    unsafe_allow_html=True
)
