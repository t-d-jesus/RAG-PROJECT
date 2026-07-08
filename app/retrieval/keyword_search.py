from collections import Counter


def keyword_score(
    query: str,
    document: str,
) -> int:

    query_words = query.lower().split()

    document_words = document.lower().split()

    counter = Counter(document_words)

    return sum(counter[word] for word in query_words)
