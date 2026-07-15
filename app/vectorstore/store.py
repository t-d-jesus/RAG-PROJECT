from app.config import VECTOR_STORE

if VECTOR_STORE == "opensearch":
    from app.vectorstore.opensearch_store import (
        add_chunks,
        get_chunks_by_parent_id,
        get_neighbor_chunks,
        reset_all_collections,
        reset_collection,
        search_chunks,
        source_exists,
    )
elif VECTOR_STORE == "qdrant":
    from app.vectorstore.qdrant_store import (
        add_chunks,
        get_chunks_by_parent_id,
        get_neighbor_chunks,
        reset_all_collections,
        reset_collection,
        search_chunks,
        source_exists,
    )
elif VECTOR_STORE == "pgvector":
    from app.vectorstore.pgvector_store import (
        add_chunks,
        get_chunks_by_parent_id,
        get_neighbor_chunks,
        reset_all_collections,
        reset_collection,
        search_chunks,
        source_exists,
    )
else:
    from app.vectorstore.chroma_store import (
        add_chunks,
        get_chunks_by_parent_id,
        get_neighbor_chunks,
        reset_all_collections,
        reset_collection,
        search_chunks,
        source_exists,
    )


__all__ = [
    "add_chunks",
    "get_chunks_by_parent_id",
    "get_neighbor_chunks",
    "reset_all_collections",
    "reset_collection",
    "search_chunks",
    "source_exists",
]
