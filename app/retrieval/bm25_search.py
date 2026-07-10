import re

from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def calculate_bm25_scores(
    question: str,
    candidates: list[tuple],
) -> list[float]:
    if not candidates:
        return []

    tokenized_documents = [tokenize(document) for document, _, _ in candidates]

    bm25 = BM25Okapi(tokenized_documents)

    return list(
        bm25.get_scores(
            tokenize(question),
        )
    )
