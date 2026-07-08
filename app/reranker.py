import json
import re

from openai import OpenAI

from app.config import CHAT_MODEL, OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def extract_json_array(text: str) -> list[int]:
    match = re.search(r"\[[\d,\s]+\]", text)

    if not match:
        return []

    return json.loads(match.group(0))


def rerank(question: str, documents: list[str], top_k: int = 3) -> list[int]:
    docs_text = "\n\n".join(
        f"[{index}] {document[:1500]}" for index, document in enumerate(documents)
    )

    response = client.responses.create(
        model=CHAT_MODEL,
        input=f"""
Você é um re-ranker de RAG.

Pergunta:
{question}

Chunks candidatos:
{docs_text}

Retorne somente um array JSON válido.
Não explique nada.
Não use markdown.

Exemplo:
[0,2,1]
""",
    )

    indexes = extract_json_array(response.output_text)

    valid_indexes = [
        index
        for index in indexes
        if isinstance(index, int) and 0 <= index < len(documents)
    ]

    if not valid_indexes:
        return list(range(min(top_k, len(documents))))

    return valid_indexes[:top_k]
