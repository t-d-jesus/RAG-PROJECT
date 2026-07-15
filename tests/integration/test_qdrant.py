# test_qdrant.py
from app.vectorstore.qdrant_store import ensure_collection

ensure_collection("documents")

print("ok")
