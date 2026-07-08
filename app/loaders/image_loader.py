import base64
import mimetypes

from openai import OpenAI

from app.config import CHAT_MODEL, OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def load_image(file_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(file_path)

    if mime_type is None:
        mime_type = "image/jpeg"

    with open(file_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    response = client.responses.create(
        model=CHAT_MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": """
                                Analise a imagem e gere um documento textual para indexação em um sistema RAG.

                                Regras:

                                1. Transcreva todo texto visível.
                                2. Descreva os elementos visuais importantes.
                                3. Preserve títulos.
                                4. Preserve nomes próprios encontrados no conteúdo.
                                5. Não use markdown.
                                6. Não use listas.
                                7. Produza texto corrido otimizado para busca semântica.

                                Retorne apenas o documento.
                                """,
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:{mime_type};base64,{image_base64}",
                    },
                ],
            }
        ],
    )

    print(response.output_text)

    return f"""
            ARQUIVO: {file_path}

            {response.output_text}
            """
