import os
import streamlit as st
import google.generativeai as genai
try:
    # 1. Try to get it from Streamlit Cloud Secrets (for deployment)
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    # 2. Fall back to your local config file (for your laptop)
    from config.settings import GEMINI_API_KEY

# Configure the API with your key
genai.configure(api_key=GEMINI_API_KEY)

print("🔍 Fetching available models for your API key...\n")

# Loop through and print only the models that generate text
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"✅ Model Name: {m.name}")

        