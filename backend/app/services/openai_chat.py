from typing import List

import openai

from app.core.config import settings
from app.schemas.chat import ChatMessage


class OpenAIChatService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def chat_completion(
        self,
        messages: List[dict],
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 256,
        temperature: float = 0.7,
    ) -> str:
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content


openai_chat_service = OpenAIChatService()
