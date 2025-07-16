import re
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse, ChatMessage  # schema
from app.services.openai_chat import openai_chat_service
from app.core.security import get_current_active_user
from app.core.database import get_db
from app.models.user import User, Profile
from app.models.chat import ChatMessage as ChatMessageDB
from app.models.training import TrainingPlan
from typing import List

router = APIRouter(prefix="/chat", tags=["chat"])

# ---- Utility helpers -------------------------------------------------------

HISTORY_DAYS = 14  # two weeks


def _strava_summary(db: Session, user: User) -> str:
    """Return a quick summary of recent Strava activities."""
    profile: Profile | None = db.query(Profile).filter(Profile.id == user.id).first()
    if not profile or not profile.strava_access_token:
        return "Strava not connected."
    try:
        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {profile.strava_access_token}"}
        response = requests.get(activities_url, headers=headers, params={"per_page": 5})
        if response.status_code != 200:
            return "Unable to fetch Strava activities at this time."
        acts = response.json()
        if not acts:
            return "No recent Strava activities."
        summary_items = [
            f"{a.get('name')} - {round(a.get('distance', 0)/1000, 1)}km" for a in acts
        ]
        return "Recent activities: " + "; ".join(summary_items)
    except Exception:
        return "Unable to fetch Strava activities."


def _training_plan_summary(db: Session, user: User) -> str:
    plan: TrainingPlan | None = (
        db.query(TrainingPlan).filter(TrainingPlan.user_id == user.id).first()
    )
    if not plan:
        return "No training plan defined yet."
    details = plan.details or {}
    weekly_hours = details.get("weekly_training_hours")
    goal = details.get("goal")
    parts = []
    if weekly_hours:
        parts.append(f"weekly_training_hours={weekly_hours}")
    if goal:
        parts.append(f"goal={goal}")
    return "Current training plan: " + ", ".join(parts)


def _system_context_for_user(db: Session, user: User) -> ChatMessage:
    """Build a system message injecting profile / Strava context for OpenAI."""
    profile: Profile | None = db.query(Profile).filter(Profile.id == user.id).first()
    prof_parts: list[str] = []
    if profile:
        if profile.age:
            prof_parts.append(f"age: {profile.age}")
        if profile.gender:
            prof_parts.append(f"gender: {profile.gender}")
        if profile.weight_lbs:
            prof_parts.append(f"weight_lbs: {profile.weight_lbs}")
        if profile.height_ft and profile.height_in is not None:
            prof_parts.append(f"height: {profile.height_ft} ft {profile.height_in} in")
        if profile.primary_goals:
            prof_parts.append(f"primary goals: {profile.primary_goals}")
        if profile.fitness_level:
            prof_parts.append(f"fitness level: {profile.fitness_level}")

    content_sections = [
        "You are Reroute AI, a friendly cycling training assistant.",
        "Profile: " + "; ".join(prof_parts) if prof_parts else "No profile information.",
        _strava_summary(db, user),
        _training_plan_summary(db, user),
    ]
    content = "\n".join(content_sections)
    return ChatMessage(role="system", content=content)


# ---- Training plan updater --------------------------------------------------

UPDATE_PATTERN = re.compile(r"change\s+(?P<field>[a-zA-Z_]+)\s+(?:to|=)\s+(?P<value>[\w\s]+)")


def _parse_and_update_training_plan(db: Session, user: User, message: str) -> tuple[bool, str]:
    """Detect update instructions and apply them. Returns (updated?, feedback)."""
    match = UPDATE_PATTERN.search(message.lower())
    if not match:
        return False, ""
    field = match.group("field")
    value_raw = match.group("value").strip()
    # Try to cast numeric
    value: str | int | float
    if value_raw.isdigit():
        value = int(value_raw)
    else:
        try:
            value = float(value_raw)
        except ValueError:
            value = value_raw

    plan: TrainingPlan | None = (
        db.query(TrainingPlan).filter(TrainingPlan.user_id == user.id).first()
    )
    if not plan:
        # create new plan
        plan = TrainingPlan(user_id=user.id, details={})
        db.add(plan)

    if plan.details is None:
        plan.details = {}
    plan.details[field] = value
    plan.updated_at = datetime.utcnow()
    db.commit()
    feedback = f"Your training plan has been updated: {field} -> {value}."
    return True, feedback


# ---- Routes ----------------------------------------------------------------

@router.post("/message", response_model=ChatResponse)
def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Send chat message with enhanced context and training plan management."""
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

        # Check for training plan update in the last user message
        last_user_content = chat_request.messages[-1].content if chat_request.messages else ""
        updated, feedback_msg = _parse_and_update_training_plan(db, current_user, last_user_content)
        if updated:
            # Return immediate confirmation without OpenAI call
            assistant_msg_db = ChatMessageDB(
                user_id=current_user.id,
                role="assistant",
                content=feedback_msg,
            )
            db.add(assistant_msg_db)
            db.commit()
            ai_message_schema = ChatMessage(role="assistant", content=feedback_msg)
            return ChatResponse(message=ai_message_schema)

        # Otherwise proceed with OpenAI chat
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