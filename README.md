
# Nexus RAG 🚀

Nexus RAG is an intelligent Q&A application that allows you to chat with your documents. It uses a Retrieval-Augmented Generation (RAG) pipeline, powered by the **Google Gemini API**, to provide accurate answers based on the content of your uploaded PDF files.

## Features

-   **Document Q&A**: Upload one or more PDF documents and ask questions in natural language.
    
-   **Explainable AI**: Each answer is accompanied by a rationale explaining how the conclusion was reached, providing transparency and trust.
    
-   **Evidence-Based Answers**: The UI includes an expandable "Show Evidence" section that displays the exact source text used to generate the answer.
    
-   **Simple & Intuitive UI**: A clean and user-friendly interface built with Streamlit.
    
-   **Robust Backend**: A scalable FastAPI backend handles document processing, the RAG pipeline, and the judge's submission API.
    

## How It Works

1.  **Upload**: The user uploads PDF documents through the Streamlit interface.
    
2.  **Ingest & Index**: The backend processes the documents, splits them into text chunks, and creates a searchable vector index using FAISS.
    
3.  **Query & Retrieve**: When a user asks a question, the system retrieves the most relevant text chunks from the index.
    
4.  **Generate & Display**: The retrieved chunks and the original question are sent to the **Gemini 1.5 Flash model**, which generates a final answer and a decision rationale. This structured response is then displayed in the UI.
    

## Setup and Installation

Follow these steps to get Nexus RAG running locally.

### Prerequisites

-   Python 3.9+
    
-   A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/ "null").
    

### 1. Clone the Repository

```
git clone [https://github.com/MR-MK47/Nexus-RAG.git](https://github.com/MR-MK47/Nexus-RAG.git)
cd Nexus-RAG

```

### 2. Set Up a Virtual Environment

```
# Create the virtual environment
python -m venv venv

# Activate it
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

```

### 3. Install Dependencies

```
pip install -r requirements.txt

```

### 4. Configure Your API Key

Create a file named `.env` in the root directory of the project and add your Google Gemini API key to it.

```
GEMINI_API_KEY="your-google-gemini-api-key"

```

### 5. Run the Application

You need to run the backend and frontend in two separate terminals.

**Terminal 1: Run the Backend**

```
python -m app.main

```

The backend server will start on `http://127.0.0.1:8000`.

**Terminal 2: Run the Frontend**

```
streamlit run ui/app.py

```

The Streamlit application will open in your browser. You can now upload documents and start asking questions!