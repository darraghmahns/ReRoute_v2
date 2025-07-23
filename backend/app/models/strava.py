import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.core.database import Base


class StravaActivity(Base):
    __tablename__ = "strava_activities"

    id = Column(BigInteger, primary_key=True)  # Strava activity id
    user_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name = Column(String(255))
    summary = Column(JSON, nullable=False, default={})  # summary fields from Strava
    streams = Column(JSON, nullable=True)  # streams data from Strava, if fetched
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
