import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create database URL - use SQLite for development if PostgreSQL is not available
if os.getenv("USE_SQLITE", "false").lower() == "true":
    SQLALCHEMY_DATABASE_URL = "sqlite:///./reroute.db"
else:
    SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
    if "sqlite" in SQLALCHEMY_DATABASE_URL
    else {},
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
