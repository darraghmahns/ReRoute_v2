from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class ProfileBase(BaseModel):
    age: Optional[int] = Field(None, ge=13, le=100)
    gender: Optional[str] = None
    weight_lbs: Optional[float] = Field(None, ge=44, le=660)  # 20kg-300kg -> 44-660 lbs
    height_ft: Optional[int] = Field(None, ge=3, le=8)
    height_in: Optional[int] = Field(None, ge=0, le=11)
    cycling_experience: Optional[str] = None
    fitness_level: Optional[str] = None
    weekly_training_hours: Optional[float] = Field(None, ge=0, le=168)
    primary_goals: Optional[str] = None
    injury_history: Optional[str] = None
    medical_conditions: Optional[str] = None
    nutrition_preferences: Optional[str] = None
    equipment_available: Optional[str] = None
    preferred_training_days: Optional[str] = None
    time_availability: Optional[Dict[str, Any]] = None
    training_preferences: Optional[Dict[str, Any]] = None
    current_fitness_assessment: Optional[str] = None

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    pass

class ProfileResponse(ProfileBase):
    id: uuid.UUID
    profile_completed: bool
    strava_user_id: Optional[str] = None
    strava_token_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProfileCompleteRequest(BaseModel):
    step: int = Field(..., ge=1, le=5)
    data: Dict[str, Any]

class ProfileStep1(BaseModel):
    age: int = Field(..., ge=13, le=100)
    gender: str
    weight_lbs: float = Field(..., ge=44, le=660)
    height_ft: int = Field(..., ge=3, le=8)
    height_in: int = Field(..., ge=0, le=11)

class ProfileStep2(BaseModel):
    cycling_experience: str
    fitness_level: str
    primary_goals: str

class ProfileStep3(BaseModel):
    injury_history: Optional[str] = None
    medical_conditions: Optional[str] = None
    current_fitness_assessment: str

class ProfileStep4(BaseModel):
    weekly_training_hours: float = Field(..., ge=0, le=168)
    preferred_training_days: str
    time_availability: Dict[str, Any]

class ProfileStep5(BaseModel):
    nutrition_preferences: Optional[str] = None
    equipment_available: str
    training_preferences: Dict[str, Any] 