from openai import OpenAI

from app.config import EMBEDDING_MODEL, OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def create_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )

    return response.data[0].embedding
