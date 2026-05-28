import os
from langchain_community.vectorstores import FAISS

DB_PATH = os.path.join("data" , "vector_db")

def create_vector_store(chunks,embedder):
    """
    Converts chunks to vectors and saves the FAISS database locally.
    """
    print("Building FAISS Vector Database")
    vector_store = FAISS.from_documents(chunks, embedder)
    
    print(f"Saving database to {DB_PATH}")
    vector_store.save_local(DB_PATH)
    print("Vector Database saved successfully!")
    
    return vector_store

def load_vector_store(embedder):
    """
    Loads an existing FAISS database from the local folder.
    """
    if os.path.exists(DB_PATH):
        print(f"Loading existing database from {DB_PATH}...")
        # allow_dangerous_deserialization is required by FAISS for local loading
        return FAISS.load_local(DB_PATH, embedder, allow_dangerous_deserialization=True)
    else:
        print("No existing database found.")
        return None
