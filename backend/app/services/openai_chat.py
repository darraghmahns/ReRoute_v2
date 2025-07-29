from typing import List, Optional, Dict, Any
import json
import logging

import openai

from app.core.config import settings
from app.schemas.chat import ChatMessage

logger = logging.getLogger(__name__)


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
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
    ) -> Dict[str, Any]:
        """
        Enhanced chat completion with function calling support.

        Returns:
            Dict containing:
            - content: The assistant's text response (if any)
            - tool_calls: List of tool calls the AI wants to make (if any)
            - finish_reason: How the response ended
        """
        client = self._get_client()

        # Prepare the API call
        api_params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Add tools if provided
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = tool_choice
            logger.info(f"Making OpenAI call with {len(tools)} tools available")

        response = client.chat.completions.create(**api_params)

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        result = {
            "content": message.content,
            "tool_calls": [],
            "finish_reason": finish_reason,
        }

        # Handle tool calls if present
        if message.tool_calls:
            for tool_call in message.tool_calls:
                try:
                    parsed_args = json.loads(tool_call.function.arguments)
                    result["tool_calls"].append(
                        {
                            "id": tool_call.id,
                            "name": tool_call.function.name,
                            "arguments": parsed_args,
                        }
                    )
                    logger.info(f"AI requested tool call: {tool_call.function.name}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse tool arguments: {e}")
                    result["tool_calls"].append(
                        {
                            "id": tool_call.id,
                            "name": tool_call.function.name,
                            "arguments": {},
                            "error": "Failed to parse arguments",
                        }
                    )

        return result

    def chat_completion_simple(
        self,
        messages: List[dict],
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 256,
        temperature: float = 0.7,
    ) -> str:
        """Simple chat completion that returns just the text content (backward compatibility)."""
        result = self.chat_completion(messages, model, max_tokens, temperature)
        return result["content"] or ""


openai_chat_service = OpenAIChatService()
