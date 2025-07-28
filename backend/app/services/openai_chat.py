from typing import List

import openai

from app.core.config import settings
from app.schemas.chat import ChatMessage


class OpenAIChatService:
    def __init__(self):
        # Lazy initialization to ensure settings are loaded
        self.client = None

    def _get_client(self):
        if self.client is None:
            api_key = settings.OPENAI_API_KEY
            if not api_key or api_key == "changeme":
                raise ValueError(
                    f"OpenAI API key not configured. Current value: {api_key[:20]}..."
                )
            self.client = openai.OpenAI(api_key=api_key)
        return self.client

    def chat_completion(
        self,
        messages: List[dict],
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 256,
        temperature: float = 0.7,
    ) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content


openai_chat_service = OpenAIChatService()
