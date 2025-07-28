import logging
import re
from datetime import datetime, timedelta
from typing import List

import requests
from dateutil import parser as date_parser
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user_by_session
from app.models.chat import ChatMessage as ChatMessageDB
from app.models.strava import StravaActivity
from app.models.training import TrainingPlan
from app.models.user import Profile, User
from app.schemas.chat import (  # schema
    ChatHistoryResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
)
from app.services.openai_chat import openai_chat_service

router = APIRouter(prefix="/chat", tags=["chat"])

# ---- Utility helpers -------------------------------------------------------

HISTORY_DAYS = 14  # two weeks


def _strava_summary(db: Session, user: User) -> str:
    """Return a quick summary of recent Strava activities."""
    try:
        profile: Profile | None = (
            db.query(Profile).filter(Profile.id == user.id).first()
        )
        if not profile or not profile.strava_access_token:
            return "Strava not connected."
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
            if "watts" in a.streams and a.streams["watts"].get("data"):
                max_watts = max(a.streams["watts"]["data"])
                line += f", max watts: {max_watts}"
            if "heartrate" in a.streams and a.streams["heartrate"].get("data"):
                avg_hr = sum(a.streams["heartrate"]["data"]) / len(
                    a.streams["heartrate"]["data"]
                )
                line += f", avg HR: {avg_hr:.1f}"
        else:
            line += "no streams"
        lines.append(line)
    return "Recent Strava activities with streams:\n" + "\n".join(lines)


def _training_plan_summary(db: Session, user: User) -> str:
    try:
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
    except Exception:
        return "Unable to retrieve training plan information."


def _parse_timeframe_or_activity(message: str):
    """Very basic NLP to extract timeframes or activity references from the user's message."""
    message = message.lower()
    # Look for 'last X days/weeks'
    m = re.search(r"last (\d+) (day|week|month|year)s?", message)
    if m:
        num = int(m.group(1))
        unit = m.group(2)
        if unit == "day":
            return {"type": "timeframe", "days": num}
        elif unit == "week":
            return {"type": "timeframe", "days": num * 7}
        elif unit == "month":
            return {"type": "timeframe", "days": num * 30}
        elif unit == "year":
            return {"type": "timeframe", "days": num * 365}
    # Look for 'on <date>'
    m = re.search(r"on ([a-zA-Z0-9 ,/-]+)", message)
    if m:
        try:
            dt = date_parser.parse(m.group(1), fuzzy=True)
            return {"type": "date", "date": dt.date()}
        except Exception:
            pass
    # Look for activity id
    m = re.search(r"activity (\d+)", message)
    if m:
        return {"type": "activity_id", "id": int(m.group(1))}
    # Look for 'recent', 'latest', etc.
    if "recent" in message or "latest" in message or "most recent" in message:
        return {"type": "recent", "count": 1}
    return None


def _strava_adaptive_context(db: Session, user: User, user_message: str) -> str:
    """Build a context string for the AI based on the user's message."""
    try:
        parsed = _parse_timeframe_or_activity(user_message)
        if not parsed:
            return "No specific timeframe or activity mentioned."
    except Exception:
        return "Unable to parse user message for activity context."

    try:
        if parsed["type"] == "timeframe":
            cutoff = datetime.utcnow() - timedelta(days=parsed["days"])
            acts = (
                db.query(StravaActivity)
                .filter(
                    StravaActivity.user_id == user.id,
                    StravaActivity.created_at >= cutoff,
                )
                .order_by(StravaActivity.created_at.desc())
                .all()
            )
            if not acts:
                return f"No Strava activities found in the last {parsed['days']} days."
            return _format_activities_with_streams(acts)
        elif parsed["type"] == "date":
            # Find activities on that date
            acts = (
                db.query(StravaActivity).filter(StravaActivity.user_id == user.id).all()
            )
            acts_on_date = [
                a
                for a in acts
                if a.summary
                and "start_date" in a.summary
                and date_parser.parse(a.summary["start_date"]).date() == parsed["date"]
            ]
            if not acts_on_date:
                return f"No Strava activities found on {parsed['date']}."
            return _format_activities_with_streams(acts_on_date)
        elif parsed["type"] == "activity_id":
            act = (
                db.query(StravaActivity)
                .filter(
                    StravaActivity.user_id == user.id, StravaActivity.id == parsed["id"]
                )
                .first()
            )
            if not act:
                return f"No Strava activity found with id {parsed['id']}."
            return _format_activities_with_streams([act])
        elif parsed["type"] == "recent":
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
    except Exception as e:
        return f"Error retrieving Strava activity data: {str(e)[:50]}"
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
    lines = [
        f"{a.name or 'Activity'} (id: {a.id}, date: {a.summary.get('start_date', 'unknown')[:10]})"
        for a in acts
    ]
    return (
        "Summary of recent Strava activities (name, id, date):\n"
        + "\n".join(lines)
        + "\nIf you want to analyze a specific activity or time period, ask the user for more details."
    )


