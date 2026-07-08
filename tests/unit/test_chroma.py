from app.embeddings.openai_embeddings import create_embedding
from app.vectorstore.chroma_store import add_chunks, search_chunks

text = "Python é muito usado em engenharia de dados e projetos de RAG."

embedding = create_embedding(text)

add_chunks(
    ids=["test-1"],
    chunks=[text],
    embeddings=[embedding],
    metadatas=[{"source": "manual_test"}],
)

query_embedding = create_embedding("Para que Python é usado?")

results = search_chunks(query_embedding)

print(results["documents"])
print(results["metadatas"])
