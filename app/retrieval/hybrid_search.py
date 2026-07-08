from app.retrieval.keyword_search import keyword_score


def hybrid_ranking(
    question: str,
    candidates: list[tuple],
) -> list[tuple]:

    scored = []

    for document, metadata, distance in candidates:
        vector_score = 1 / (1 + distance)

        keyword_match_score = keyword_score(
            question,
            document,
        )

        final_score = vector_score + keyword_match_score

        scored.append(
            (
                final_score,
                document,
                metadata,
                distance,
            )
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True,
    )

    return [
        (document, metadata, distance) for _, document, metadata, distance in scored
    ]