def _format_activities_with_streams(acts):
    lines = []
    for a in acts:
        line = f"{a.name or 'Activity'} (id: {a.id}, date: {a.summary.get('start_date', 'unknown')[:10]}): "
        if a.streams:
            stream_types = list(a.streams.keys())
            line += f"streams: {', '.join(stream_types)}"
            if "watts" in a.streams and a.streams["watts"].get("data"):
                max_watts = max(a.streams["watts"]["data"])
                line += f", max watts: {max_watts}"
            if "heartrate" in a.streams and a.streams["heartrate"].get("data"):
                avg_hr = sum(a.streams["heartrate"]["data"]) / len(
                    a.streams["heartrate"]["data"]
                )
                line += f", avg HR: {avg_hr:.1f}"
        else:
            line += "no streams"
        lines.append(line)
    return "Detailed Strava activity data:\n" + "\n".join(lines)


def _get_detailed_user_profile(db: Session, user: User) -> str:
    """Get comprehensive user profile information."""
    try:
        profile: Profile | None = (
            db.query(Profile).filter(Profile.id == user.id).first()
        )
        if not profile:
            return "No profile information available."

        profile_info = []

        # Basic info
        if profile.age:
            profile_info.append(f"Age: {profile.age} years")
        if profile.gender:
            profile_info.append(f"Gender: {profile.gender}")
        if profile.weight_lbs:
            profile_info.append(f"Weight: {profile.weight_lbs} lbs")
        if profile.height_ft and profile.height_in is not None:
            profile_info.append(f"Height: {profile.height_ft}'{profile.height_in}\"")

        # Cycling specifics
        if profile.cycling_experience:
            profile_info.append(f"Cycling Experience: {profile.cycling_experience}")
        if profile.fitness_level:
            profile_info.append(f"Fitness Level: {profile.fitness_level}")
        if profile.weekly_training_hours:
            profile_info.append(
                f"Weekly Training Hours: {profile.weekly_training_hours}"
            )

        # Goals and preferences
        if profile.primary_goals:
            profile_info.append(f"Primary Goals: {profile.primary_goals}")
        if profile.training_preferences:
            profile_info.append(f"Training Preferences: {profile.training_preferences}")
        if profile.preferred_training_days:
            profile_info.append(
                f"Preferred Training Days: {profile.preferred_training_days}"
            )

        # Health considerations
        if profile.injury_history:
            profile_info.append(f"Injury History: {profile.injury_history}")
        if profile.medical_conditions:
            profile_info.append(f"Medical Conditions: {profile.medical_conditions}")

        # Strava connection status
        strava_status = "Connected" if profile.strava_access_token else "Not connected"
        profile_info.append(f"Strava Status: {strava_status}")

        return (
            "\n".join(profile_info)
            if profile_info
            else "Profile information not complete."
        )
    except Exception:
        return "Unable to retrieve profile information."


