from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.chunker import chunk_text
from app.config import DATA_PATH
from app.embeddings.openai_embeddings import create_embedding
from app.loaders.docx_loader import load_docx
from app.loaders.image_loader import load_image
from app.loaders.pdf_loader import load_pdf
from app.vectorstore.chroma_store import add_chunks, source_exists


def get_document_type(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix in [".pdf", ".docx"]:
        return "document"

    if suffix in [".jpg", ".jpeg", ".png"]:
        return "image"

    return "unknown"


def load_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf(str(file_path))

    if suffix == ".docx":
        return load_docx(str(file_path))

    if suffix in [".jpg", ".jpeg", ".png"]:
        return load_image(str(file_path))

    raise ValueError(f"Tipo não suportado: {suffix}")


def ingest_file(file_path: Path) -> None:
    if source_exists(file_path.name):
        print(f"{file_path.name}: já indexado, pulando")
        return

    text = load_file(file_path)
    chunks = chunk_text(text)

    embeddings = [create_embedding(chunk) for chunk in chunks]

    ids = [str(uuid4()) for _ in chunks]

    indexed_at = datetime.now(timezone.utc).isoformat()

    metadatas = [
        {
            "source": file_path.name,
            "file_type": file_path.suffix.lower(),
            "document_type": get_document_type(file_path),
            "chunk_index": index,
            "indexed_at": indexed_at,
        }
        for index, _ in enumerate(chunks)
    ]

    add_chunks(
        ids=ids,
        chunks=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"{file_path.name}: {len(chunks)} chunks indexados")


if __name__ == "__main__":
    data_path = Path(DATA_PATH)

    for file_path in data_path.iterdir():
        if file_path.is_file():
            ingest_file(file_path)
