import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.core.database import Base, get_uuid_column, generate_uuid


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid)
    user_id = Column(get_uuid_column(), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', or 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
