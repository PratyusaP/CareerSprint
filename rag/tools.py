from langchain_core.tools import tool
from rag.retriever import retrieve

@tool
def search_resume_database(query: str) -> str:
    """
    Searches the user's resume vector database for context.
    Use this tool ONLY when the user asks questions about the user's past experience, 
    education, skills, or projects. Do not use this for general knowledge questions.
    """
    print(f"🛠️ [Agent Action] Searching Resume Database for: '{query}'")
    
    # 1. Use your existing code to get the top 3 chunks
    retrieved_chunks = retrieve(query, k=3)
    
    # 2. If FAISS finds nothing, tell the Agent so it doesn't hallucinate
    if not retrieved_chunks:
        return "No relevant information found in the resume database."
    
    # 3. Format the list of chunks into a single readable string for the Agent
    formatted_context = "\n\n---\n\n".join(retrieved_chunks)
    
    return formatted_context