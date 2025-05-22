from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.models.models import MessageCreate, QAPair

from app.db.db import Message
from app.services.groq_service import GroqService

class MessageDAL:
    def __init__(self, db_session):
        self.db_session = db_session
        self.groq_service = GroqService()
    
    async def add_message(self, chat_id: str, message, user_id: str) -> Optional[Message]:
        """Add a message to a chat and get AI response."""
        # Extract content from MessageCreate object
        message_content = message.content if hasattr(message, 'content') else str(message)
        message_type = message.message_type.value if hasattr(message, 'message_type') else "text"
        
        # Create user message
        user_message = Message(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            user_id=user_id,
            question=message_content,  # Now using the extracted content
            content=message_content,   # Now using the extracted content
            message_type=message_type,
            role="user",
            sender_id=user_id
        )
        
        self.db_session.add(user_message)
        self.db_session.commit()
        
        # Get recent messages for context
        recent_messages = self.db_session.query(Message).filter(
            Message.chat_id == chat_id
        ).order_by(Message.timestamp.desc()).limit(10).all()
        
        # Format messages for Groq
        chat_history = [{
            "role": msg.role or ("user" if msg.user_id else "assistant"),
            "content": msg.content or msg.question or msg.response or ""
        } for msg in reversed(recent_messages) if msg.content or msg.question or msg.response]
        
        # Generate AI response
        groq_service = GroqService()
        ai_response_text = await groq_service.generate_response(
            message_content,  # Using extracted content
            chat_history
        )
        
        # Create AI message
        ai_message = Message(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            user_id=None,
            response=ai_response_text,
            content=ai_response_text,
            response_id=str(uuid.uuid4()),
            message_type="text",
            role="assistant",
            sender_id="AI"
        )
        
        self.db_session.add(ai_message)
        self.db_session.commit()
        
        return ai_message
    
    async def get_message(self, chat_id: str, message_id: str) -> Optional[QAPair]:
        """Get a specific message from a chat."""
        message = self.db_session.query(Message).filter(
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
        messages = self.db_session.query(Message).filter(
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
        messages = self.db_session.query(Message).filter(
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