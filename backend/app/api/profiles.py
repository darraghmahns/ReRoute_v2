from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse, ProfileCompleteRequest
from app.core.database import get_db
from app.core.security import get_current_active_user_by_session
from app.models.user import User, Profile
from typing import Optional

router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.get("/me", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_active_user_by_session), db: Session = Depends(get_db)):
    """Get current user profile"""
    profile = db.query(Profile).filter(Profile.id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return profile

@router.put("/me", response_model=ProfileResponse)
def update_profile(
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db)
):
    """Update profile"""
    profile = db.query(Profile).filter(Profile.id == current_user.id).first()
    if not profile:
        # Create profile if it doesn't exist
        profile = Profile(id=current_user.id)
        db.add(profile)
    
    # Update profile fields
    for field, value in profile_update.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    return profile

@router.post("/complete", response_model=ProfileResponse)
def complete_profile(
    completion_request: ProfileCompleteRequest,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db)
):
    """Complete profile setup - multi-step wizard"""
    profile = db.query(Profile).filter(Profile.id == current_user.id).first()
    if not profile:
        profile = Profile(id=current_user.id)
        db.add(profile)
    
    # Update profile based on step
    step = completion_request.step
    data = completion_request.data
    
    if step == 1:
        # Personal information
        profile.age = data.get('age')
        profile.gender = data.get('gender')
        profile.weight_lbs = data.get('weight_lbs')
        profile.height_ft = data.get('height_ft')
        profile.height_in = data.get('height_in')
    
    elif step == 2:
        # Goals and experience
        profile.cycling_experience = data.get('cycling_experience')
        profile.fitness_level = data.get('fitness_level')
        profile.primary_goals = data.get('primary_goals')
    
    elif step == 3:
        # Health and fitness assessment
        profile.injury_history = data.get('injury_history')
        profile.medical_conditions = data.get('medical_conditions')
        profile.current_fitness_assessment = data.get('current_fitness_assessment')
    
    elif step == 4:
        # Schedule and availability
        profile.weekly_training_hours = data.get('weekly_training_hours')
        profile.preferred_training_days = data.get('preferred_training_days')
        profile.time_availability = data.get('time_availability')
    
    elif step == 5:
        # Equipment and preferences
        profile.nutrition_preferences = data.get('nutrition_preferences')
        profile.equipment_available = data.get('equipment_available')
        profile.training_preferences = data.get('training_preferences')
        profile.profile_completed = True
    
    db.commit()
    db.refresh(profile)
    return profile

@router.delete("/me")
def delete_profile(current_user: User = Depends(get_current_active_user_by_session), db: Session = Depends(get_db)):
    """Delete profile"""
    profile = db.query(Profile).filter(Profile.id == current_user.id).first()
    if profile:
        db.delete(profile)
        db.commit()
    
    # Also delete the user
    db.delete(current_user)
    db.commit()
    
    return {"message": "Profile and user account deleted successfully"} 