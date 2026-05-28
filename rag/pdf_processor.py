import os
import streamlit as st
import tempfile
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

try:
    # 1. Try to get it from Streamlit Cloud Secrets (for deployment)
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    # 2. Fall back to your local config file (for your laptop)
    from config.settings import GEMINI_API_KEY

# Ensure pytesseract can find the Windows executable
# If you installed Tesseract somewhere else, update this path!
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialize the Embeddings Model
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2",
    google_api_key=GEMINI_API_KEY
)

def process_uploaded_resume(uploaded_file):
    """
    Processes a PDF. Tries standard text extraction first. 
    If it fails (e.g., Canva resume), silently falls back to OCR image scanning.
    """
    # 1. Save the Streamlit file to a temporary location on disk
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_file.read())
        temp_pdf_path = temp_file.name

    try:
        documents = []
        
        # ==========================================
        # ATTEMPT 1: Standard Fast Text Extraction
        # ==========================================
        loader = PyPDFLoader(temp_pdf_path)
        standard_docs = loader.load()
        
        # Combine all extracted text to check if it's empty
        extracted_text = "".join([doc.page_content for doc in standard_docs]).strip()

        # ==========================================
        # ATTEMPT 2: The Silent OCR Fallback
        # ==========================================
        # If the text is empty or suspiciously short, it's likely an image-based PDF
        if len(extracted_text) < 50:
            print("Standard extraction failed. Triggering silent OCR fallback...")
            
            ocr_text = ""
            # Open the PDF with PyMuPDF to render pages as images
            pdf_document = fitz.open(temp_pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                # Render page to an image (zoom factor 2 for better OCR resolution)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                
                # Convert the PyMuPDF pixmap to a standard PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Run the OCR engine on the image
                page_text = pytesseract.image_to_string(img)
                ocr_text += page_text + "\n"
                
            pdf_document.close()
            
            # Wrap the OCR text back into LangChain's Document format
            documents = [Document(page_content=ocr_text, metadata={"source": uploaded_file.name})]
            print("OCR Successful!")
            
        else:
            # If standard extraction worked, just use those documents
            documents = standard_docs

        # ==========================================
        # FINAL STEP: Split and Save to FAISS
        # ==========================================
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)

        # Remove the old database to avoid mixing resumes
        if os.path.exists("faiss_index"):
            import shutil
            shutil.rmtree("faiss_index")

        # Build and save the new Vector Database
        vectorstore = FAISS.from_documents(chunks, embeddings)
        vectorstore.save_local("faiss_index")

    finally:
        # Always clean up the temporary file, even if an error occurs
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)