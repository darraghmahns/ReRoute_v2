import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base, get_uuid_column, generate_uuid


class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid)
    user_id = Column(
        get_uuid_column(), ForeignKey("users.id"), nullable=False, index=True
    )
    name = Column(String, nullable=False, default="Training Plan")
    goal = Column(String, nullable=True)  # e.g., "General Fitness", "Race Preparation"
    weekly_hours = Column(Integer, nullable=True)  # target weekly training hours
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    plan_data = Column(JSON, nullable=False, default={})  # structured workout data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
