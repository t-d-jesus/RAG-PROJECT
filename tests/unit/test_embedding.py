from app.embeddings.openai_embeddings import create_embedding

embedding = create_embedding("Teste de embedding para RAG")

print(type(embedding))
print(len(embedding))
print(embedding[:5])
