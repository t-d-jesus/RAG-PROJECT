from uuid import uuid4

from app.vectorstore.chroma_store import (
    add_chunks,
    reset_collection,
    search_chunks,
)


def test_chroma_adds_and_searches_chunks() -> None:
    collection_name = f"test_{uuid4().hex}"

    try:
        add_chunks(
            ids=[str(uuid4())],
            chunks=["Python é usado em engenharia de dados."],
            embeddings=[[0.1] * 1536],
            metadatas=[{"source": "test.txt"}],
            collection_name=collection_name,
        )

        results = search_chunks(
            query_embedding=[0.1] * 1536,
            n_results=1,
            collection_name=collection_name,
        )

        assert results["documents"][0]
        assert results["documents"][0][0] == ("Python é usado em engenharia de dados.")
    finally:
        reset_collection(collection_name)
