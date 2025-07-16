from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from datetime import datetime
import uuid

from app.core.database import Base


class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False, default="Training Plan")
    goal = Column(String, nullable=True)  # e.g., "General Fitness", "Race Preparation"
    weekly_hours = Column(Integer, nullable=True)  # target weekly training hours
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    plan_data = Column(JSON, nullable=False, default={})  # structured workout data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)