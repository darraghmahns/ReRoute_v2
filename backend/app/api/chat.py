from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse, ChatMessage  # schema
from app.services.openai_chat import openai_chat_service
from app.core.security import get_current_active_user
from app.core.database import get_db
from app.models.user import User, Profile
from app.models.chat import ChatMessage as ChatMessageDB
from typing import List

router = APIRouter(prefix="/chat", tags=["chat"])

# ---- Utility helpers -------------------------------------------------------

HISTORY_DAYS = 14  # two weeks


def _system_context_for_user(db: Session, user: User) -> ChatMessage:
    """Build a system message injecting profile / Strava context for OpenAI."""
    profile: Profile | None = db.query(Profile).filter(Profile.id == user.id).first()
    if not profile:
        content = (
            "You are Reroute AI, a friendly cycling training assistant. "
            "The user has not yet completed their profile, so ask clarifying questions "
            "when you need more information."
        )
    else:
        # Assemble a minimal profile summary string – extend as needed.
        summary_parts: list[str] = []
        if profile.age:
            summary_parts.append(f"age: {profile.age}")
        if profile.gender:
            summary_parts.append(f"gender: {profile.gender}")
        if profile.weight_lbs:
            summary_parts.append(f"weight_lbs: {profile.weight_lbs}")
        if profile.height_ft and profile.height_in is not None:
            summary_parts.append(
                f"height: {profile.height_ft} ft {profile.height_in} in"
            )
        if profile.primary_goals:
            summary_parts.append(f"primary goals: {profile.primary_goals}")
        if profile.fitness_level:
            summary_parts.append(f"fitness level: {profile.fitness_level}")

        content = (
            "You are Reroute AI, a friendly cycling training assistant. "
            "Here is the latest user profile summary (you should use this as context, "
            "but do not reveal it directly): "
            + "; ".join(summary_parts)
        )

    return ChatMessage(role="system", content=content)


# ---- Routes ----------------------------------------------------------------

@router.post("/message", response_model=ChatResponse)
def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Send chat message to OpenAI and get response (history persists 2 weeks)."""
    try:
        # Persist incoming user messages
        for msg in chat_request.messages:
            new_msg = ChatMessageDB(
                user_id=current_user.id,
                role=msg.role,
                content=msg.content,
            )
            db.add(new_msg)
        db.commit()

        # Build the message list: system context + last two weeks of history
        cutoff_date = datetime.utcnow() - timedelta(days=HISTORY_DAYS)
        history_rows: List[ChatMessageDB] = (
            db.query(ChatMessageDB)
            .filter(ChatMessageDB.user_id == current_user.id, ChatMessageDB.created_at >= cutoff_date)
            .order_by(ChatMessageDB.created_at.asc())
            .all()
        )

        messages_for_openai: List[dict] = []
        # System context
        system_msg = _system_context_for_user(db, current_user)
        messages_for_openai.append(system_msg.dict())
        # Historical messages
        messages_for_openai.extend(
            {"role": m.role, "content": m.content} for m in history_rows
        )

        # OpenAI completion
        ai_content: str = openai_chat_service.chat_completion(
            messages=messages_for_openai,
            model=chat_request.model,
            max_tokens=chat_request.max_tokens,
            temperature=chat_request.temperature,
        )

        # Persist assistant response
        assistant_msg_db = ChatMessageDB(
            user_id=current_user.id,
            role="assistant",
            content=ai_content,
        )
        db.add(assistant_msg_db)
        db.commit()

        # Naive hook: if the last user message asks to update the training plan, call the placeholder endpoint
        last_user_content = chat_request.messages[-1].content.lower() if chat_request.messages else ""
        if "update" in last_user_content and "training" in last_user_content and "plan" in last_user_content:
            # NOTE: training plan logic is still a placeholder in app.api.training
            # Here we simply record that a request was made; in a real implementation you would
            # parse `last_user_content` and apply the requested modifications.
            from app.api import training as training_api  # lazy import to avoid cycles
            try:
                training_api.ai_update_plan(id="current",)  # type: ignore[arg-type]
            except Exception:
                pass  # Ignore errors from placeholder

        ai_message_schema = ChatMessage(role="assistant", content=ai_content)
        return ChatResponse(message=ai_message_schema)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"OpenAI chat failed: {str(e)}")


@router.get("/history", response_model=ChatHistoryResponse)
def get_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get conversation history for the current user (last 2 weeks)."""
    cutoff_date = datetime.utcnow() - timedelta(days=HISTORY_DAYS)
    messages: List[ChatMessageDB] = (
        db.query(ChatMessageDB)
        .filter(ChatMessageDB.user_id == current_user.id, ChatMessageDB.created_at >= cutoff_date)
        .order_by(ChatMessageDB.created_at.asc())
        .all()
    )

    history_schema: List[ChatMessage] = [
        ChatMessage(role=m.role, content=m.content) for m in messages
    ]
    return ChatHistoryResponse(history=history_schema)


@router.delete("/history")
def clear_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Clear chat history for the current user (deletes all records)."""
    deleted = (
        db.query(ChatMessageDB)
        .filter(ChatMessageDB.user_id == current_user.id)
        .delete()
    )
    db.commit()
    return {"message": f"Deleted {deleted} chat messages"} 