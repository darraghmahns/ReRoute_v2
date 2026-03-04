"""Service for tracking and enforcing usage limits for free tier users."""

import logging
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import uuid_to_db_format
from app.models.usage import UsageLog
from app.models.user import User

logger = logging.getLogger(__name__)

# Free tier limits
LIMITS = {
    "route_generation": 3,  # 3 routes per month
    "chat_message": 10,  # 10 messages per month
}


def check_and_log_usage(
    db: Session, user: User, feature: str, limit_free: int = None
) -> tuple[bool, str]:
    """
    Check if user has hit their limit for free tier and log usage.

    Returns (allowed, message) tuple.
    If allowed=False, the user has exceeded their limit.
    """
    if not hasattr(user, "subscription") or not user.subscription:
        # No subscription data - allow for now
        logger.warning(f"User {user.id} has no subscription object")
        return (True, "")

    if user.subscription.tier == "pro":
        # Pro users have unlimited access
        log_usage(db, user.id, feature)
        return (True, "")

    # Free tier: check monthly limit
    if limit_free is None:
        limit_free = LIMITS.get(feature, 100)  # Default generous limit if not specified

    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    user_id = uuid_to_db_format(user.id)

    count = (
        db.query(func.count(UsageLog.id))
        .filter(
            UsageLog.user_id == user_id,
            UsageLog.feature == feature,
            UsageLog.timestamp >= month_start,
        )
        .scalar()
    )

    if count >= limit_free:
        msg = f"Free tier limit ({limit_free}/{feature}/month) reached. Upgrade to Pro for unlimited access."
        logger.info(f"User {user.id} hit limit for {feature}: {count}/{limit_free}")
        return (False, msg)

    # Log the usage
    log_usage(db, user.id, feature)
    return (True, "")


def log_usage(db: Session, user_id: str, feature: str) -> None:
    """Log a feature usage event."""
    try:
        user_id_db = uuid_to_db_format(user_id)
        log = UsageLog(user_id=user_id_db, feature=feature)
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log usage for user {user_id}, feature {feature}: {e}")
        db.rollback()