def _get_recent_activities_with_details(
    db: Session, user: User, limit: int = 10
) -> str:
    """Get detailed recent activities including streams data."""
    try:
        # First, get all activities and sort by actual activity date from summary
        all_activities = (
            db.query(StravaActivity).filter(StravaActivity.user_id == user.id).all()
        )

        # Sort by actual activity start_date from summary data
        activities_with_dates = []
        for activity in all_activities:
            if activity.summary and activity.summary.get("start_date"):
                activities_with_dates.append(activity)

        # Sort by start_date (most recent first)
        activities_with_dates.sort(
            key=lambda x: x.summary.get("start_date", ""), reverse=True
        )

        # Take the most recent activities
        activities = activities_with_dates[:limit]

        if not activities:
            return "No Strava activities found in database. User should sync their Strava data."

        # Check if data seems old
        from datetime import datetime, timedelta

        most_recent_activity_date = (
            activities[0].summary.get("start_date", "")[:10] if activities else ""
        )
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        current_date = datetime.utcnow().strftime("%Y-%m-%d")

        # Debug logging
        logging.info(
            f"Chat context: Found {len(activities)} activities, most recent: {most_recent_activity_date}, current date: {current_date}"
        )

        # Log first few activity dates for debugging
        for i, act in enumerate(activities[:5]):
            act_date = (
                act.summary.get("start_date", "Unknown")[:10]
                if act.summary
                else "Unknown"
            )
            act_name = act.name or "Unnamed"
            logging.info(f"Activity {i+1}: {act_name} - {act_date}")

        data_freshness_note = ""
        if most_recent_activity_date < thirty_days_ago:
            data_freshness_note = f"\n⚠️ **Note: Most recent activity is from {most_recent_activity_date} (current: {current_date}). User should sync recent Strava data to get the latest activities.**\n"

        activity_details = []
        for activity in activities:
            details = []

            # Basic activity info with clear date formatting
            activity_name = activity.name or "Unnamed Activity"
            activity_date = (
                activity.summary.get("start_date", "Unknown date")[:10]
                if activity.summary
                else "Unknown date"
            )

            # Convert date to more readable format for AI matching
            date_display = activity_date
            if activity_date != "Unknown date":
                try:
                    from datetime import datetime

                    parsed_date = datetime.strptime(activity_date, "%Y-%m-%d")
                    date_display = (
                        f"{activity_date} ({parsed_date.strftime('%B %d, %Y')})"
                    )
                except:
                    date_display = activity_date

            details.append(f"**{activity_name}** (ID: {activity.id})")
            details.append(f"**Date: {date_display}**")

            # Summary data
            if activity.summary:
                summary = activity.summary
                if summary.get("distance"):
                    details.append(f"Distance: {summary['distance']/1000:.1f} km")
                if summary.get("moving_time"):
                    hours = summary["moving_time"] // 3600
                    minutes = (summary["moving_time"] % 3600) // 60
                    details.append(f"Moving Time: {hours:02d}:{minutes:02d}")
                if summary.get("average_speed"):
                    details.append(
                        f"Avg Speed: {summary['average_speed']*3.6:.1f} km/h"
                    )
                if summary.get("average_watts"):
                    details.append(f"Avg Power: {summary['average_watts']:.0f}W")
                if summary.get("average_heartrate"):
                    details.append(f"Avg HR: {summary['average_heartrate']:.0f} bpm")
                if summary.get("average_cadence"):
                    details.append(f"Avg Cadence: {summary['average_cadence']:.0f} rpm")
                if summary.get("total_elevation_gain"):
                    details.append(f"Elevation: {summary['total_elevation_gain']:.0f}m")

            # Streams data availability and detailed metrics
            if activity.streams:
                available_streams = list(activity.streams.keys())
                details.append(
                    f"**Detailed stream data available:** {', '.join(available_streams)}"
                )

                # Detailed stream analysis with emphasis on cadence
                streams = activity.streams

                # CADENCE - Prioritize this for user queries
                if "cadence" in streams and streams["cadence"].get("data"):
                    cadence_data = streams["cadence"]["data"]
                    # Filter out zero values for more accurate averages
                    non_zero_cadence = [c for c in cadence_data if c > 0]
                    if non_zero_cadence:
                        avg_cadence = sum(non_zero_cadence) / len(non_zero_cadence)
                        max_cadence = max(cadence_data)
                        min_cadence = (
                            min([c for c in cadence_data if c > 0])
                            if non_zero_cadence
                            else 0
                        )
                        details.append(
                            f"**CADENCE DETAILED:** avg {avg_cadence:.1f} rpm, max {max_cadence:.0f} rpm, min {min_cadence:.0f} rpm ({len(non_zero_cadence)} data points)"
                        )
                    else:
                        details.append("**CADENCE:** No valid cadence data recorded")
                else:
                    details.append("**CADENCE:** Not available in streams")

                # POWER
                if "watts" in streams and streams["watts"].get("data"):
                    power_data = streams["watts"]["data"]
                    non_zero_power = [p for p in power_data if p > 0]
                    if non_zero_power:
                        avg_power = sum(non_zero_power) / len(non_zero_power)
                        max_power = max(power_data)
                        details.append(
                            f"**POWER DETAILED:** avg {avg_power:.0f}W, max {max_power:.0f}W ({len(non_zero_power)} data points)"
                        )

                # HEART RATE
                if "heartrate" in streams and streams["heartrate"].get("data"):
                    hr_data = streams["heartrate"]["data"]
                    non_zero_hr = [hr for hr in hr_data if hr > 0]
                    if non_zero_hr:
                        avg_hr = sum(non_zero_hr) / len(non_zero_hr)
                        max_hr = max(hr_data)
                        min_hr = (
                            min([hr for hr in hr_data if hr > 0]) if non_zero_hr else 0
                        )
                        details.append(
                            f"**HEART RATE DETAILED:** avg {avg_hr:.0f} bpm, max {max_hr:.0f} bpm, min {min_hr:.0f} bpm"
                        )
            else:
                details.append(
                    "**NO DETAILED STREAMS DATA** - Only basic summary available"
                )

            activity_details.append("\n".join(details))

        # Add clear context about what's included
        context_header = (
            f"## 📊 YOUR COMPLETE STRAVA ACTIVITY DATA{data_freshness_note}\n\n"
        )
        context_header += f"**Current Date: {current_date}** - Only activities from July 2024 should be considered 'recent'\n\n"
        context_header += "**⚠️ IMPORTANT: This is ALL the data you have access to. Use this data to answer questions.**\n"
        context_header += (
            f"**Found {len(activities)} activities with detailed metrics below:**\n\n"
        )

        return context_header + "\n\n".join(activity_details)
    except Exception as e:
        return f"Error retrieving activity details: {str(e)[:100]}"


