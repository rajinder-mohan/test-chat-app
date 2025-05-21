from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.models.models import MessageCreate, QAPair
from app.db.db import Message

class MessageDAL:
    def __init__(self, db: Session):
        self.db = db
    
    async def add_message(self, chat_id: str, message: MessageCreate, user_id: str) -> QAPair:
        # Create message in SQLite
        db_message = Message(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            user_id=user_id,
            question=message.content,
            response="",  # Add response later if needed
            response_id=str(uuid.uuid4()),
            message_type=message.message_type,
            timestamp=datetime.utcnow(),
            branches=[]
        )
        
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        
        # Return in QAPair format
        return QAPair(
            question=db_message.question,
            response=db_message.response,
            response_id=db_message.response_id,
            timestamp=db_message.timestamp,
            branches=db_message.branches
        )
    
    async def get_message(self, chat_id: str, message_id: str) -> Optional[QAPair]:
        """Get a specific message from a chat."""
        message = self.db.query(Message).filter(
            Message.chat_id == chat_id,
            Message.response_id == message_id
        ).first()
        
        if message:
            return QAPair(
                question=message.question,
                response=message.response,
                response_id=message.response_id,
                timestamp=message.timestamp,
                branches=message.branches
            )
        
        return None
    
    async def get_chat_messages(self, chat_id: str) -> List[QAPair]:
        """Get all messages for a chat."""
        messages = self.db.query(Message).filter(
            Message.chat_id == chat_id
        ).order_by(Message.timestamp).all()
        
        return [
            QAPair(
                question=message.question,
                response=message.response,
                response_id=message.response_id,
                timestamp=message.timestamp,
                branches=message.branches
            )
            for message in messages
        ]
    
    async def search_messages(self, chat_id: str, query: str) -> List[QAPair]:
        """Search for messages containing the query within a chat."""
        messages = self.db.query(Message).filter(
            Message.chat_id == chat_id,
            (Message.question.like(f"%{query}%") | Message.response.like(f"%{query}%"))
        ).order_by(Message.timestamp).all()
        
        return [
            QAPair(
                question=message.question,
                response=message.response,
                response_id=message.response_id,
                timestamp=message.timestamp,
                branches=message.branches
            )
            for message in messages
        ] 