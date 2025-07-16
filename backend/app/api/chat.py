import re
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from dateutil import parser as date_parser

from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse, ChatMessage  # schema
from app.services.openai_chat import openai_chat_service
from app.core.security import get_current_active_user
from app.core.database import get_db
from app.models.user import User, Profile
from app.models.chat import ChatMessage as ChatMessageDB
from app.models.training import TrainingPlan
from typing import List
from app.models.strava import StravaActivity

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


def _strava_streams_summary(db: Session, user: User, limit: int = 3) -> str:
    """Return a summary of recent Strava activities and their streams."""
    acts = (
        db.query(StravaActivity)
        .filter(StravaActivity.user_id == user.id)
        .order_by(StravaActivity.created_at.desc())
        .limit(limit)
        .all()
    )
    if not acts:
        return "No recent Strava activities with streams."
    lines = []
    for a in acts:
        line = f"{a.name or 'Activity'} (id: {a.id}): "
        if a.streams:
            stream_types = list(a.streams.keys())
            line += f"streams: {', '.join(stream_types)}"
            # Optionally, add a short stat, e.g. max watts, avg heartrate
            if 'watts' in a.streams and a.streams['watts'].get('data'):
                max_watts = max(a.streams['watts']['data'])
                line += f", max watts: {max_watts}"
            if 'heartrate' in a.streams and a.streams['heartrate'].get('data'):
                avg_hr = sum(a.streams['heartrate']['data']) / len(a.streams['heartrate']['data'])
                line += f", avg HR: {avg_hr:.1f}"
        else:
            line += "no streams"
        lines.append(line)
    return "Recent Strava activities with streams:\n" + "\n".join(lines)


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


def _parse_timeframe_or_activity(message: str):
    """Very basic NLP to extract timeframes or activity references from the user's message."""
    message = message.lower()
    # Look for 'last X days/weeks'
    m = re.search(r'last (\d+) (day|week|month|year)s?', message)
    if m:
        num = int(m.group(1))
        unit = m.group(2)
        if unit == 'day':
            return {'type': 'timeframe', 'days': num}
        elif unit == 'week':
            return {'type': 'timeframe', 'days': num * 7}
        elif unit == 'month':
            return {'type': 'timeframe', 'days': num * 30}
        elif unit == 'year':
            return {'type': 'timeframe', 'days': num * 365}
    # Look for 'on <date>'
    m = re.search(r'on ([a-zA-Z0-9 ,/-]+)', message)
    if m:
        try:
            dt = date_parser.parse(m.group(1), fuzzy=True)
            return {'type': 'date', 'date': dt.date()}
        except Exception:
            pass
    # Look for activity id
    m = re.search(r'activity (\d+)', message)
    if m:
        return {'type': 'activity_id', 'id': int(m.group(1))}
    # Look for 'recent', 'latest', etc.
    if 'recent' in message or 'latest' in message or 'most recent' in message:
        return {'type': 'recent', 'count': 1}
    return None


def _strava_adaptive_context(db: Session, user: User, user_message: str) -> str:
    """Build a context string for the AI based on the user's message."""
    parsed = _parse_timeframe_or_activity(user_message)
    if parsed:
        if parsed['type'] == 'timeframe':
            cutoff = datetime.utcnow() - timedelta(days=parsed['days'])
            acts = (
                db.query(StravaActivity)
                .filter(StravaActivity.user_id == user.id, StravaActivity.created_at >= cutoff)
                .order_by(StravaActivity.created_at.desc())
                .all()
            )
            if not acts:
                return f"No Strava activities found in the last {parsed['days']} days."
            return _format_activities_with_streams(acts)
        elif parsed['type'] == 'date':
            # Find activities on that date
            acts = (
                db.query(StravaActivity)
                .filter(StravaActivity.user_id == user.id)
                .all()
            )
            acts_on_date = [a for a in acts if a.summary and 'start_date' in a.summary and date_parser.parse(a.summary['start_date']).date() == parsed['date']]
            if not acts_on_date:
                return f"No Strava activities found on {parsed['date']}."
            return _format_activities_with_streams(acts_on_date)
        elif parsed['type'] == 'activity_id':
            act = db.query(StravaActivity).filter(StravaActivity.user_id == user.id, StravaActivity.id == parsed['id']).first()
            if not act:
                return f"No Strava activity found with id {parsed['id']}."
            return _format_activities_with_streams([act])
        elif parsed['type'] == 'recent':
            acts = (
                db.query(StravaActivity)
                .filter(StravaActivity.user_id == user.id)
                .order_by(StravaActivity.created_at.desc())
                .limit(1)
                .all()
            )
            if not acts:
                return "No recent Strava activities found."
            return _format_activities_with_streams(acts)
    # Default: summary only
    acts = (
        db.query(StravaActivity)
        .filter(StravaActivity.user_id == user.id)
        .order_by(StravaActivity.created_at.desc())
        .limit(5)
        .all()
    )
    if not acts:
        return "No Strava activities found."
    lines = [f"{a.name or 'Activity'} (id: {a.id}, date: {a.summary.get('start_date', 'unknown')[:10]})" for a in acts]
    return (
        "Summary of recent Strava activities (name, id, date):\n" +
        "\n".join(lines) +
        "\nIf you want to analyze a specific activity or time period, ask the user for more details."
    )

def _format_activities_with_streams(acts):
    lines = []
    for a in acts:
        line = f"{a.name or 'Activity'} (id: {a.id}, date: {a.summary.get('start_date', 'unknown')[:10]}): "
        if a.streams:
            stream_types = list(a.streams.keys())
            line += f"streams: {', '.join(stream_types)}"
            if 'watts' in a.streams and a.streams['watts'].get('data'):
                max_watts = max(a.streams['watts']['data'])
                line += f", max watts: {max_watts}"
            if 'heartrate' in a.streams and a.streams['heartrate'].get('data'):
                avg_hr = sum(a.streams['heartrate']['data']) / len(a.streams['heartrate']['data'])
                line += f", avg HR: {avg_hr:.1f}"
        else:
            line += "no streams"
        lines.append(line)
    return "Detailed Strava activity data:\n" + "\n".join(lines)


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

    user_msg = ""
    if db.query(ChatMessageDB).filter(ChatMessageDB.user_id == user.id).order_by(ChatMessageDB.created_at.desc()).first():
        user_msg = db.query(ChatMessageDB).filter(ChatMessageDB.user_id == user.id).order_by(ChatMessageDB.created_at.desc()).first().content
    content_sections = [
        "You are Reroute AI, a friendly cycling training assistant.",
        "You have access to all of the user's Strava activities and their detailed streams (power, heart rate, etc.).",
        "When the user asks about a specific activity, date, or time period, use the relevant data to answer. If the user is not specific, ask clarifying questions to help them get the most relevant analysis.",
        "Profile: " + "; ".join(prof_parts) if prof_parts else "No profile information.",
        _strava_summary(db, user),
        _training_plan_summary(db, user),
        _strava_adaptive_context(db, user, user_msg),
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