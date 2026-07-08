def detect_metadata_filter(question: str) -> dict | None:
    question_lower = question.lower()

    if any(
        term in question_lower
        for term in ["imagem", "imagens", "foto", "fotos", "print"]
    ):
        return {"document_type": "image"}

    if "pdf" in question_lower or "pdfs" in question_lower:
        return {"file_type": ".pdf"}

    if "docx" in question_lower or "word" in question_lower:
        return {"file_type": ".docx"}

    if any(term in question_lower for term in ["documento", "documentos"]):
        return {"document_type": "document"}

    return None
