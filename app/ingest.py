from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.chunker import chunk_text
from app.config import DATA_PATH
from app.embeddings.openai_embeddings import create_embedding
from app.loaders.docx_loader import load_docx
from app.loaders.image_loader import load_image
from app.loaders.pdf_loader import load_pdf
from app.section_extractor import extract_sections
from app.vectorstore.store import add_chunks, source_exists


def get_document_type(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix in [".pdf", ".docx"]:
        return "document"

    if suffix in [".jpg", ".jpeg", ".png"]:
        return "image"

    return "unknown"


def get_collection_name(file_path: Path) -> str:
    document_type = get_document_type(file_path)

    if document_type == "image":
        return "images"

    return "documents"


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
    collection_name = get_collection_name(file_path)

    if source_exists(
        file_path.name,
        collection_name=collection_name,
    ):
        print(f"{file_path.name}: já indexado, pulando")
        return

    text = load_file(file_path)
    sections = extract_sections(text)

    ids = []
    chunks = []
    embeddings = []
    metadatas = []

    indexed_at = datetime.now(timezone.utc).isoformat()
    global_chunk_index = 0

    for section_index, section in enumerate(sections):
        section_chunks = chunk_text(section["text"])

        parent_id = f"{file_path.name}::section_{section['section_id']}"

        for section_chunk_index, chunk in enumerate(section_chunks):
            ids.append(str(uuid4()))
            chunks.append(chunk)
            embeddings.append(create_embedding(chunk))

            metadatas.append(
                {
                    "source": file_path.name,
                    "file_type": file_path.suffix.lower(),
                    "document_type": get_document_type(file_path),
                    "collection_name": collection_name,
                    "chunk_index": global_chunk_index,
                    "section_chunk_index": section_chunk_index,
                    "section_index": section_index,
                    "section_title": section["title"],
                    "section_id": section["section_id"],
                    "parent_id": parent_id,
                    "parent_index": section_index,
                    "indexed_at": indexed_at,
                }
            )

            global_chunk_index += 1

    add_chunks(
        ids=ids,
        chunks=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        collection_name=collection_name,
    )

    print(f"{file_path.name}: {len(chunks)} chunks em {len(sections)} seções indexados")


if __name__ == "__main__":
    data_path = Path(DATA_PATH)

    for file_path in data_path.iterdir():
        if file_path.is_file():
            ingest_file(file_path)
