from app.vectorstore.chroma_store import get_chunks_by_parent_id


def expand_with_parent(
    selected_chunks: list[tuple],
    collection_name: str = "documents",
) -> list[tuple]:
    expanded = []
    seen = set()

    for document, metadata, distance in selected_chunks:
        parent_id = metadata.get("parent_id")

        if not parent_id:
            expanded.append((document, metadata, distance))
            continue

        parent_chunks = get_chunks_by_parent_id(
            parent_id=parent_id,
            collection_name=collection_name,
        )

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
