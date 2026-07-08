def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 1 <= chunk_size:
            current_chunk += "\n" + paragraph if current_chunk else paragraph
        else:
            if current_chunk:
                chunks.append(current_chunk)

            overlap_text = current_chunk[-chunk_overlap:] if current_chunk else ""
            current_chunk = overlap_text + "\n" + paragraph

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
