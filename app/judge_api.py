import os
import requests
import tempfile
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from app.core.retriever import build_index_from_path, retrieve_chunks_from_path

# --- Configuration & Initialization ---
load_dotenv()
router = APIRouter()
security = HTTPBearer()

JUDGE_API_TOKEN = "6ccbcb445fa7637aab976eee0a08c98ecc722ccce7ad0b80ffccc4614dc382aa"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# --- Pydantic Models ---
class JudgeRequest(BaseModel):
    documents: str
    questions: List[str]

class JudgeResponse(BaseModel):
    answers: List[str]

# --- Security Dependency ---
def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.scheme != "Bearer" or credentials.credentials != JUDGE_API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid authorization token")
    return credentials.credentials

# --- API Endpoint ---
@router.post("/hackrx/run", response_model=JudgeResponse, dependencies=[Depends(verify_token)])
async def run_submission(request: JudgeRequest):
    """
    Stateless endpoint to download a document, process questions via Gemini, and return answers.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not found in environment variables.")

    temp_dir = tempfile.mkdtemp()
    try:
        doc_response = requests.get(request.documents)
        doc_response.raise_for_status()
        
        temp_pdf_path = os.path.join(temp_dir, "policy.pdf")
        with open(temp_pdf_path, 'wb') as f:
            f.write(doc_response.content)

        vector_store_path = os.path.join(temp_dir, "vector_store")
        build_index_from_path(source_dir=temp_dir, vector_store_path=vector_store_path)

        answers = []
        for question in request.questions:
            relevant_chunks = retrieve_chunks_from_path(query=question, vector_store_path=vector_store_path)
            
            if not relevant_chunks:
                answers.append("Could not find relevant information to answer the question.")
                continue

            context = "\n\n---\n\n".join(relevant_chunks)
            prompt = f"""
            Based ONLY on the context provided below, give a direct and concise answer to the user's question.
            Do not use any Markdown formatting. Return only the plain text answer.

            Context:
            ---
            {context}
            ---

            Question: {question}

            Answer:
            """
            
            # --- Gemini API Call ---
            headers = {'Content-Type': 'application/json'}
            params = {'key': GEMINI_API_KEY}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            api_response = requests.post(GEMINI_API_URL, params=params, headers=headers, json=payload)
            api_response.raise_for_status()
            
            response_json = api_response.json()
            answer = response_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No answer generated.")
            answers.append(answer.strip())

        return JudgeResponse(answers=answers)

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to process request: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")
    finally:
        shutil.rmtree(temp_dir)
