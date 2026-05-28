# 🚀 CareerSprint: Agentic RAG-Driven Career Assistant

An Agentic RAG-Driven Career Assistant designed to analyze resumes, provide actionable career improvements, and conduct highly contextual mock interviews for technical roles. 

# ✨ Key Features

- **🤖 Agentic AI Pipeline:** Built directly into the RAG generator, the LLM acts as an autonomous agent that dynamically routes user queries, adopts specific interviewer personas, and maintains strict conversational guardrails.
- **🧠 Stateful Conversational Memory:** Utilizes Streamlit's advanced session state to maintain short-term conversational context. The agent remembers your target role and previous answers without needing to re-read the vector database, eliminating latency.
- **📊 Smart Resume Analysis:** Uses a hybrid retrieval approach (FAISS + BM25) to analyze strengths, weaknesses, and actionable improvements for a specific target role.
- **👁️ Robust OCR Fallback:** Includes silent image-to-text processing using Tesseract, ensuring consistent data extraction even if the user uploads a flattened or image-based PDF.

# 📂 Project Architecture

```text
CareerSprint/
│
├── config/               # Configuration settings and API keys (Git ignored)
├── data/                 # Local data storage for resumes & vector DBs (Git ignored)
├── faiss_index/          # Auto-generated local FAISS database (Git ignored)
│
├── rag/                  # Core Retrieval-Augmented Generation logic
│   ├── generator.py      # Core Agentic AI logic, prompt routing, and persona management
│   ├── pdf_processor.py  # Handles document parsing, OCR fallback, and indexing
│   ├── retriever.py      # Manages hybrid search (FAISS + BM25) and caching
│   ├── tools.py          # Custom RAG tools and LangChain utilities
│   └── vector_store.py   # Vector database setup and configuration
│
├── venv/                 # Python virtual environment (Git ignored)
│
├── .env                  # Local environment variables (Git ignored)
├── .gitignore            # Security rules to hide API keys and local data
├── app.py                # Main UI, Session State Memory, and audio routing
├── check.py              # Local testing and debugging script
└── requirements.txt      # Package dependencies for cloud deployment

## 🛠️ Installation & Setup

Follow these steps to get CareerSprint running on your local machine:

```bash
# 1. Clone the repository
git clone [https://github.com/PratyusaP/CareerSprint.git](https://github.com/PratyusaP/CareerSprint.git)
cd CareerSprint

# 2. Create and activate a virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
# Create a .env file in the root directory and add: GEMINI_API_KEY="your_api_key_here"

# 5. Run the application
streamlit run app.py

