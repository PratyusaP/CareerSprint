import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

# Import your tool
from rag.tools import search_resume_database 
try:
    # 1. Try to get it from Streamlit Cloud Secrets (for deployment)
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    # 2. Fall back to your local config file (for your laptop)
    from config.settings import GEMINI_API_KEY

os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

# 1. Initialize the Model (With the token limit fix!)
model = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite", 
    temperature=0,
    max_output_tokens=8192, 
    timeout=120 
)

# 2. The System Prompt 
SYSTEM_PROMPT = """You are a highly capable Career Assistant AI. 
Your job is to answer questions about the user's professional background, education, and skills.
You have access to a resume database tool. If the user asks about their experience, YOU MUST use the tool to find the facts.
Do not guess or hallucinate. If the tool returns no data, state that you don't have that information."""

# 3. Build the Agent
agent = create_agent(
    model=model,
    tools=[search_resume_database],
    system_prompt=SYSTEM_PROMPT
)

def ask_career_agent(query: str) -> str:
    """Runs the user query through the Agent."""
    try:
        response = agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        
        raw_content = response["messages"][-1].content
        
        # The Unpacker: Extracts text if Gemini returns a list of blocks
        if isinstance(raw_content, str):
            return raw_content
        elif isinstance(raw_content, list):
            for block in raw_content:
                if isinstance(block, dict) and block.get("type") == "text":
                    return block.get("text")
                    
        return str(raw_content)
        
    except Exception as e:
        return f"⚠️ The Agent encountered an error: {str(e)}"