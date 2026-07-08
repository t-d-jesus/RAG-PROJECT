from docx import Document


def load_docx(file_path: str) -> str:
    doc = Document(file_path)

    paragraphs = []

    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs)
