from opensearchpy import OpenSearch, helpers

from app.config import (
    BM25_WEIGHT,
    EMBEDDING_DIMENSION,
    OPENSEARCH_HOST,
    OPENSEARCH_HYBRID_PIPELINE,
    OPENSEARCH_INDEX_PREFIX,
    OPENSEARCH_PORT,
    OPENSEARCH_USE_SSL,
    OPENSEARCH_VERIFY_CERTS,
    VECTOR_WEIGHT,
)

client = OpenSearch(
    hosts=[
        {
            "host": OPENSEARCH_HOST,
            "port": OPENSEARCH_PORT,
        }
    ],
    use_ssl=OPENSEARCH_USE_SSL,
    verify_certs=OPENSEARCH_VERIFY_CERTS,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
)


def get_index_name(
    collection_name: str,
) -> str:
    return f"{OPENSEARCH_INDEX_PREFIX}-{collection_name}"


def ensure_index(
    collection_name: str,
) -> None:
    index_name = get_index_name(collection_name)

    if client.indices.exists(index=index_name):
        return

    client.indices.create(
        index=index_name,
        body={
            "settings": {
                "index": {
                    "knn": True,
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                }
            },
            "mappings": {
                "dynamic": True,
                "properties": {
                    "document": {
                        "type": "text",
                    },
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": EMBEDDING_DIMENSION,
                        "method": {
                            "name": "hnsw",
                            "engine": "lucene",
                            "space_type": "cosinesimil",
                        },
                    },
                    "metadata": {
                        "type": "object",
                        "dynamic": True,
                    },
                },
            },
        },
    )


def add_chunks(
    ids: list[str],
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    collection_name: str = "documents",
) -> None:
    ensure_index(collection_name)

    index_name = get_index_name(collection_name)

    actions = [
        {
            "_op_type": "index",
            "_index": index_name,
            "_id": chunk_id,
            "_source": {
                "document": chunk,
                "embedding": embedding,
                "metadata": metadata,
            },
        }
        for chunk_id, chunk, embedding, metadata in zip(
            ids,
            chunks,
            embeddings,
            metadatas,
        )
    ]

    helpers.bulk(
        client,
        actions,
        refresh=True,
    )


def build_filter(
    where: dict | None,
) -> list[dict]:
    if not where:
        return []

    return [
        {
            "term": {
                f"metadata.{key}.keyword": value,
            }
        }
        for key, value in where.items()
    ]


def search_chunks(
    query_embedding: list[float],
    n_results: int = 5,
    where: dict | None = None,
    collection_name: str = "documents",
) -> dict:
    ensure_index(collection_name)

    index_name = get_index_name(collection_name)

    knn_query: dict = {
        "vector": query_embedding,
        "k": n_results,
    }

    filters = build_filter(where)

    if filters:
        knn_query["filter"] = {
            "bool": {
                "must": filters,
            }
        }

    response = client.search(
        index=index_name,
        body={
            "size": n_results,
            "query": {
                "knn": {
                    "embedding": knn_query,
                }
            },
        },
    )

    documents = []
    metadatas = []
    distances = []

    for hit in response["hits"]["hits"]:
        source = hit["_source"]

        documents.append(source["document"])
        metadatas.append(source["metadata"])

        score = float(hit["_score"])

        distance = max(
            0.0,
            1.0 - score,
        )

        distances.append(distance)

    return {
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances],
    }


def source_exists(
    source: str,
    collection_name: str = "documents",
) -> bool:
    ensure_index(collection_name)

    response = client.count(
        index=get_index_name(collection_name),
        body={
            "query": {
                "term": {
                    "metadata.source.keyword": source,
                }
            }
        },
    )

    return response["count"] > 0


def reset_collection(
    collection_name: str = "documents",
) -> None:
    index_name = get_index_name(collection_name)

    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)

    ensure_index(collection_name)


def reset_all_collections() -> None:
    pattern = f"{OPENSEARCH_INDEX_PREFIX}-*"

    if client.indices.exists(index=pattern):
        client.indices.delete(index=pattern)


