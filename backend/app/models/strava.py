import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, Column, DateTime, ForeignKey, String

from app.core.database import Base, get_uuid_column, generate_uuid


class StravaActivity(Base):
    __tablename__ = "strava_activities"

    id = Column(BigInteger, primary_key=True)  # Strava activity id
    user_id = Column(
        get_uuid_column(), ForeignKey("users.id"), nullable=False, index=True
    )
    name = Column(String(255))
    summary = Column(JSON, nullable=False, default={})  # summary fields from Strava
    streams = Column(JSON, nullable=True)  # streams data from Strava, if fetched
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
