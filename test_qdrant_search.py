# test_qdrant_search.py

from app.embeddings.openai_embeddings import create_embedding
from app.vectorstore.qdrant_store import search_chunks

query_embedding = create_embedding("Sydney Sweeney")

results = search_chunks(
    query_embedding=query_embedding,
    n_results=3,
    collection_name="documents",
)

print(results.keys())
print(len(results["documents"][0]))
