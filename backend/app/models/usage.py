"""Usage tracking for rate limiting free tier users."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String

from app.core.database import Base, get_uuid_column


class UsageLog(Base):
    """Track usage of metered features per user."""

    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        get_uuid_column(), ForeignKey("users.id"), nullable=False, index=True
    )
    feature = Column(String, nullable=False)  # 'route_generation', 'chat_message', 'training_plan'
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_usage_logs_user_feature_timestamp", "user_id", "feature", "timestamp"),
    )
