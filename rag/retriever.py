import os
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.retrievers import BM25Retriever
try:
    # 1. Try to get it from Streamlit Cloud Secrets 
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    # 2. Fall back to your local config file (for your laptop)
    from config.settings import GEMINI_API_KEY

# Initialize the exact same embedding model used when saving the PDF
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2",
    google_api_key=GEMINI_API_KEY
)

def retrieve(query: str, k: int = 5):
    """
    Retrieves the most relevant chunks from the resume using Hybrid Search.
    Uses custom Reciprocal Rank Fusion (RRF) to combine Vector and Keyword searches.
    """
    index_path = "faiss_index"

    if not os.path.exists(index_path):
        return []

    try:
        # Load the FAISS Vector Database
        vectorstore = FAISS.load_local(
            index_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        # 1. Get Semantic Search Results (FAISS Vectors)
        faiss_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        faiss_docs = faiss_retriever.invoke(query)

        # 2. Get Keyword Search Results (BM25)
        docs = list(vectorstore.docstore._dict.values())
        if not docs:
            return []
            
        bm25_retriever = BM25Retriever.from_documents(docs)
        bm25_retriever.k = k
        bm25_docs = bm25_retriever.invoke(query)

        # 3. Execute Reciprocal Rank Fusion (RRF) Algorithm
        # This mathematically combines the rankings of both searches
        doc_scores = {}
        c = 60 # Standard RRF smoothing constant
        
        # Score FAISS (Semantic) results
        for rank, doc in enumerate(faiss_docs):
            if doc.page_content not in doc_scores:
                doc_scores[doc.page_content] = 0
            doc_scores[doc.page_content] += 1.0 / (rank + c)
            
        # Score BM25 (Keyword) results
        for rank, doc in enumerate(bm25_docs):
            if doc.page_content not in doc_scores:
                doc_scores[doc.page_content] = 0
            doc_scores[doc.page_content] += 1.0 / (rank + c)

        # 4. Sort the documents by their combined fusion score
        ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Extract just the text strings and return the top 'k' results
        final_texts = [text for text, score in ranked_docs]
        return final_texts[:k]

    except Exception as e:
        print(f"Error during retrieval: {e}")
        return [f"CRITICAL ERROR: {str(e)}"]