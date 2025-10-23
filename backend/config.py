import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Qdrant settings
COLLECTION_NAME = "codelens_docs"
VECTOR_SIZE = 384  # for all-MiniLM-L6-v2

# Model settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "llama-3.3-70b-versatile"  # Groq's best model

# Chunking settings (OPTIMIZED)
CHUNK_SIZE = 800        # Increased from 500 for better context
CHUNK_OVERLAP = 100     # Increased overlap for continuity
