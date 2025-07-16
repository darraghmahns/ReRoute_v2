from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse, ChatMessage
from app.services.openai_chat import openai_chat_service
from app.core.security import get_current_active_user
from app.models.user import User
from typing import List
from fastapi import Request

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory chat history for demo (replace with DB in production)
user_chat_history = {}

@router.post("/message", response_model=ChatResponse)
def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send chat message to OpenAI and get response"""
    user_id = str(current_user.id)
    messages = [msg.dict() for msg in chat_request.messages]
    try:
        ai_content = openai_chat_service.chat_completion(
            messages=messages,
            model=chat_request.model,
            max_tokens=chat_request.max_tokens,
            temperature=chat_request.temperature
        )
        ai_message = ChatMessage(role="assistant", content=ai_content)
        # Save to in-memory history
        if user_id not in user_chat_history:
            user_chat_history[user_id] = []
        user_chat_history[user_id].extend(chat_request.messages)
        user_chat_history[user_id].append(ai_message)
        return ChatResponse(message=ai_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI chat failed: {str(e)}")

@router.get("/history", response_model=ChatHistoryResponse)
def get_history(current_user: User = Depends(get_current_active_user)):
    """Get conversation history for the current user"""
    user_id = str(current_user.id)
    history = user_chat_history.get(user_id, [])
    return ChatHistoryResponse(history=history)

@router.delete("/history")
def clear_history(current_user: User = Depends(get_current_active_user)):
    """Clear chat history for the current user"""
    user_id = str(current_user.id)
    user_chat_history[user_id] = []
    return {"message": "Chat history cleared"} 