from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import Base, get_uuid_column, generate_uuid


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid)
    user_id = Column(
        get_uuid_column(), ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    tier = Column(String(50), nullable=False, default="free")
    status = Column(String(50), nullable=False, default="active")
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="subscription")
