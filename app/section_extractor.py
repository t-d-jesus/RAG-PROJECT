import re
import unicodedata


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_text.lower())
    return slug.strip("_") or "sem_titulo"


def is_section_title(paragraph: str) -> bool:
    text = paragraph.strip()

    if not text:
        return False

    if len(text) > 100:
        return False

    if text.startswith("#"):
        return True

    words = text.split()

    if len(words) > 12:
        return False

    letters = [char for char in text if char.isalpha()]

    if letters and all(char.isupper() for char in letters):
        return True

    return False


def extract_sections(text: str) -> list[dict[str, str]]:
    paragraphs = [
        paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()
    ]

    sections = []
    current_title = "documento"
    current_paragraphs = []

    for paragraph in paragraphs:
        if is_section_title(paragraph):
            if current_paragraphs:
                sections.append(
                    {
                        "title": current_title,
                        "section_id": slugify(current_title),
                        "text": "\n".join(current_paragraphs),
                    }
                )

            current_title = paragraph.lstrip("#").strip()
            current_paragraphs = []
            continue

        current_paragraphs.append(paragraph)

    if current_paragraphs:
        sections.append(
            {
                "title": current_title,
                "section_id": slugify(current_title),
                "text": "\n".join(current_paragraphs),
            }
        )

    if not sections and text.strip():
        sections.append(
            {
                "title": "documento",
                "section_id": "documento",
                "text": text.strip(),
            }
        )

    return sections
