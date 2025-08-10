import os
import json
import requests
from typing import List
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.core.retriever import retrieve_chunks, build_index
from app import judge_api

# --- Configuration & Initialization ---
load_dotenv()
app = FastAPI(
    title="Nexus RAG Backend",
    description="API for both the Streamlit UI and the Judge's Submission",
    version="3.1"
)
# Include the separate router for the judge's API, prefixed with /api/v1
app.include_router(judge_api.router, prefix="/api/v1")

# --- Constants ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# --- CORS Middleware ---
# Allows the Streamlit frontend (running on a different port) to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted to the Streamlit app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for UI API ---
class QueryRequest(BaseModel):
    """Defines the expected request body for a query from the UI."""
    query: str
    session_id: str

class StructuredResponse(BaseModel):
    """Defines the structured JSON response sent back to the UI."""
    query: str
    answer: str
    decision_rationale: str
    source_clauses: List[str]
    status: str = "success"

# --- API Endpoints for Streamlit UI ---

@app.get("/start_session", summary="Start a new user session")
def start_session():
    """Generates and returns a unique session ID for a new user interaction."""
    return {"session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}

@app.post("/upload_docs", summary="Upload and process documents")
async def upload_docs(session_id: str, uploaded_files: List[UploadFile] = File(...)):
    """Handles file uploads for a specific session and builds the vector index."""
    save_dir = f"temp_uploads/{session_id}"
    os.makedirs(save_dir, exist_ok=True)
    for file in uploaded_files:
        file_path = os.path.join(save_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
    try:
        build_index(session_id, save_dir)
        return {"message": "Files processed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=StructuredResponse, summary="Query documents for a session")
def query_docs(request: QueryRequest):
    """Processes a user's query for a specific session using the Gemini API."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not found in environment variables.")

    try:
        # Step 1: Retrieve relevant context from the documents
        relevant_chunks = retrieve_chunks(request.query, request.session_id)
        if not relevant_chunks:
            return StructuredResponse(
                query=request.query,
                answer="No relevant information was found in the uploaded documents.",
                decision_rationale="No relevant text chunks were retrieved to answer the query.",
                source_clauses=[]
            )
        
        context = "\n\n---\n\n".join(relevant_chunks)
        
        # Step 2: Create a detailed prompt for the LLM to generate a structured response
        prompt = f"""
        Context:\n{context}\n\nQuestion: "{request.query}"
        Based ONLY on the context provided, perform two tasks:
        1. Answer the question.
        2. Provide a brief rationale explaining how you arrived at the answer.
        Respond with a single, raw JSON object with two keys: "answer" and "rationale". Do not include any markdown or other text.
        """

        # Step 3: Call the Gemini API
        headers = {'Content-Type': 'application/json'}
        params = {'key': GEMINI_API_KEY}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        api_response = requests.post(GEMINI_API_URL, params=params, headers=headers, json=payload)
        api_response.raise_for_status()
        
        response_json = api_response.json()
        
        # Step 4: Robustly parse the JSON response from the LLM
        llm_response_text = ""
        try:
            llm_response_text = response_json['candidates'][0]['content']['parts'][0]['text']
            if llm_response_text.strip().startswith("```json"):
                llm_response_text = llm_response_text.strip().strip("```json\n").strip("`")
            llm_json = json.loads(llm_response_text)
        except (KeyError, IndexError, json.JSONDecodeError):
            return StructuredResponse(
                query=request.query,
                answer=f"The model returned an unexpected or invalid response: {llm_response_text}",
                decision_rationale="Could not parse the decision rationale from the model's output.",
                source_clauses=relevant_chunks,
                status="error"
            )
        
        # Step 5: Return the final structured response
        return StructuredResponse(
            query=request.query,
            answer=llm_json.get("answer", "Failed to extract answer from model response."),
            decision_rationale=llm_json.get("rationale", "Failed to extract rationale from model response."),
            source_clauses=relevant_chunks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Server Startup ---
# This block allows the server to be started directly by running `python -m app.main`
# It is not inside an `if __name__ == "__main__"` block to ensure it runs in module mode.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
