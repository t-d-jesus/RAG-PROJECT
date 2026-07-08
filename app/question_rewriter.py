from openai import OpenAI

from app.config import CHAT_MODEL, OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def rewrite_question(question: str, conversation_history: list[dict]) -> str:

    if not conversation_history:
        return question

    history_text = "\n".join(
        [f"{item['role']}: {item['content']}" for item in conversation_history]
    )

    response = client.responses.create(
        model=CHAT_MODEL,
        input=f"""
Reescreva a pergunta do usuário para que ela fique completa
e independente do histórico.

Histórico:
{history_text}

Pergunta:
{question}

Retorne apenas a pergunta reescrita.
""",
    )

    return response.output_text.strip()
