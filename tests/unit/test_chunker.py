from app.chunker import chunk_text


def test_chunk_text_returns_chunks() -> None:
    text = "Primeiro parágrafo.\n\nSegundo parágrafo."

    chunks = chunk_text(text)

    assert chunks
    assert isinstance(chunks, list)
    assert all(isinstance(chunk, str) for chunk in chunks)


def test_chunk_text_returns_empty_list_for_empty_text() -> None:
    chunks = chunk_text("")

    assert chunks == []
