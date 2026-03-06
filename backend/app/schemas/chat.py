from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(
        ..., description="Role of the message sender: user, assistant, or system"
    )
    content: str = Field(..., description="Content of the message")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(
        ..., description="Conversation history including the new user message"
    )
    model: Optional[str] = Field("gpt-3.5-turbo", description="OpenAI model to use")
    max_tokens: Optional[int] = Field(
        1024, description="Maximum tokens in the response"
    )
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")


class ActionResult(BaseModel):
    """Represents a structured action the AI agent took, rendered as an inline card."""

    type: str = Field(..., description="Action type identifier, e.g. 'route_generated'")
    title: str = Field(..., description="Short display title for the card")
    description: str = Field(..., description="One-line summary of what changed")
    data: Dict[str, Any] = Field(default_factory=dict, description="Type-specific payload")
    nav_url: str = Field(..., description="Frontend route to navigate to, e.g. '/routes'")


class ChatResponse(BaseModel):
    message: ChatMessage
    actions: List[ActionResult] = Field(default_factory=list)


class ChatHistoryResponse(BaseModel):
    history: List[ChatMessage]