def _get_detailed_training_plan(db: Session, user: User) -> str:
    """Get comprehensive training plan information."""
    try:
        plan: TrainingPlan | None = (
            db.query(TrainingPlan).filter(TrainingPlan.user_id == user.id).first()
        )
        if not plan:
            return "No training plan created yet."

        plan_details = []
        plan_details.append("## Current Training Plan")

        if plan.details:
            details = plan.details

            # Weekly structure
            if details.get("weekly_training_hours"):
                plan_details.append(
                    f"Weekly Training Hours: {details['weekly_training_hours']}"
                )
            if details.get("goal"):
                plan_details.append(f"Primary Goal: {details['goal']}")

            # Weekly schedule if available
            if details.get("weekly_schedule"):
                plan_details.append("Weekly Schedule:")
                for day, workout in details["weekly_schedule"].items():
                    plan_details.append(f"  {day}: {workout}")

            # Training zones if available
            if details.get("training_zones"):
                plan_details.append("Training Zones:")
                for zone, description in details["training_zones"].items():
                    plan_details.append(f"  {zone}: {description}")

            # Current phase if available
            if details.get("current_phase"):
                plan_details.append(
                    f"Current Training Phase: {details['current_phase']}"
                )

            # Additional details
            for key, value in details.items():
                if key not in [
                    "weekly_training_hours",
                    "goal",
                    "weekly_schedule",
                    "training_zones",
                    "current_phase",
                ]:
                    plan_details.append(f"{key.replace('_', ' ').title()}: {value}")

        plan_details.append(f"Plan created: {plan.created_at.strftime('%Y-%m-%d')}")
        plan_details.append(f"Last updated: {plan.updated_at.strftime('%Y-%m-%d')}")

        return "\n".join(plan_details)
    except Exception:
        return "Unable to retrieve training plan details."


