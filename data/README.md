# Data Directory

This directory is used to store data for the Nexus RAG application.

-   **`/docs`**: This folder should contain any sample documents (e.g., PDFs) used for demonstrating or testing the application.
    
-   **`/vector_store`**: This is the default location where the application saves the generated FAISS vector indexes for each user session. Each session will have its own subdirectory (e.g., `session_20250810_123000`).
    

**Important**: The session-specific subdirectories within `/vector_store` are temporary and are ignored by Git (as specified in the root `.gitignore` file). They should not be committed to the version control system.