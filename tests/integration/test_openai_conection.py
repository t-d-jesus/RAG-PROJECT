from openai import OpenAI

from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

response = client.responses.create(
    model="gpt-4o-mini", input="Responda apenas: conexão ok"
)

print(response.output_text)
