from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkoutType(str, Enum):
    RECOVERY = "recovery"
    ENDURANCE = "endurance"
    THRESHOLD = "threshold"
    VO2MAX = "vo2max"
    CROSS_TRAINING = "cross_training"
    REST = "rest"


class Workout(BaseModel):
    id: str
    title: str
    description: str
    duration_minutes: int
    workout_type: WorkoutType
    ftp_percentage_min: Optional[int] = None
    ftp_percentage_max: Optional[int] = None
    details: Optional[str] = None  # Additional workout details
    completed: bool = False


class TrainingWeek(BaseModel):
    week_start_date: date
    workouts: Dict[str, Workout]  # key is day of week (monday, tuesday, etc.)


class TrainingPlanCreate(BaseModel):
    name: str = Field(..., description="Name of the training plan")
    goal: str = Field(
        ..., description="Training goal (e.g., General Fitness, Race Preparation)"
    )
    weekly_hours: int = Field(..., description="Target weekly training hours")
    start_date: date = Field(..., description="Start date of the training plan")


class TrainingPlanResponse(BaseModel):
    id: str
    name: str
    goal: str
    weekly_hours: int
    start_date: datetime
    end_date: Optional[datetime]
    is_active: bool
    plan_data: Dict[str, Any]  # Contains weeks with workouts
    created_at: datetime
    updated_at: datetime


class TrainingPlanListResponse(BaseModel):
    plans: List[TrainingPlanResponse]


class GeneratePlanRequest(BaseModel):
    goal: str = Field(..., description="Training goal")
    weekly_hours: int = Field(..., description="Target weekly training hours")
    fitness_level: Optional[str] = Field(
        None, description="Fitness level (beginner, intermediate, advanced)"
    )
    preferences: Optional[List[str]] = Field(None, description="Training preferences")
