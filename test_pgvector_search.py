from app.embeddings.openai_embeddings import create_embedding
from app.vectorstore.pgvector_store import search_chunks


query_embedding = create_embedding("Sydney Sweeney IMDb")

results = search_chunks(
    query_embedding=query_embedding,
    n_results=3,
    collection_name="documents",
)

print(results.keys())
print(results["documents"][0])
print(results["metadatas"][0])
print(results["distances"][0])
