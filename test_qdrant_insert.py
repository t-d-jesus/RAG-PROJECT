# test_qdrant_insert.py

from uuid import uuid4

from app.vectorstore.qdrant_store import add_chunks

add_chunks(
    ids=[str(uuid4())],
    chunks=["Sydney Sweeney IMDb"],
    embeddings=[[0.1] * 1536],
    metadatas=[
        {
            "source": "teste.txt",
            "document_type": "document",
        }
    ],
    collection_name="documents",
)

print("insert ok")
