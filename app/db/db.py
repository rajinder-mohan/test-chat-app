from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, create_engine
from sqlalchemy.dialects.sqlite import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.config import settings
from app.constants import ChatType

Base = declarative_base()

class Chat(Base):
    __tablename__ = "chats"
    
    chat_id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String, index=True, nullable=False)
    chat_type = Column(Enum(ChatType), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    active = Column(Boolean, default=True)
    
    conversations = relationship("Conversation", back_populates="chat")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    chat_id = Column(String, ForeignKey("chats.chat_id"), index=True)
    account_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    deleted = Column(Boolean, default=False)
    parent_chat_id = Column(String, ForeignKey("chats.chat_id"), nullable=True)
    parent_message_id = Column(String, nullable=True)
    
    chat = relationship("Chat", back_populates="conversations", foreign_keys=[chat_id])

# Create engine
engine = create_engine(
    settings.SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine) 