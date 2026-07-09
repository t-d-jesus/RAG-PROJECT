import chromadb

from app.config import CHROMA_PATH

client = chromadb.PersistentClient(path=CHROMA_PATH)


def get_collection(collection_name: str = "documents"):
    return client.get_or_create_collection(name=collection_name)


def add_chunks(
    ids: list[str],
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    collection_name: str = "documents",
) -> None:
    collection = get_collection(collection_name)

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
    collection_name: str = "documents",
) -> dict:
    collection = get_collection(collection_name)

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


def source_exists(
    source: str,
    collection_name: str = "documents",
) -> bool:
    collection = get_collection(collection_name)

    results = collection.get(
        where={"source": source},
        limit=1,
    )

    return len(results["ids"]) > 0


def reset_collection(collection_name: str = "documents") -> None:
    try:
        client.delete_collection(name=collection_name)
    except ValueError:
        pass

    client.get_or_create_collection(name=collection_name)


def reset_all_collections() -> None:
    for collection in client.list_collections():
        client.delete_collection(name=collection.name)


def get_neighbor_chunks(
    source: str,
    chunk_index: int,
    window: int = 1,
    collection_name: str = "documents",
) -> list[tuple[str, dict]]:
    collection = get_collection(collection_name)

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


def get_chunks_by_parent_id(
    parent_id: str,
    collection_name: str = "documents",
) -> list[tuple[str, dict]]:
    collection = get_collection(collection_name)

    results = collection.get(
        where={"parent_id": parent_id},
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
