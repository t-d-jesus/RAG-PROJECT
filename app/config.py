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

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma")
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
VECTOR_WEIGHT = 0.7
BM25_WEIGHT = 0.3


EMBEDDING_DIMENSION = 1536

VECTOR_STORE = os.getenv(
    "VECTOR_STORE",
    "pgvector",
).lower()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "rag")
POSTGRES_USER = os.getenv("POSTGRES_USER", "rag")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rag")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_PATH = os.getenv("QDRANT_PATH", "./qdrant_data")

OPENSEARCH_HOST = os.getenv(
    "OPENSEARCH_HOST",
    "localhost",
)

OPENSEARCH_PORT = int(
    os.getenv(
        "OPENSEARCH_PORT",
        "9200",
    )
)

OPENSEARCH_USE_SSL = (
    os.getenv(
        "OPENSEARCH_USE_SSL",
        "false",
    ).lower()
    == "true"
)

OPENSEARCH_VERIFY_CERTS = (
    os.getenv(
        "OPENSEARCH_VERIFY_CERTS",
        "false",
    ).lower()
    == "true"
)

OPENSEARCH_INDEX_PREFIX = os.getenv(
    "OPENSEARCH_INDEX_PREFIX",
    "rag",
)


OPENSEARCH_HYBRID_PIPELINE = os.getenv(
    "OPENSEARCH_HYBRID_PIPELINE",
    "rag-hybrid-pipeline",
)
