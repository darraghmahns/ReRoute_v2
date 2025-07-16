from sqlalchemy import Column, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from datetime import datetime
import uuid

from app.core.database import Base


class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(JSON, nullable=False, default={"title": "Default Plan"})
    details = Column(JSON, nullable=False, default={})  # arbitrary JSON structure for plan
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)