import atexit

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.config import EMBEDDING_DIMENSION, QDRANT_PATH

client = QdrantClient(path=QDRANT_PATH)

atexit.register(client.close)


def ensure_collection(
    collection_name: str,
) -> None:
    if client.collection_exists(collection_name):
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=EMBEDDING_DIMENSION,
            distance=Distance.COSINE,
        ),
    )


def build_filter(
    where: dict | None,
) -> Filter | None:
    if not where:
        return None

    conditions = [
        FieldCondition(
            key=key,
            match=MatchValue(value=value),
        )
        for key, value in where.items()
    ]

    return Filter(must=conditions)


def add_chunks(
    ids: list[str],
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    collection_name: str = "documents",
) -> None:
    ensure_collection(collection_name)

    points = [
        PointStruct(
            id=chunk_id,
            vector=embedding,
            payload={
                "document": chunk,
                **metadata,
            },
        )
        for chunk_id, chunk, embedding, metadata in zip(
            ids,
            chunks,
            embeddings,
            metadatas,
        )
    ]

    client.upsert(
        collection_name=collection_name,
        points=points,
        wait=True,
    )


def search_chunks(
    query_embedding: list[float],
    n_results: int = 5,
    where: dict | None = None,
    collection_name: str = "documents",
) -> dict:
    ensure_collection(collection_name)

    results = client.query_points(
        collection_name=collection_name,
        query=query_embedding,
        query_filter=build_filter(where),
        limit=n_results,
        with_payload=True,
        with_vectors=False,
    )

    documents = []
    metadatas = []
    distances = []

    for point in results.points:
        payload = point.payload or {}

        document = payload.get("document")

        if document is None:
            continue

        metadata = {key: value for key, value in payload.items() if key != "document"}

        documents.append(document)
        metadatas.append(metadata)

        # Como usamos cosine similarity:
        # score maior = melhor.
        # O restante do projeto espera distância menor = melhor.
        distances.append(1.0 - point.score)

    return {
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances],
    }


def source_exists(
    source: str,
    collection_name: str = "documents",
) -> bool:
    ensure_collection(collection_name)

    records, _ = client.scroll(
        collection_name=collection_name,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="source",
                    match=MatchValue(value=source),
                )
            ]
        ),
        limit=1,
        with_payload=False,
        with_vectors=False,
    )

    return bool(records)


def reset_collection(
    collection_name: str = "documents",
) -> None:
    if client.collection_exists(collection_name):
        client.delete_collection(
            collection_name=collection_name,
        )

    ensure_collection(collection_name)


def reset_all_collections() -> None:
    collections = client.get_collections().collections

    for collection in collections:
        client.delete_collection(
            collection_name=collection.name,
        )


def get_chunks_by_parent_id(
    parent_id: str,
    collection_name: str = "documents",
) -> list[tuple[str, dict]]:
    ensure_collection(collection_name)

    records = []
    next_offset = None

    while True:
        page, next_offset = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="parent_id",
                        match=MatchValue(value=parent_id),
                    )
                ]
            ),
            limit=100,
            offset=next_offset,
            with_payload=True,
            with_vectors=False,
        )

        records.extend(page)

        if next_offset is None:
            break

    items = []

    for record in records:
        payload = record.payload or {}
        document = payload.get("document")

        if document is None:
            continue

        metadata = {key: value for key, value in payload.items() if key != "document"}

        items.append(
            (
                document,
                metadata,
            )
        )

    return sorted(
        items,
        key=lambda item: item[1].get("chunk_index", 0),
    )


def get_neighbor_chunks(
    source: str,
    chunk_index: int,
    window: int = 1,
    collection_name: str = "documents",
) -> list[tuple[str, dict]]:
    ensure_collection(collection_name)

    start_index = max(chunk_index - window, 0)
    end_index = chunk_index + window

    records = []

    for current_index in range(start_index, end_index + 1):
        page, _ = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source),
                    ),
                    FieldCondition(
                        key="chunk_index",
                        match=MatchValue(value=current_index),
                    ),
                ]
            ),
            limit=1,
            with_payload=True,
            with_vectors=False,
        )

        records.extend(page)

    items = []

    for record in records:
        payload = record.payload or {}
        document = payload.get("document")

        if document is None:
            continue

        metadata = {key: value for key, value in payload.items() if key != "document"}

        items.append(
            (
                document,
                metadata,
            )
        )

    return sorted(
        items,
        key=lambda item: item[1].get("chunk_index", 0),
    )
