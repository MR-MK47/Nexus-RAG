import streamlit as st
import requests
import os
from dotenv import load_dotenv

# --- 1. INITIALIZATION & CONFIGURATION ---

# Load environment variables from .env file for local development
load_dotenv()

# Get the backend URL from an environment variable.
# On Render, this will be the live URL of your backend service.
# Locally, it will fall back to the default localhost address.
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

def initialize_session():
    """
    Initializes the Streamlit session state by getting a unique session ID
    from the backend.
    """
    if "session_id" not in st.session_state:
        try:
            # Use the BACKEND_URL variable to make the request
            response = requests.get(f"{BACKEND_URL}/start_session")
            response.raise_for_status()
            st.session_state.session_id = response.json()["session_id"]
            st.session_state.messages = []
        except requests.exceptions.RequestException as e:
            st.error(f"Fatal Error: Could not connect to the backend. Ensure it's running and accessible. Details: {e}")
            st.stop()

# Configure and initialize the app
st.set_page_config(page_title="Nexus RAG", page_icon="🚀", layout="wide")
initialize_session()


# --- 2. HEADER & INTRODUCTORY TEXT ---

st.title("Nexus RAG 🚀")
st.header("Intelligent Query-Retrieval System")
st.write("Upload your insurance policy PDFs and get answers backed by direct evidence from the documents.")


# --- 3. SIDEBAR FOR DOCUMENT UPLOADS ---

with st.sidebar:
    st.header("Upload Your Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF files and click 'Process'",
        accept_multiple_files=True,
        type="pdf"
    )

    if st.button("Process"):
        if uploaded_files:
            with st.spinner("Processing documents..."):
                files = [("uploaded_files", (file.name, file.getvalue(), file.type)) for file in uploaded_files]
                try:
                    # Use the BACKEND_URL variable for the upload request
                    response = requests.post(
                        f"{BACKEND_URL}/upload_docs?session_id={st.session_state.session_id}",
                        files=files
                    )
                    response.raise_for_status()
                    st.success("Files processed successfully!")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error processing files: {e}")
        else:
            st.warning("Please upload at least one PDF file.")


# --- 4. MAIN CHAT INTERFACE ---

st.subheader("Chat with Your Documents")

# Display message history
for message in st.session_state.messages:
    # ... (This part remains the same)
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if message.get("rationale"):
                st.info(f"**Rationale:** {message['rationale']}")
            with st.expander("Show Evidence"):
                for i, chunk in enumerate(message.get("evidence", [])):
                    st.info(f"Source {i+1}:\n\n{chunk}")

# Handle new user input
if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Thinking..."):
            try:
                # Use the BACKEND_URL variable for the query request
                response = requests.post(
                    f"{BACKEND_URL}/query",
                    json={"query": prompt, "session_id": st.session_state.session_id}
                )
                response.raise_for_status()
                
                # ... (The rest of the response handling remains the same)
                response_data = response.json()
                answer = response_data.get("answer", "No answer found.")
                rationale = response_data.get("decision_rationale")
                evidence = response_data.get("source_clauses", [])

                message_placeholder.markdown(answer)
                if rationale:
                    st.info(f"**Rationale:** {rationale}")
                with st.expander("Show Evidence"):
                    for i, chunk in enumerate(evidence):
                        st.info(f"Source {i+1}:\n\n{chunk}")
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer, 
                    "rationale": rationale, 
                    "evidence": evidence
                })
            except requests.exceptions.RequestException as e:
                st.error(f"Error from backend: {e}")

