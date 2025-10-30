# Chat with PDF using Local LLM (FLAN-T5)

This project lets you upload any PDF and ask questions about its content using a locally hosted generative model — no API keys required!

## 🧠 Features

- Upload and chat with your PDF
- Uses `flan-t5-base` (free, instruction-tuned model from HuggingFace)
- Fully local — no internet connection or OpenAI key needed
- Built with LangChain, FAISS, HuggingFace, and Streamlit

## 📁 Files

- `app.py`: Streamlit frontend (full chat interface)
- `app_simple.py`: Simplified version (if you encounter WebSocket issues)
- `pdf_processor.py`: PDF reading and vector storage
- `qa_chain.py`: Question Answering logic using local FLAN-T5
- `requirements.txt`: Project dependencies
- `fix_websocket.ps1`: PowerShell script to fix WebSocket issues
- `run_app.bat`: Windows batch file to run the app

## 🚀 How to Run

### Option 1: Quick Fix for WebSocket Issues (Recommended)

If you're experiencing WebSocket errors, run this PowerShell script:

```powershell
# Right-click on fix_websocket.ps1 and select "Run with PowerShell"
# OR open PowerShell and run:
.\fix_websocket.ps1
```

Then run the app:
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the app
streamlit run app.py
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### Option 3: Simple Version (if WebSocket issues persist)

If you continue to have WebSocket issues, try the simplified version:

```bash
streamlit run app_simple.py
```

## 🔧 Troubleshooting

### WebSocket Error Fix
If you see errors like:
```
TypeError: WebSocketHandler.__init__() missing 2 required positional arguments
```

1. **Use the PowerShell script**: Run `fix_websocket.ps1`
2. **Or manually reinstall**: Delete the `venv` folder and recreate it
3. **Try the simple version**: Use `app_simple.py` instead

### Common Issues

1. **Port already in use**: Change the port with `streamlit run app.py --server.port 8502`
2. **Memory issues**: The model requires ~1GB RAM. Close other applications if needed
3. **Slow first run**: The model downloads on first use (~1GB download)

## 📝 Usage

1. Upload a PDF file
2. Wait for processing (may take a few minutes on first run)
3. Ask questions about the PDF content
4. Get AI-powered answers based on the document

## 🛠️ Technical Details

- **Model**: FLAN-T5-Base (1.1B parameters)
- **Vector Store**: FAISS for efficient similarity search
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Framework**: Streamlit for the web interface

```bash
git clone https://github.com/your-repo/chat-with-pdf
cd chat-with-pdf
pip install -r requirements.txt
streamlit run app.py
