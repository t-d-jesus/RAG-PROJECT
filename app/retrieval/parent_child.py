from app.vectorstore.store import get_neighbor_chunks


def expand_with_neighbors(
    selected_chunks: list[tuple],
    window: int = 1,
) -> list[tuple]:
    expanded = []
    seen = set()

    for document, metadata, distance in selected_chunks:
        source = metadata["source"]
        chunk_index = metadata["chunk_index"]

        neighbors = get_neighbor_chunks(
            source=source,
            chunk_index=chunk_index,
            window=window,
        )

        for neighbor_document, neighbor_metadata in neighbors:
            key = (
                neighbor_metadata["source"],
                neighbor_metadata["chunk_index"],
            )

            if key in seen:
                continue

            seen.add(key)

            expanded.append(
                (
                    neighbor_document,
                    neighbor_metadata,
                    distance,
                )
            )

    return expanded
