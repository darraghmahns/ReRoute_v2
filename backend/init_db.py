#!/usr/bin/env python
"""Initialize database schema for local development."""
import sys
from app.core.database import Base, engine

# Import all models to register them with Base
from app.models.user import User, Profile  # noqa
from app.models.route import Route  # noqa
from app.models.training import TrainingPlan  # noqa
from app.models.chat import ChatMessage  # noqa
from app.models.strava import StravaActivity  # noqa
from app.models.subscription import Subscription  # noqa
from app.models.usage import UsageLog  # noqa

if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized successfully")
    sys.exit(0)
