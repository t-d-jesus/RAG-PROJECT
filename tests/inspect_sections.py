from app.vectorstore.chroma_store import list_chunks


def inspect_collection(collection_name: str) -> None:
    print(f"\nCollection: {collection_name}")

    chunks = list_chunks(collection_name)

    for item in chunks:
        metadata = item["metadata"]

        print(
            f"- source={metadata.get('source')} "
            f"| section_title={metadata.get('section_title')} "
            f"| section_id={metadata.get('section_id')} "
            f"| parent_id={metadata.get('parent_id')} "
            f"| chunk_index={metadata.get('chunk_index')}"
        )


if __name__ == "__main__":
    inspect_collection("documents")
    inspect_collection("images")
