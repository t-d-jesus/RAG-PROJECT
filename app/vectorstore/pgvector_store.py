import psycopg
from pgvector.psycopg import register_vector
import json
from uuid import UUID

from app.config import (
    EMBEDDING_DIMENSION,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)
from pgvector import Vector


def get_connection() -> psycopg.Connection:
    connection = psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )

    register_vector(connection)

    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS vector_documents (
                    id UUID PRIMARY KEY,
                    collection_name TEXT NOT NULL,
                    document TEXT NOT NULL,
                    embedding VECTOR({EMBEDDING_DIMENSION}) NOT NULL,
                    metadata JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_vector_documents_collection
                ON vector_documents (collection_name)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_vector_documents_metadata
                ON vector_documents
                USING GIN (metadata)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_vector_documents_embedding_hnsw
                ON vector_documents
                USING hnsw (embedding vector_cosine_ops)
                """
            )


def add_chunks(
    ids: list[str],
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    collection_name: str = "documents",
) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            rows = [
                (
                    UUID(chunk_id),
                    collection_name,
                    chunk,
                    embedding,
                    json.dumps(metadata),
                )
                for chunk_id, chunk, embedding, metadata in zip(
                    ids,
                    chunks,
                    embeddings,
                    metadatas,
                )
            ]

            cursor.executemany(
                """
                INSERT INTO vector_documents (
                    id,
                    collection_name,
                    document,
                    embedding,
                    metadata
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s::jsonb
                )
                """,
                rows,
            )


def search_chunks(
    query_embedding: list[float],
    n_results: int = 5,
    where: dict | None = None,
    collection_name: str = "documents",
) -> dict:
    conditions = ["collection_name = %s"]
    filter_parameters: list = [collection_name]

    if where:
        for key, value in where.items():
            conditions.append("metadata ->> %s = %s")
            filter_parameters.extend([key, str(value)])

    where_clause = " AND ".join(conditions)

    query_vector = Vector(query_embedding)

    parameters = [
        query_vector,
        *filter_parameters,
        query_vector,
        n_results,
    ]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    document,
                    metadata,
                    embedding <=> %s AS distance
                FROM vector_documents
                WHERE {where_clause}
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                parameters,
            )

            rows = cursor.fetchall()

    documents = []
    metadatas = []
    distances = []

    for document, metadata, distance in rows:
        documents.append(document)
        metadatas.append(metadata)
        distances.append(float(distance))

    return {
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances],
    }


def source_exists(
    source: str,
    collection_name: str = "documents",
) -> bool:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM vector_documents
                    WHERE collection_name = %s
                      AND metadata ->> 'source' = %s
                )
                """,
                [collection_name, source],
            )

            result = cursor.fetchone()

    return bool(result and result[0])


def reset_collection(
    collection_name: str = "documents",
) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM vector_documents
                WHERE collection_name = %s
                """,
                [collection_name],
            )


def reset_all_collections() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                TRUNCATE TABLE vector_documents
                """
            )


def get_chunks_by_parent_id(
    parent_id: str,
    collection_name: str = "documents",
) -> list[tuple[str, dict]]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    document,
                    metadata
                FROM vector_documents
                WHERE collection_name = %s
                  AND metadata ->> 'parent_id' = %s
                ORDER BY
                    (metadata ->> 'chunk_index')::integer
                """,
                [collection_name, parent_id],
            )

            rows = cursor.fetchall()

    return [
        (
            document,
            metadata,
        )
        for document, metadata in rows
    ]


def get_neighbor_chunks(
    source: str,
    chunk_index: int,
    window: int = 1,
    collection_name: str = "documents",
) -> list[tuple[str, dict]]:
    start_index = max(chunk_index - window, 0)
    end_index = chunk_index + window

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    document,
                    metadata
                FROM vector_documents
                WHERE collection_name = %s
                  AND metadata ->> 'source' = %s
                  AND (metadata ->> 'chunk_index')::integer
                      BETWEEN %s AND %s
                ORDER BY
                    (metadata ->> 'chunk_index')::integer
                """,
                [
                    collection_name,
                    source,
                    start_index,
                    end_index,
                ],
            )

            rows = cursor.fetchall()

    return [
        (
            document,
            metadata,
        )
        for document, metadata in rows
    ]
