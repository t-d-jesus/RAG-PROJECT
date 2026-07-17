import re
import unicodedata


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        text,
    )

    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )

    return re.sub(
        r"\s+",
        " ",
        without_accents.lower(),
    ).strip()


def contains_keywords(
    answer: str,
    expected_keywords: list[str],
) -> bool:
    normalized_answer = normalize_text(answer)

    return all(
        normalize_text(keyword) in normalized_answer for keyword in expected_keywords
    )


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
