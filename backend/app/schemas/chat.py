from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender: user, assistant, or system")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Conversation history including the new user message")
    model: Optional[str] = Field("gpt-3.5-turbo", description="OpenAI model to use")
    max_tokens: Optional[int] = Field(256, description="Maximum tokens in the response")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")

class ChatResponse(BaseModel):
    message: ChatMessage

class ChatHistoryResponse(BaseModel):
    history: List[ChatMessage] 