def build_context(
    selected_chunks: list[tuple],
    max_chunks: int,
    max_chars: int,
) -> tuple[str, list[dict]]:

    context_parts = []
    citations = []
    current_size = 0

    for idx, (document, metadata, distance) in enumerate(
        selected_chunks[:max_chunks],
        start=1,
    ):
        reference = f"[{idx}]"

        chunk_text = (
            f"{reference}\n"
            f"Fonte: {metadata['source']}\n"
            f"Tipo: {metadata.get('file_type')}\n"
            f"Chunk: {metadata.get('chunk_index')}\n"
            f"Distância: {distance:.4f}\n"
            f"Conteúdo:\n{document}\n\n"
        )

        if current_size + len(chunk_text) > max_chars:
            break

        context_parts.append(chunk_text)

        citations.append(
            {
                "reference": reference,
                "source": metadata["source"],
                "chunk_index": metadata.get("chunk_index"),
                "file_type": metadata.get("file_type"),
                "distance": distance,
            }
        )

        current_size += len(chunk_text)

    return "\n".join(context_parts), citations
