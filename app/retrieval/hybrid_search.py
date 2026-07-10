from app.config import BM25_WEIGHT, VECTOR_WEIGHT
from app.retrieval.bm25_search import calculate_bm25_scores


def normalize_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []

    minimum = min(scores)
    maximum = max(scores)

    if maximum == minimum:
        return [0.0 for _ in scores]

    return [(score - minimum) / (maximum - minimum) for score in scores]


def hybrid_ranking(
    question: str,
    candidates: list[tuple],
) -> list[tuple]:
    if not candidates:
        return []

    vector_scores = [1 / (1 + distance) for _, _, distance in candidates]

    bm25_scores = calculate_bm25_scores(
        question=question,
        candidates=candidates,
    )

    normalized_vector_scores = normalize_scores(vector_scores)
    normalized_bm25_scores = normalize_scores(bm25_scores)

    scored_candidates = []

    for (
        candidate,
        vector_score,
        bm25_score,
    ) in zip(
        candidates,
        normalized_vector_scores,
        normalized_bm25_scores,
    ):
        document, metadata, distance = candidate

        hybrid_score = VECTOR_WEIGHT * vector_score + BM25_WEIGHT * bm25_score

        scored_candidates.append(
            (
                hybrid_score,
                document,
                metadata,
                distance,
            )
        )

    scored_candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        (document, metadata, distance)
        for _, document, metadata, distance in scored_candidates
    ]
