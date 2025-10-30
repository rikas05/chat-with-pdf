"""
File: backend/main.py
FastAPI backend that ingests PDFs, builds FAISS vectorstores with embeddings,
and answers questions using Groq API via LangChain ConversationalRetrievalChain.
"""

import os
import uuid
import shutil
import traceback
from typing import Optional, List, Dict, Any
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

# ---------------------------
# Environment & Config
# ---------------------------
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
EMBED_MODEL = os.getenv("HUGGINGFACE_EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

DATA_DIR = Path("data/indexes")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------
# FastAPI setup
# ---------------------------
app = FastAPI(title="Chat with PDF (LangChain + Groq API)")

# ---------------------------
# LangChain imports
# ---------------------------
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_classic.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI


# ---------------------------
# Pydantic models
# ---------------------------
class UploadResponse(BaseModel):
    doc_id: str
    message: str


class ChatRequest(BaseModel):
    doc_id: str
    question: str
    history: Optional[List[List[str]]] = None


class ChatResponse(BaseModel):
    answer: str
    source_documents: List[Dict[str, Any]]
    history: List[List[str]]


# ---------------------------
# Helpers
# ---------------------------
def _get_index_path(doc_id: str) -> Path:
    return DATA_DIR / doc_id


def _cleanup_index(doc_id: str):
    path = _get_index_path(doc_id)
    if path.exists():
        shutil.rmtree(path)


# ---------------------------
# Upload PDF and create FAISS index
# ---------------------------
@app.post("/upload_pdf", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF, extract text, create FAISS index, and return doc_id."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    doc_id = str(uuid.uuid4())
    index_dir = _get_index_path(doc_id)
    index_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = index_dir / file.filename

    try:
        # Save PDF
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        # Extract and split text
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load_and_split()

        splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
        docs = []
        for p in pages:
            chunks = splitter.split_text(p.page_content)
            for i, c in enumerate(chunks):
                docs.append(
                    Document(
                        page_content=c,
                        metadata={
                            "source": file.filename,
                            "page": p.metadata.get('page', 0),
                            "chunk": i
                        }
                    )
                )

        if not docs:
            _cleanup_index(doc_id)
            raise HTTPException(status_code=500, detail="No text extracted from PDF.")

        # Create embeddings and FAISS index
        print(f"📄 Processing {len(docs)} text chunks from {file.filename}")
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL, 
            model_kwargs={"device": "cpu"}
        )
        faiss_index = FAISS.from_documents(docs, embeddings)
        faiss_index.save_local(str(index_dir))

        return UploadResponse(
            doc_id=doc_id, 
            message=f"✅ PDF processed successfully. Created {len(docs)} text chunks."
        )

    except Exception as e:
        print(f"❌ Error during PDF upload: {e}\n{traceback.format_exc()}")
        _cleanup_index(doc_id)
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")


# ---------------------------
# LLM Initialization (Groq API)
# ---------------------------
_llm_cache = None


def get_llm():
    """Return or initialize the Groq LLM."""
    global _llm_cache

    if _llm_cache is not None:
        return _llm_cache

    if not GROQ_API_KEY:
        raise ValueError(
            "❌ Missing GROQ_API_KEY in environment variables.\n"
            "Get a free API key at: https://console.groq.com"
        )

    print(f"🔧 Initializing Groq API with model: {GROQ_MODEL}")

    try:
        _llm_cache = ChatOpenAI(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            temperature=0.7,
            max_tokens=4048,
        )

        print(f"✅ Groq API initialized successfully with {GROQ_MODEL}")
        return _llm_cache

    except Exception as e:
        print(f"❌ Error initializing Groq API: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"LLM initialization failed: {str(e)}")


# ---------------------------
# Chat Endpoint
# ---------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Query the PDF index using Groq API."""
    print(f"\n📩 Chat request for doc_id={req.doc_id}")
    print(f"❓ Question: {req.question}")

    index_dir = _get_index_path(req.doc_id)
    if not index_dir.exists():
        raise HTTPException(
            status_code=404, 
            detail="Document not found. Please upload a PDF first."
        )

    try:
        # Load embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL, 
            model_kwargs={"device": "cpu"}
        )

        # Load FAISS index
        print(f"📘 Loading FAISS index from {index_dir}...")
        vectordb = FAISS.load_local(
            str(index_dir), 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        
        # Create retriever
        retriever = vectordb.as_retriever(
            search_type="similarity", 
            search_kwargs={"k": 4}
        )

        # Get LLM
        llm = get_llm()

        # Create conversational retrieval chain
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            return_source_documents=True,
            verbose=False,
        )

        # Prepare chat history
        history = req.history or []
        history_tuples = [(h[0], h[1]) for h in history] if history else []

        # Generate answer
        print("🤖 Generating answer with Groq...")
        result = qa_chain.invoke({
            "question": req.question, 
            "chat_history": history_tuples
        })

        # Extract answer and sources
        answer = result.get("answer", "")
        source_docs = []
        for d in result.get("source_documents", []):
            source_docs.append({
                "page_content": d.page_content[:500],
                "metadata": d.metadata
            })

        # Update history
        history.append([req.question, answer])

        print(f"✅ Answer generated: {answer[:100]}...")
        return ChatResponse(
            answer=answer, 
            source_documents=source_docs, 
            history=history
        )

    except Exception as e:
        print(f"❌ Error during chat: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# ---------------------------
# Health Check
# ---------------------------
@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "llm_provider": "groq",
        "groq_model": GROQ_MODEL,
        "groq_key_set": bool(GROQ_API_KEY),
        "embed_model": EMBED_MODEL,
        "llm_loaded": _llm_cache is not None,
    }


# ---------------------------
# Optional: List all uploaded documents
# ---------------------------
@app.get("/documents")
def list_documents():
    """List all uploaded document IDs."""
    doc_ids = []
    if DATA_DIR.exists():
        for item in DATA_DIR.iterdir():
            if item.is_dir():
                doc_ids.append(item.name)
    
    return {
        "count": len(doc_ids),
        "documents": doc_ids
    }


# ---------------------------
# Optional: Delete a document
# ---------------------------
@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    """Delete a specific document and its index."""
    try:
        _cleanup_index(doc_id)
        return {"message": f"Document {doc_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")