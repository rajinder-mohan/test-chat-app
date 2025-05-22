from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from sqlalchemy import select, update

from app.db.db import Chat, Conversation, Message
from app.models.models import ChatCreate, ChatUpdate, QAPair

class ChatDAL:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        
    async def create_chat(self, chat: ChatCreate, account_id: str) -> Chat:
        """Create a new chat."""
        db_chat = Chat(
            id=str(uuid.uuid4()),
            account_id=account_id,
            chat_type=chat.chat_type,
            name=chat.name
        )
        
        # Create the main conversation for this chat
        db_conversation = Conversation(
            id=str(uuid.uuid4()),
            chat_id=db_chat.id,
            account_id=account_id,
            name=chat.name
        )
        
        self.db_session.add(db_chat)
        self.db_session.add(db_conversation)
        self.db_session.commit()
        self.db_session.refresh(db_chat)
        
        return db_chat
    
    async def get_chat(self, chat_id: str, account_id: str) -> Optional[Chat]:
        """Get a chat by ID."""
        chat = self.db_session.query(Chat).filter(
            Chat.id == chat_id, 
            Chat.account_id == account_id
        ).first()
        return chat
    
    async def update_chat(self, chat_id: str, chat_update: ChatUpdate, account_id: str) -> Optional[Chat]:
        """Update an existing chat."""
        update_data = chat_update.dict(exclude_unset=True)
        if not update_data:
            return await self.get_chat(chat_id, account_id)
        
        query = update(Chat).where(
            Chat.id == chat_id, 
            Chat.account_id == account_id
        ).values(**update_data)
        
        self.db_session.execute(query)
        self.db_session.commit()
        return await self.get_chat(chat_id, account_id)
    
    async def delete_chat(self, chat_id: str, account_id: str) -> bool:
        """Delete a chat."""
        # Mark conversations as deleted
        conv_query = update(Conversation).where(
            Conversation.chat_id == chat_id,
            Conversation.account_id == account_id
        ).values(deleted=True)
        
        self.db_session.execute(conv_query)
        
        # Update chat to be inactive
        chat_query = update(Chat).where(
            Chat.id == chat_id,
            Chat.account_id == account_id
        ).values(active=False)
        
        result = self.db_session.execute(chat_query)
        self.db_session.commit()
        
        return result.rowcount > 0
    
    async def get_all_chats(self, account_id: str) -> List[Chat]:
        """Get all chats for a user."""
        query = select(Chat).where(
            Chat.account_id == account_id,
            Chat.active == True
        ).order_by(Chat.updated_at.desc())
        
        result = self.db_session.execute(query)
        return result.scalars().all()
    
    async def get_chat_content(self, chat_id: str, account_id: str) -> Optional[List[QAPair]]:
        """Get chat content from database."""
        # First check if user has access to this chat
        chat = await self.get_chat(chat_id, account_id)
        if not chat:
            return None
            
        # Get all messages for this chat
        messages = self.db_session.query(Message).filter(
            Message.chat_id == chat_id
        ).order_by(Message.timestamp).all()
        
        if not messages:
            return []
            
        # Convert to QAPair format
        qa_pairs = [
            QAPair(
                question=message.question,
                response=message.response,
                response_id=message.response_id,
                timestamp=message.timestamp,
                branches=message.branches
            )
            for message in messages
        ]
        
        return qa_pairs 