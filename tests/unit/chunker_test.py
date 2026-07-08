from app.chunker import chunk_text

texto = (
    """
Lorem ipsum...
"""
    * 500
)

chunks = chunk_text(texto)

print(f"Chunks: {len(chunks)}")

for i, chunk in enumerate(chunks[:3]):
    print(f"\nChunk {i + 1}")
    print(chunk[:100])
