from sqlalchemy import create_engine, Column, String, ForeignKey, Text, Boolean, DateTime, JSON, Table
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid
import enum

# Create synchronous engine - note the regular sqlite:// URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Create regular sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Define ChatType enum
class ChatType(enum.Enum):
    DIRECT = "direct"
    GROUP = "group"
    AI = "ai"
    BRANCH = "branch"

# Synchronous table creation
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency for synchronous DB access
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    chats = relationship("Chat", back_populates="owner")

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    chat_type = Column(String, nullable=False)  # Using String instead of Enum for simplicity
    account_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="chats")
    conversations = relationship("Conversation", back_populates="chat")
    messages = relationship("Message", back_populates="chat")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_id = Column(String(36), ForeignKey("chats.id"), nullable=False)
    account_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    parent_chat_id = Column(String(36), nullable=True)
    parent_message_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    chat = relationship("Chat", back_populates="conversations")

# New model for message content
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_id = Column(String(36), ForeignKey("chats.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    question = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    response_id = Column(String(36), default=lambda: str(uuid.uuid4()))
    message_type = Column(String(50), default="text")
    timestamp = Column(DateTime, server_default=func.now())
    branches = Column(JSON, default=list)  # Store branches as JSON array
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")

