from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.constants import ChatType, MessageType

# User models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    is_active: bool
    
    class Config:
        orm_mode = True

# Chat models
class ChatBase(BaseModel):
    name: str
    chat_type: ChatType = ChatType.DIRECT

class ChatCreate(ChatBase):
    pass

class ChatUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None

class ChatResponse(ChatBase):
    chat_id: str
    account_id: str
    created_at: datetime
    updated_at: datetime
    active: bool
    
    class Config:
        orm_mode = True

# Conversation models
class ConversationBase(BaseModel):
    name: str
    chat_id: str

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: str
    account_id: str
    deleted: bool
    parent_chat_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    
    class Config:
        orm_mode = True

# Message models
class MessageBase(BaseModel):
    content: str
    message_type: MessageType = MessageType.TEXT

class MessageCreate(MessageBase):
    chat_id: str

class MessageResponse(MessageBase):
    id: str
    chat_id: str
    user_id: str
    timestamp: datetime
    branches: List[str] = []
    
    class Config:
        orm_mode = True

# Branch models
class BranchCreate(BaseModel):
    parent_chat_id: str
    parent_message_id: str
    name: str

class BranchResponse(BaseModel):
    chat_id: str
    name: str
    parent_chat_id: str
    parent_message_id: str
    created_at: datetime
    
    class Config:
        orm_mode = True

# MongoDB chat content model
class QAPair(BaseModel):
    question: str
    response: str
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    branches: List[str] = []

class ChatContent(BaseModel):
    chat_id: str
    qa_pairs: List[QAPair] = [] 