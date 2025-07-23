from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user_by_session
from app.models.training import TrainingPlan
from app.models.user import User
from app.schemas.training import (
    GeneratePlanRequest,
    TrainingPlanCreate,
    TrainingPlanListResponse,
    TrainingPlanResponse,
)
from app.services.training_plan_generator import training_plan_generator

router = APIRouter(prefix="/training", tags=["training"])


@router.post("/plans/generate", response_model=TrainingPlanResponse)
def generate_plan(
    request: GeneratePlanRequest,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Generate a new training plan using AI"""
    try:
        # Get user's Strava data for personalization
        strava_data = _get_user_strava_data(current_user, db)

        # Generate the plan using OpenAI with Strava data
        plan_data = training_plan_generator.generate_plan(
            goal=request.goal,
            weekly_hours=request.weekly_hours,
            fitness_level=request.fitness_level or "intermediate",
            preferences=request.preferences,
            strava_data=strava_data,
        )

        # Create the training plan in the database
        training_plan = TrainingPlan(
            user_id=current_user.id,
            name=f"{request.goal} Training Plan",
            goal=request.goal,
            weekly_hours=request.weekly_hours,
            start_date=datetime.now(),
            plan_data=plan_data,
        )

        db.add(training_plan)
        db.commit()
        db.refresh(training_plan)

        return TrainingPlanResponse(
            id=str(training_plan.id),
            name=training_plan.name,
            goal=training_plan.goal,
            weekly_hours=training_plan.weekly_hours,
            start_date=training_plan.start_date,
            end_date=training_plan.end_date,
            is_active=training_plan.is_active,
            plan_data=training_plan.plan_data,
            created_at=training_plan.created_at,
            updated_at=training_plan.updated_at,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to generate training plan: {str(e)}"
        )


def _get_user_strava_data(user: User, db: Session) -> dict:
    """Get user's Strava data for personalization"""
    try:
        import requests

        from app.models.strava import StravaActivity
        from app.models.user import Profile

        # Get user's profile with Strava connection
        profile = db.query(Profile).filter(Profile.id == user.id).first()

        if not profile or not profile.strava_access_token:
            return {"connected": False, "message": "Strava not connected"}

        # Get recent activities from Strava API
        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {profile.strava_access_token}"}

        response = requests.get(
            activities_url, headers=headers, params={"per_page": 20}
        )

        if response.status_code != 200:
            return {
                "connected": True,
                "activities": [],
                "error": "Failed to fetch activities",
            }

        activities = response.json()

        # Calculate some basic metrics
        total_distance = sum(act.get("distance", 0) for act in activities)
        total_time = sum(act.get("moving_time", 0) for act in activities)
        avg_heartrate = sum(
            act.get("average_heartrate", 0)
            for act in activities
            if act.get("average_heartrate")
        ) / max(1, len([act for act in activities if act.get("average_heartrate")]))

        # Get activity types and their frequencies
        activity_types = {}
        for act in activities:
            act_type = act.get("type", "Unknown")
            activity_types[act_type] = activity_types.get(act_type, 0) + 1

        # Get recent performance trends
        recent_activities = activities[:5]  # Last 5 activities
        recent_avg_speed = sum(
            act.get("average_speed", 0) for act in recent_activities
        ) / max(1, len(recent_activities))

        return {
            "connected": True,
            "activities_count": len(activities),
            "total_distance_m": total_distance,
            "total_time_s": total_time,
            "avg_heartrate": avg_heartrate,
            "activity_types": activity_types,
            "recent_avg_speed_ms": recent_avg_speed,
            "recent_activities": [
                {
                    "name": act.get("name"),
                    "type": act.get("type"),
                    "distance_m": act.get("distance"),
                    "moving_time_s": act.get("moving_time"),
                    "average_speed_ms": act.get("average_speed"),
                    "total_elevation_gain_m": act.get("total_elevation_gain"),
                    "average_heartrate": act.get("average_heartrate"),
                    "start_date": act.get("start_date"),
                }
                for act in recent_activities
            ],
        }

    except Exception as e:
        return {"connected": False, "error": str(e)}


@router.get("/plans", response_model=TrainingPlanListResponse)
def list_plans(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """List all training plans for the current user"""
    plans = (
        db.query(TrainingPlan)
        .filter(TrainingPlan.user_id == current_user.id)
        .order_by(TrainingPlan.created_at.desc())
        .all()
    )

    return TrainingPlanListResponse(
        plans=[
            TrainingPlanResponse(
                id=str(plan.id),
                name=plan.name,
                goal=plan.goal,
                weekly_hours=plan.weekly_hours,
                start_date=plan.start_date,
                end_date=plan.end_date,
                is_active=plan.is_active,
                plan_data=plan.plan_data,
                created_at=plan.created_at,
                updated_at=plan.updated_at,
            )
            for plan in plans
        ]
    )


@router.get("/plans/{plan_id}", response_model=TrainingPlanResponse)
def get_plan(
    plan_id: str,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Get a specific training plan"""
    plan = (
        db.query(TrainingPlan)
        .filter(TrainingPlan.id == plan_id, TrainingPlan.user_id == current_user.id)
        .first()
    )

    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")

    return TrainingPlanResponse(
        id=str(plan.id),
        name=plan.name,
        goal=plan.goal,
        weekly_hours=plan.weekly_hours,
        start_date=plan.start_date,
        end_date=plan.end_date,
        is_active=plan.is_active,
        plan_data=plan.plan_data,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.get("/plans/{plan_id}/week/{week_start_date}")
def get_week_plan(
    plan_id: str,
    week_start_date: str,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Get a specific week from a training plan"""
    plan = (
        db.query(TrainingPlan)
        .filter(TrainingPlan.id == plan_id, TrainingPlan.user_id == current_user.id)
        .first()
    )

    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")

    # Parse the week start date
    try:
        week_date = datetime.strptime(week_start_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

    # Find the week in the plan data
    plan_data = plan.plan_data
    if "weeks" not in plan_data:
        raise HTTPException(status_code=404, detail="No weeks found in training plan")

    # Find the week that starts on or before the requested date
    target_week = None
    for week in plan_data["weeks"]:
        week_start = datetime.strptime(week["week_start_date"], "%Y-%m-%d").date()
        if week_start <= week_date < week_start + timedelta(days=7):
            target_week = week
            break

    if not target_week:
        raise HTTPException(status_code=404, detail="Week not found in training plan")

    return {
        "week_start_date": target_week["week_start_date"],
        "workouts": target_week["workouts"],
    }


@router.put("/plans/{plan_id}/workout/{workout_id}/complete")
def mark_workout_complete(
    plan_id: str,
    workout_id: str,
    completed: bool = True,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Mark a workout as completed or not completed"""
    plan = (
        db.query(TrainingPlan)
        .filter(TrainingPlan.id == plan_id, TrainingPlan.user_id == current_user.id)
        .first()
    )

    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")

    # Update the workout completion status
    plan_data = plan.plan_data
    if "weeks" not in plan_data:
        raise HTTPException(status_code=404, detail="No weeks found in training plan")

    # Find and update the workout
    workout_found = False
    for week in plan_data["weeks"]:
        if "workouts" in week:
            for day, workout in week["workouts"].items():
                if workout.get("id") == workout_id:
                    workout["completed"] = completed
                    workout_found = True
                    break
            if workout_found:
                break

    if not workout_found:
        raise HTTPException(status_code=404, detail="Workout not found")

    # Save the updated plan
    plan.plan_data = plan_data
    plan.updated_at = datetime.utcnow()
    db.commit()

    return {
        "message": f"Workout marked as {'completed' if completed else 'not completed'}"
    }


@router.delete("/plans/{plan_id}")
def delete_plan(
    plan_id: str,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Delete a training plan"""
    plan = (
        db.query(TrainingPlan)
        .filter(TrainingPlan.id == plan_id, TrainingPlan.user_id == current_user.id)
        .first()
    )

    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")

    db.delete(plan)
    db.commit()

    return {"message": "Training plan deleted successfully"}