def get_chunks_by_parent_id(
    parent_id: str,
    collection_name: str = "documents",
) -> list[tuple[str, dict]]:
    ensure_index(collection_name)

    response = client.search(
        index=get_index_name(collection_name),
        body={
            "size": 1000,
            "query": {
                "term": {
                    "metadata.parent_id.keyword": parent_id,
                }
            },
            "sort": [
                {
                    "metadata.chunk_index": {
                        "order": "asc",
                        "unmapped_type": "long",
                    }
                }
            ],
        },
    )

    return [
        (
            hit["_source"]["document"],
            hit["_source"]["metadata"],
        )
        for hit in response["hits"]["hits"]
    ]


def get_neighbor_chunks(
    source: str,
    chunk_index: int,
    window: int = 1,
    collection_name: str = "documents",
) -> list[tuple[str, dict]]:
    ensure_index(collection_name)

    start_index = max(chunk_index - window, 0)
    end_index = chunk_index + window

    response = client.search(
        index=get_index_name(collection_name),
        body={
            "size": (window * 2) + 1,
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "metadata.source.keyword": source,
                            }
                        },
                        {
                            "range": {
                                "metadata.chunk_index": {
                                    "gte": start_index,
                                    "lte": end_index,
                                }
                            }
                        },
                    ]
                }
            },
            "sort": [
                {
                    "metadata.chunk_index": {
                        "order": "asc",
                        "unmapped_type": "long",
                    }
                }
            ],
        },
    )

    return [
        (
            hit["_source"]["document"],
            hit["_source"]["metadata"],
        )
        for hit in response["hits"]["hits"]
    ]


def ensure_hybrid_pipeline() -> None:
    if not abs((BM25_WEIGHT + VECTOR_WEIGHT) - 1.0) < 1e-9:
        raise ValueError("BM25_WEIGHT e VECTOR_WEIGHT devem somar 1.0.")

    client.transport.perform_request(
        "PUT",
        f"/_search/pipeline/{OPENSEARCH_HYBRID_PIPELINE}",
        body={
            "description": ("Normalize and combine BM25 and vector scores."),
            "phase_results_processors": [
                {
                    "normalization-processor": {
                        "normalization": {
                            "technique": "min_max",
                        },
                        "combination": {
                            "technique": "arithmetic_mean",
                            "parameters": {
                                "weights": [
                                    BM25_WEIGHT,
                                    VECTOR_WEIGHT,
                                ],
                            },
                        },
                    }
                }
            ],
        },
    )


def build_hybrid_filter(
    where: dict | None,
) -> dict | None:
    if not where:
        return None

    conditions = [
        {
            "term": {
                f"metadata.{key}.keyword": value,
            }
        }
        for key, value in where.items()
    ]

    if len(conditions) == 1:
        return conditions[0]

    return {
        "bool": {
            "must": conditions,
        }
    }


def search_hybrid_chunks(
    question: str,
    query_embedding: list[float],
    n_results: int = 5,
    where: dict | None = None,
    collection_name: str = "documents",
) -> dict:
    ensure_index(collection_name)
    ensure_hybrid_pipeline()

    hybrid_query: dict = {
        "queries": [
            {
                "match": {
                    "document": {
                        "query": question,
                    }
                }
            },
            {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": n_results,
                    }
                }
            },
        ]
    }

    search_filter = build_hybrid_filter(where)

    if search_filter:
        hybrid_query["filter"] = search_filter

    response = client.search(
        index=get_index_name(collection_name),
        params={
            "search_pipeline": OPENSEARCH_HYBRID_PIPELINE,
        },
        body={
            "size": n_results,
            "_source": {
                "excludes": ["embedding"],
            },
            "query": {
                "hybrid": hybrid_query,
            },
        },
    )

    documents = []
    metadatas = []
    distances = []
    scores = []

    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        score = float(hit["_score"] or 0.0)

        documents.append(source["document"])
        metadatas.append(source["metadata"])
        scores.append(score)

        # Compatibilidade temporária com o pipeline atual.
        # Não representa distância vetorial pura.
        normalized_score = min(max(score, 0.0), 1.0)
        distances.append(1.0 - normalized_score)

    return {
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances],
        "scores": [scores],
    }
