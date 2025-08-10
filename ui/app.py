import streamlit as st
import requests
import os
from dotenv import load_dotenv

# --- 1. INITIALIZATION & CONFIGURATION ---

def initialize_session():
    """
    Initializes the Streamlit session state. It gets a unique session ID
    from the backend and sets up the message history.
    """
    if "session_id" not in st.session_state:
        try:
            # Request a new session ID from the backend API
            response = requests.get("http://127.0.0.1:8000/start_session")
            response.raise_for_status()
            st.session_state.session_id = response.json()["session_id"]
            st.session_state.messages = []
        except requests.exceptions.RequestException as e:
            # Display a persistent error if the backend is not available on startup
            st.error(f"Fatal Error: Could not connect to the backend API. Please ensure the server is running. Details: {e}")
            st.stop() # Halt the app if the backend isn't running

# Load environment variables from the .env file
load_dotenv()

# Configure the Streamlit page
st.set_page_config(page_title="Nexus RAG", page_icon="🚀", layout="wide")

# Initialize the session state
initialize_session()


# --- 2. HEADER & INTRODUCTORY TEXT ---

st.title("Nexus RAG 🚀")
st.header("Intelligent Query-Retrieval System")
st.write("""
Upload your insurance policy PDFs and get answers backed by direct evidence from the documents.
This application uses a Retrieval-Augmented Generation (RAG) pipeline to provide accurate, context-aware responses.
""")


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
            with st.spinner("Processing documents... This may take a moment."):
                # Prepare files for the multipart/form-data request
                files = [("uploaded_files", (file.name, file.getvalue(), file.type)) for file in uploaded_files]
                
                try:
                    # Send files to the backend for processing and indexing
                    response = requests.post(
                        f"http://127.0.0.1:8000/upload_docs?session_id={st.session_state.session_id}",
                        files=files
                    )
                    response.raise_for_status()
                    st.success("Files processed successfully! You can now ask questions.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error processing files: {e}")
        else:
            st.warning("Please upload at least one PDF file.")


# --- 4. MAIN CHAT INTERFACE ---

st.subheader("Chat with Your Documents")

# Display the existing chat message history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If the message is from the assistant, show the rationale and evidence
        if message["role"] == "assistant":
            if message.get("rationale"):
                st.info(f"**Rationale:** {message['rationale']}")
            with st.expander("Show Evidence"):
                for i, chunk in enumerate(message.get("evidence", [])):
                    st.info(f"Source {i+1}:\n\n{chunk}")

# Handle new user input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user's message to history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get and display the assistant's response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Thinking..."):
            try:
                # Send the query to the backend API
                response = requests.post(
                    "http://127.0.0.1:8000/query",
                    json={"query": prompt, "session_id": st.session_state.session_id}
                )
                response.raise_for_status()
                
                response_data = response.json()
                answer = response_data.get("answer", "Sorry, I couldn't find an answer.")
                rationale = response_data.get("decision_rationale")
                evidence = response_data.get("source_clauses", [])

                # Display the main answer and rationale
                message_placeholder.markdown(answer)
                if rationale:
                    st.info(f"**Rationale:** {rationale}")

                # Display the evidence in a collapsible section
                with st.expander("Show Evidence"):
                    if evidence:
                        for i, chunk in enumerate(evidence):
                            st.info(f"Source {i+1}:\n\n{chunk}")
                    else:
                        st.write("No specific evidence was used for this answer.")
                
                # Store the full response in session state for redisplay
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer, 
                    "rationale": rationale, 
                    "evidence": evidence
                })

            except requests.exceptions.RequestException as e:
                error_message = f"Error from backend: {e}"
                message_placeholder.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
