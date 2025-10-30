import streamlit as st
import requests
import json
from typing import List, Dict, Any
import os

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# Page configuration
st.set_page_config(
    page_title="PDF Chat Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .source-doc {
        background-color: #f5f5f5;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem 0;
        font-size: 0.9rem;
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
st.markdown('<h1 class="main-header">📄 PDF Chat Assistant</h1>', unsafe_allow_html=True)

# Sidebar for PDF upload
with st.sidebar:
    st.header("📁 Upload PDF")
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ Backend API is not running!")
        st.info("Please start the backend server:\n```bash\nuvicorn backend.main:app --reload\n```")
        st.stop()
    else:
        st.success("✅ Backend API is running")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload a PDF file to start chatting with its content"
    )
    
    if uploaded_file is not None:
        if st.button("📤 Upload PDF", type="primary"):
            with st.spinner("Processing PDF..."):
                result = upload_pdf(uploaded_file)
                if result:
                    st.session_state.doc_id = result["doc_id"]
                    st.session_state.uploaded_file_name = uploaded_file.name
                    st.session_state.messages = []  # Clear previous chat
                    st.success(f"✅ {result['message']}")
                    st.rerun()
    
    # Display current document info
    if st.session_state.doc_id:
        st.markdown("---")
        st.subheader("📄 Current Document")
        st.info(f"**File:** {st.session_state.uploaded_file_name}")
        st.info(f"**ID:** {st.session_state.doc_id[:8]}...")
        
        if st.button("🗑️ Clear Document", type="secondary"):
            st.session_state.doc_id = None
            st.session_state.uploaded_file_name = None
            st.session_state.messages = []
            st.rerun()

# Main chat interface
if st.session_state.doc_id:
    st.subheader("💬 Chat with your PDF")
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>You:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>Assistant:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
            
            # Show source documents if available
            if "source_documents" in message and message["source_documents"]:
                with st.expander("📚 Source Documents", expanded=False):
                    for i, doc in enumerate(message["source_documents"]):
                        st.markdown(f"""
                        <div class="source-doc">
                            <strong>Source {i+1}:</strong><br>
                            {doc["page_content"]}<br>
                            <em>Metadata: {doc["metadata"]}</em>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your PDF..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Prepare history for API
        history = []
        for msg in st.session_state.messages[:-1]:  # Exclude the current message
            if msg["role"] == "user":
                history.append([msg["content"], ""])
            elif msg["role"] == "assistant":
                if history and history[-1][1] == "":
                    history[-1][1] = msg["content"]
        
        # Get response from API
        with st.spinner("Thinking..."):
            response = chat_with_pdf(st.session_state.doc_id, prompt, history)
            
            if response:
                # Add assistant response to chat
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response["answer"],
                    "source_documents": response["source_documents"]
                })
                st.rerun()
            else:
                st.error("Failed to get response from the assistant")

else:
    # Welcome message when no PDF is uploaded
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h2>Welcome to PDF Chat Assistant! 🤖</h2>
        <p style="font-size: 1.2rem; color: #666;">
            Upload a PDF file using the sidebar to start chatting with its content.
        </p>
        <p style="color: #888;">
            The AI will answer questions based on the text content of your PDF document.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🔍 Smart Search
        Ask questions about your PDF content and get accurate answers based on the document.
        """)
    
    with col2:
        st.markdown("""
        ### 📚 Source References
        See which parts of your PDF were used to answer your questions.
        """)
    
    with col3:
        st.markdown("""
        ### 💬 Conversational
        Maintain context throughout your conversation with the AI assistant.
        """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888;'>Built with Streamlit, FastAPI, and LangChain</div>",
    unsafe_allow_html=True
)
