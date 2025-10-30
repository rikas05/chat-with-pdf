# PDF Chat Assistant with LangChain and Groq API

This project is a high-performance PDF chat assistant that allows you to have interactive conversations with your PDF documents. It leverages the speed of the Groq API for real-time responses and the power of LangChain for robust conversational AI. The application is built with a Streamlit frontend and a FastAPI backend.

## Features

- **Interactive PDF Chat**: Upload a PDF and ask questions about its content.
- **Fast Responses**: Powered by the Groq API for near-instant answers.
- **Source Referencing**: Identifies the parts of the PDF used to generate a response.
- **Conversational Memory**: Maintains context throughout the conversation.
- **Easy-to-use Interface**: Simple and intuitive UI built with Streamlit.
- **Decoupled Frontend/Backend**: Scalable architecture with a FastAPI backend for processing and a Streamlit frontend for user interaction.

## Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/)
- **Conversational AI**: [LangChain](https://www.langchain.com/)
- **Language Model**: [Groq](https://groq.com/)
- **Embeddings**: [Hugging Face](https://huggingface.co/) (Sentence Transformers)
- **Vector Store**: [FAISS](https://github.com/facebookresearch/faiss)

## Prerequisites

- Python 3.8+
- `pip` package manager

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/pdf-chat-assistant.git
    cd pdf-chat-assistant
    ```

2.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Get a Groq API Key**:
    To use this application, you need a Groq API key. You can get a free key from the [Groq Console](https://console.groq.com/).

2.  **Create a `.env` file**:
    In the root directory of the project, create a file named `.env` and add your Groq API key:

    ```
    GROQ_API_KEY="your-groq-api-key"
    ```

## Running the Application

You need to run the backend and frontend servers in two separate terminals.

1.  **Start the Backend (FastAPI)**:
    Open a terminal and run the following command to start the FastAPI server:
    ```bash
    uvicorn backend.main:app --reload
    ```
    The backend will be available at `http://127.0.0.1:8000`.

2.  **Start the Frontend (Streamlit)**:
    Open a second terminal and run the following command to start the Streamlit app:
    ```bash
    streamlit run streamlit_app.py
    ```
    The frontend will be accessible in your browser at `http://localhost:8501`.

## Usage

1.  **Open the application** in your web browser.
2.  **Upload a PDF file** using the sidebar.
3.  **Wait for the processing** to complete. You will see a success message.
4.  **Start chatting** by typing your questions in the input box.

## Project Structure

-   `streamlit_app.py`: The main frontend application file.
-   `backend/main.py`: The main backend application file with the FastAPI logic.
-   `requirements.txt`: A list of all the Python packages required.
-   `data/`: This directory is created automatically to store the FAISS vector indexes for the uploaded PDFs.

## API Endpoints

The FastAPI backend provides the following endpoints:

-   `POST /upload_pdf`: Upload a PDF file.
-   `POST /chat`: Send a question and get an answer.
-   `GET /health`: Check the health of the backend.
-   `GET /documents`: List all uploaded documents.
-   `DELETE /documents/{doc_id}`: Delete a specific document.

## Customization

You can customize the language model and the embedding model by setting the following environment variables in your `.env` file:

-   `GROQ_MODEL`: The Groq model to use (e.g., `llama3-8b-8192`).
-   `HUGGINGFACE_EMBEDDINGS_MODEL`: The Sentence Transformers model to use for embeddings (e.g., `sentence-transformers/all-MiniLM-L6-v2`).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
