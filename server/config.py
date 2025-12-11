import os
import google.generativeai as genai
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from logger import logger

# Load environment variables
load_dotenv()

# Environment variable setup
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "medicalindex")
DATABASE_URL = os.getenv("DATABASE_URL")
# --JWT--
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# --- Namespace Config ---
GLOBAL_KB_NAMESPACE = "global_kb"

# Configuration checks
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found in .env file")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file")
if not DATABASE_URL:
    raise ValueError("DataBase URL not found in .env file")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY not found in .env file. Please generate a strong secret key.")

# Initialize clients once at startup
try:
    logger.info("Initializing global clients...")

    # Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)

    # Google Generative AI
    genai.configure(api_key=GOOGLE_API_KEY)

    # Google Embeddings model
    embed_model = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GOOGLE_API_KEY
    )

    # Groq LLM
    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile",
        temperature=0.7
    )

    logger.info("Global clients initialized successfully.")

except Exception as e:
    logger.error(f"Failed to initialize global clients: {e}")
    raise