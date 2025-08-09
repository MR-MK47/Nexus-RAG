import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# The API_URL should point to your backend server
API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000')  # Allow configuring via environment variable

def check_api_health():
    try:
        response = requests.get(f"{API_URL}/health")  # Assuming there's a health check endpoint
        return True
    except:
        return False

# Load environment variables from a .env file if it exists
load_dotenv()

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="VeriSureAI", layout="wide")

# --- Page Title and Description ---
st.title("🧠 VeriSure AI - Your Own Policy Explainer")
st.markdown("Upload your policy documents and ask any question about them.")

# Check if API is accessible
if not check_api_health():
    st.error("⚠️ Cannot connect to the backend server. Please ensure the backend is running and accessible.")
    st.stop()

# --- File Upload Section ---
st.subheader("📤 Upload Document")
uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])

if uploaded_file:
    # Use a spinner to indicate that processing is happening
    with st.spinner("Uploading and indexing your document..."):
        try:
            # Prepare the file for the POST request
            files = [("uploaded_files", (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type))]
            
            # Send the file to the backend API
            response = requests.post(f"{API_URL}/upload_docs", files=files)

            # Check the response from the server
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            
            data = response.json()
            
            st.success(data.get("message", "File uploaded and processed successfully!"))

            # Store the session_id received from the backend in the Streamlit session state
            session_id = data.get("session_id")
            if session_id:
                st.session_state["session_id"] = session_id
                st.info(f"🔑 Your session ID is: `{session_id}`")
            else:
                st.error("Could not retrieve session ID from the server.")

        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect to the backend API: {e}")
        except Exception as e:
            st.error(f"An error occurred during file upload: {e}")

st.markdown("---")

# --- Query Section ---
st.subheader("🔍 Ask a Question")
query = st.text_input("Enter your query in plain English", key="query_input")

if st.button("Submit Query", key="submit_button"):
    session_id = st.session_state.get("session_id")

    if not query:
        st.warning("Please enter a question.")
    elif not session_id:
        st.error("❗️ Please upload a document first to start a session.")
    else:
        with st.spinner("Thinking..."):
            try:
                # Prepare the JSON payload for the query
                payload = {"query": query, "session_id": session_id}
                
                # Send the query to the backend API
                response = requests.post(f"{API_URL}/query", json=payload)
                response.raise_for_status()

                result = response.json()

                if "error" in result:
                    st.error(f"❌ Error from API: {result['error']}")
                else:
                    st.success("✅ AI Answer:")
                    
                    # Display the question
                    st.markdown(f"**Your Question:** {result.get('query')}")

                    # Display the formatted JSON answer
                    response_text = result.get("response", "")
                    try:
                        # Try to parse and pretty-print the JSON response
                        parsed_json = json.loads(response_text)
                        st.json(parsed_json)
                    except (json.JSONDecodeError, TypeError):
                        # If it's not valid JSON, display it as plain text
                        st.markdown("**Answer:**")
                        st.markdown(response_text)

                    # Display the referenced clauses
                    retrieved_clauses = result.get("retrieved_clauses", [])
                    if retrieved_clauses:
                        st.markdown("---")
                        st.markdown("### 🔎 Referenced Clauses")
                        for i, clause in enumerate(retrieved_clauses):
                            with st.expander(f"**Reference Clause {i+1}**"):
                                st.code(clause, language="text")
            
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to the backend API: {e}")
            except Exception as e:
                st.error(f"An unknown error occurred: {e}")

# --- Footer ---
st.markdown(
    """
    <div style='position: fixed; bottom: 10px; right: 15px; color: #888; font-size: 0.75em;'>
         Trinetra AI
    </div>
    """,
    unsafe_allow_html=True
)