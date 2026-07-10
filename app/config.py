import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY não encontrada no .env")

# app/config.py

# Models

CHAT_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"

# Storage

CHROMA_PATH = "chroma_db"
DATA_PATH = "data/raw"

# Retrieval

RETRIEVAL_RESULTS = 20
RERANK_TOP_K = 3

ENABLE_DISTANCE_FILTER = False
MAX_DISTANCE = 1.8
LOW_CONFIDENCE_DISTANCE = 1.8

# Context

MAX_CONTEXT_CHUNKS = 3
MAX_CONTEXT_CHARS = 6000

# Conversation

MAX_HISTORY_MESSAGES = 10

PARENT_CHUNK_SIZE = 5
VECTOR_WEIGHT = 0.6
BM25_WEIGHT = 0.4