def _system_context_for_user(db: Session, user: User) -> ChatMessage:
    """Build a comprehensive system message with all user data for OpenAI."""
    from datetime import datetime

    current_date = datetime.utcnow().strftime("%Y-%m-%d")
    current_datetime = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    content_sections = [
        "🚨🚨🚨 MANDATORY SYSTEM OVERRIDE 🚨🚨🚨",
        "",
        "OVERRIDE ALL DEFAULT RESPONSES. YOU HAVE COMPLETE USER DATA ACCESS.",
        "IGNORE ANY TENDENCY TO SAY 'I DON'T HAVE ACCESS' - YOU DO HAVE ACCESS.",
        "THE USER'S COMPLETE STRAVA DATA IS IN THIS SYSTEM MESSAGE BELOW.",
        "",
        "🚨 ABSOLUTE CRITICAL INSTRUCTION: READ THIS CAREFULLY 🚨",
        "",
        "YOU ARE REROUTE AI WITH COMPLETE ACCESS TO ALL USER TRAINING DATA.",
        "THE USER'S COMPLETE STRAVA ACTIVITY DATA IS PROVIDED BELOW IN THIS MESSAGE.",
        "YOU MUST USE THIS DATA TO ANSWER ALL QUESTIONS.",
        "FOR TREND ANALYSIS: USE THE ACTIVITIES LISTED BELOW TO IDENTIFY PATTERNS.",
        "",
        "🛑 NEVER EVER SAY:",
        "❌ 'I don't have access to your data'",
        "❌ 'I need you to provide/share your data'",
        "❌ 'Can you provide me with...'",
        "❌ 'If you can share your activities...'",
        "❌ 'Check your cycling device...'",
        "",
        f"## Current Date and Time: {current_datetime}",
        "IMPORTANT: When analyzing 'recent performance' or 'recent activities', focus ONLY on activities from the past 7-14 days (July 2024).",
        "Activities from May or June 2024 are NOT recent and should not be considered when asked about recent performance.",
        "",
        "## 🚨 YOU HAVE ALL THE DATA YOU NEED IN THIS MESSAGE",
        "- Complete Strava activity history is listed below",
        "- Detailed metrics including cadence, power, heart rate for each activity",
        "- Stream data (second-by-second measurements) where available",
        "- Activity dates, distances, speeds, elevation gains",
        "- ANALYZE THE DATA PROVIDED BELOW - DO NOT ASK FOR MORE DATA",
        "",
        "## Response Guidelines",
        "- Use markdown formatting for better readability",
        "- Reference specific data points when answering questions",
        "- Use **bold** for key metrics and important information",
        "- Create tables or bullet points for data comparisons",
        "- Always be encouraging and supportive",
        "- When analyzing activities, use the detailed stream data (cadence, power, HR) when available",
        "- ALWAYS check activity dates - only consider July 2024 activities as 'recent'",
        "- ANALYZE THE ACTUAL DATA PROVIDED BELOW - don't ask for more data",
        "",
        "## 🔥 COMPLETE USER DATA - USE THIS TO ANSWER ALL QUESTIONS 🔥",
        "",
        "🚨 THE DATA BELOW IS EVERYTHING YOU NEED - DO NOT ASK FOR MORE 🚨",
        "",
        "### User Profile",
        _get_detailed_user_profile(db, user),
        "",
        "### Training Plan",
        _get_detailed_training_plan(db, user),
        "",
        "### 📊 COMPLETE ACTIVITY DATA - ANALYZE THIS FOR TRENDS",
        _get_recent_activities_with_details(db, user, limit=20),
        "",
        "🚨 END OF DATA - YOU HAVE EVERYTHING NEEDED TO ANSWER QUESTIONS 🚨",
        "",
        "## Important Notes",
        "- You have access to detailed cadence, power, heart rate, and other metrics for activities with stream data",
        "- When users ask about specific dates or activities, reference the actual data above",
        "- If you need data from a specific activity not shown above, you can access it by activity ID",
        "- Always provide specific, data-driven insights based on the information available",
        "",
        "## CRITICAL INSTRUCTIONS:",
        f"- Current date: {current_date}",
        "- When asked about 'recent performance' or 'recent activities', ONLY analyze activities from July 2024",
        "- IGNORE activities from May and June 2024 when asked about recent performance",
        "- If no July 2024 activities are available, explicitly state that recent data needs to be synced",
        "- Always mention the dates of activities you're analyzing to confirm they are truly recent",
        "",
        "## SPECIFIC DATE QUERIES:",
        "- When asked about a specific date (e.g., 'July 11th'), search through ALL activities listed above",
        "- Look for activities with start_date matching the requested date (2024-07-11 for July 11th)",
        "- If you find the activity, provide detailed analysis using the EXACT data shown above",
        "- Use the stream data (CADENCE DETAILED, POWER DETAILED, etc.) if available",
        "- If you see 'CADENCE DETAILED: avg X rpm' - USE THAT DATA, don't ask for more",
        "- If you see 'NO DETAILED STREAMS DATA' - explain what basic data is available instead",
        "- If no activity found for that date, clearly state 'No activity found for [date]' and suggest syncing",
        "",
        "## EXAMPLE RESPONSES:",
        "✅ GOOD: 'Your July 11th ride had an average cadence of 85.2 rpm with a max of 124 rpm based on the stream data.'",
        "❌ BAD: 'I don't have access to your cadence data. Please share it with me.'",
        "❌ BAD: 'You can check your cycling device for cadence data.'",
        "✅ GOOD: 'No activity found for July 11th in your synced data. Try using the Full Refresh button to sync recent activities.'",
        "",
        "✅ GOOD TREND ANALYSIS: 'Based on your activities from July 1-19, I can see several trends: Your average distance has increased from 15km to 25km, your power output is trending upward from 150W to 180W average, and you're riding more consistently with 4 rides per week.'",
        "❌ BAD: 'I don't have access to your complete training data. Please provide your activities.'",
        "❌ BAD: 'Can you share your training data so I can analyze trends?'",
    ]
    content = "\n".join(content_sections)
    return ChatMessage(role="system", content=content)


