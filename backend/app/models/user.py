from sqlalchemy import Column, String, Boolean, DateTime, Integer, DECIMAL, Text, JSON, ForeignKey, UUID
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(1024), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    profile = relationship("Profile", back_populates="user", uselist=False)

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    age = Column(Integer)
    gender = Column(String(50))
    weight_lbs = Column(DECIMAL(5, 2))
    height_ft = Column(Integer)
    height_in = Column(Integer)
    cycling_experience = Column(String(50))
    fitness_level = Column(String(50))
    weekly_training_hours = Column(DECIMAL(4, 1))
    primary_goals = Column(Text)
    injury_history = Column(Text)
    medical_conditions = Column(Text)
    nutrition_preferences = Column(Text)
    equipment_available = Column(Text)
    preferred_training_days = Column(Text)
    time_availability = Column(JSON)
    training_preferences = Column(JSON)
    current_fitness_assessment = Column(Text)
    profile_completed = Column(Boolean, default=False)
    
    # Strava integration fields
    strava_user_id = Column(String(255))
    strava_access_token = Column(Text)
    strava_refresh_token = Column(Text)
    strava_token_expires_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="profile") 