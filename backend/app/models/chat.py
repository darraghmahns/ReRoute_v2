import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.core.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', or 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
