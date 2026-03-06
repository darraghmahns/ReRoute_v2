import os
import uuid

from sqlalchemy import create_engine, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.core.config import settings

# Detect database type
USE_SQLITE = settings.USE_SQLITE and settings.DATABASE_URL
IS_SQLITE = USE_SQLITE or (settings.DATABASE_URL and settings.DATABASE_URL.startswith("sqlite"))

if USE_SQLITE:
    # Use SQLite for local development
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
    # Create engine with SQLite-specific options
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}  # Needed for SQLite
    )
else:
    # Create database URL for PostgreSQL
    # For Cloud SQL unix socket connections, format is different
    if settings.POSTGRES_HOST.startswith("/cloudsql/"):
        # Cloud SQL unix socket connection
        SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@/{settings.POSTGRES_DB}?host={settings.POSTGRES_HOST}"
    else:
        # Standard TCP connection
        SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    
    # Create engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Database compatibility functions
def get_uuid_column():
    """Return appropriate UUID column type based on database."""
    if IS_SQLITE:
        # Use String for SQLite
        return String(36)
    else:
        # Use PostgreSQL UUID for PostgreSQL
        return PostgresUUID(as_uuid=True)

def generate_uuid():
    """Generate UUID appropriate for database type."""
    new_uuid = uuid.uuid4()
    if IS_SQLITE:
        return str(new_uuid)
    else:
        return new_uuid

def uuid_to_db_format(uuid_value):
    """Convert UUID to appropriate format for database operations."""
    if uuid_value is None:
        return None
    if IS_SQLITE:
        return str(uuid_value) if not isinstance(uuid_value, str) else uuid_value
    else:
        return uuid_value if isinstance(uuid_value, uuid.UUID) else uuid.UUID(str(uuid_value))

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
