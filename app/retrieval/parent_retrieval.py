from app.vectorstore.store import get_chunks_by_parent_id


def expand_with_parent(
    selected_chunks: list[tuple],
) -> list[tuple]:
    expanded = []
    seen = set()

    for document, metadata, distance in selected_chunks:
        source = metadata["source"]
        chunk_index = metadata["chunk_index"]

        original_key = (source, chunk_index)

        # Primeiro mantém o chunk selecionado pelo reranker.
        if original_key not in seen:
            seen.add(original_key)

            expanded.append(
                (
                    document,
                    metadata,
                    distance,
                )
            )

        parent_id = metadata.get("parent_id")

        if not parent_id:
            continue

        collection_name = metadata.get(
            "collection_name",
            "documents",
        )

        parent_chunks = get_chunks_by_parent_id(
            parent_id=parent_id,
            collection_name=collection_name,
        )

        # Depois adiciona os outros chunks do mesmo parent.
        for parent_document, parent_metadata in parent_chunks:
            key = (
                parent_metadata["source"],
                parent_metadata["chunk_index"],
            )

            if key in seen:
                continue

            seen.add(key)

            expanded.append(
                (
                    parent_document,
                    parent_metadata,
                    distance,
                )
            )

    return expanded