# ---- Training plan updater --------------------------------------------------

UPDATE_PATTERN = re.compile(
    r"change\s+(?P<field>[a-zA-Z_]+)\s+(?:to|=)\s+(?P<value>[\w\s]+)"
)


def _parse_and_update_training_plan(
    db: Session, user: User, message: str
) -> tuple[bool, str]:
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
    current_user: User = Depends(get_current_active_user_by_session),
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
        last_user_content = (
            chat_request.messages[-1].content if chat_request.messages else ""
        )
        updated, feedback_msg = _parse_and_update_training_plan(
            db, current_user, last_user_content
        )
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
            .filter(
                ChatMessageDB.user_id == current_user.id,
                ChatMessageDB.created_at >= cutoff_date,
            )
            .order_by(ChatMessageDB.created_at.asc())
            .all()
        )

        messages_for_openai: List[dict] = []
        # System context
        try:
            system_msg = _system_context_for_user(db, current_user)
            messages_for_openai.append(system_msg.dict())

            # Debug logging to see what system message is being sent
            logging.info(f"System message length: {len(system_msg.content)} characters")
            logging.info(f"System message preview: {system_msg.content[:500]}...")

        except Exception as e:
            # Fallback system message if context generation fails
            logging.error(f"Failed to generate system context: {e}")
            fallback_msg = ChatMessage(
                role="system",
                content="You are Reroute AI, a friendly cycling training assistant.",
            )
            messages_for_openai.append(fallback_msg.dict())

        # Historical messages
        messages_for_openai.extend(
            {"role": m.role, "content": m.content} for m in history_rows
        )

        # Add current user message (enhanced with data context)
        if chat_request.messages:
            last_user_message = chat_request.messages[-1]
            if last_user_message.role == "user":
                try:
                    # Get user data for injection
                    user_data_summary = _get_recent_activities_with_details(
                        db, current_user, limit=20
                    )

                    # Enhance the user message with explicit data context
                    enhanced_content = f"""USER QUESTION: {last_user_message.content}

IMPORTANT CONTEXT FOR AI: You have access to the user's complete Strava activity data below. Use this data to answer the question. Do not ask for more data.

{user_data_summary}

Based on the activity data above, please answer the user's question: {last_user_message.content}"""

                    # Add the enhanced message
                    messages_for_openai.append(
                        {"role": "user", "content": enhanced_content}
                    )

                    logging.info(
                        f"Enhanced user message with {len(user_data_summary)} characters of activity data"
                    )

                except Exception as e:
                    logging.error(f"Error enhancing user message: {e}")
                    # Fallback to original message
                    messages_for_openai.append(
                        {"role": "user", "content": last_user_message.content}
                    )

        # OpenAI completion
        try:
            logging.info(f"Sending {len(messages_for_openai)} messages to OpenAI")
            logging.info(
                f"Message types: {[msg['role'] for msg in messages_for_openai]}"
            )

            ai_content: str = openai_chat_service.chat_completion(
                messages=messages_for_openai,
                model=chat_request.model or "gpt-3.5-turbo",
                max_tokens=chat_request.max_tokens or 1024,
                temperature=chat_request.temperature or 0.7,
            )

            logging.info(f"OpenAI response length: {len(ai_content)} characters")
            logging.info(f"OpenAI response preview: {ai_content[:200]}...")

        except Exception as e:
            # Fallback response if OpenAI fails
            logging.error(f"OpenAI API error: {e}")
            ai_content = f"I'm sorry, I'm experiencing some technical difficulties right now. Please try again in a moment. Error: {str(e)[:100]}"

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


