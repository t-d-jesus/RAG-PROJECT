def contains_keywords(answer: str, expected_keywords: list[str]) -> bool:
    answer_lower = answer.lower()

    return all(keyword.lower() in answer_lower for keyword in expected_keywords)


def source_found(
    actual_sources: list[str],
    expected_sources: list[str],
) -> bool:
    if not expected_sources:
        return True

    actual = set(actual_sources)

    return any(expected_source in actual for expected_source in expected_sources)


def sources_from_dicts(sources: list[dict]) -> list[str]:
    return [source["source"] for source in sources]
