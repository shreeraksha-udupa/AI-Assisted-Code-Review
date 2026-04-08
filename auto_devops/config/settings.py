import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq-hosted model — fast, free tier available
# Options: "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"
MODEL = "llama-3.3-70b-versatile"

CHROMA_PATH = "./chroma_db"
EMBED_MODEL = "all-MiniLM-L6-v2"   # local sentence-transformers model, no API needed
CHUNK_SIZE = 60
CHUNK_OVERLAP = 10
RETRIEVAL_TOP_K = 5
SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".go", ".java", ".cpp", ".rb"}