@router.get("/debug")
async def debug_openai():
    """Debug endpoint for testing OpenAI integration."""
    try:
        from app.core.config import settings
        from app.services.openai_chat import openai_chat_service

        # Test basic configuration
        api_key_preview = (
            settings.OPENAI_API_KEY[:20] + "..."
            if settings.OPENAI_API_KEY
            else "NOT SET"
        )

        # Test OpenAI API call
        response = openai_chat_service.chat_completion(
            [
                {
                    "role": "user",
                    "content": "Respond with just 'OK' if you can read this.",
                }
            ],
            max_tokens=10,
        )

        return {
            "status": "success",
            "api_key_preview": api_key_preview,
            "openai_response": response,
            "message": "OpenAI integration working correctly",
        }
    except Exception as e:
        import traceback

        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
            "api_key_preview": getattr(settings, "OPENAI_API_KEY", "NOT_ACCESSIBLE")[
                :20
            ]
            + "..."
            if hasattr(locals(), "settings") and settings.OPENAI_API_KEY
            else "NOT SET",
        }


@router.get("/history", response_model=ChatHistoryResponse)
def get_history(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Get conversation history for the current user (last 2 weeks)."""
    cutoff_date = datetime.utcnow() - timedelta(days=HISTORY_DAYS)
    messages: List[ChatMessageDB] = (
        db.query(ChatMessageDB)
        .filter(
            ChatMessageDB.user_id == current_user.id,
            ChatMessageDB.created_at >= cutoff_date,
        )
        .order_by(ChatMessageDB.created_at.asc())
        .all()
    )

    history_schema: List[ChatMessage] = [
        ChatMessage(role=m.role, content=m.content) for m in messages
    ]
    return ChatHistoryResponse(history=history_schema)


@router.delete("/history")
def clear_history(
    current_user: User = Depends(get_current_active_user_by_session),
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
