import chromadb

from app.config import CHROMA_PATH

client = chromadb.PersistentClient(path=CHROMA_PATH)

collection = client.get_or_create_collection(name="documents")


def add_chunks(
    ids: list[str],
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
) -> None:
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def search_chunks(
    query_embedding: list[float],
    n_results: int = 5,
    where: dict | None = None,
) -> dict:
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )


def source_exists(source: str) -> bool:
    results = collection.get(
        where={"source": source},
        limit=1,
    )

    return len(results["ids"]) > 0


def reset_collection() -> None:
    global collection

    try:
        client.delete_collection(name="documents")
    except ValueError:
        pass

    collection = client.get_or_create_collection(name="documents")


def get_neighbor_chunks(
    source: str,
    chunk_index: int,
    window: int = 1,
) -> list[tuple[str, dict]]:
    start_index = max(chunk_index - window, 0)
    end_index = chunk_index + window

    results = collection.get(
        where={
            "$and": [
                {"source": source},
                {"chunk_index": {"$gte": start_index}},
                {"chunk_index": {"$lte": end_index}},
            ]
        },
        include=[
            "documents",
            "metadatas",
        ],
    )

    items = list(
        zip(
            results["documents"],
            results["metadatas"],
        )
    )

    return sorted(
        items,
        key=lambda item: item[1]["chunk_index"],
    )
