from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from typing import List, Optional
import uuid

from app.db.db import Chat, Conversation
from app.models.models import ChatCreate, ChatUpdate, ChatContent
from app.constants import ChatType, ErrorMessages

class ChatDAL:
    def __init__(self, db_session: AsyncSession, mongodb_session=None):
        self.db_session = db_session
        self.mongodb_session = mongodb_session
        
    async def create_chat(self, chat: ChatCreate, account_id: str) -> Chat:
        """Create a new chat."""
        db_chat = Chat(
            chat_id=str(uuid.uuid4()),
            account_id=account_id,
            chat_type=chat.chat_type,
            name=chat.name
        )
        
        # Create the main conversation for this chat
        db_conversation = Conversation(
            chat_id=db_chat.chat_id,
            account_id=account_id,
            name=chat.name
        )
        
        self.db_session.add(db_chat)
        self.db_session.add(db_conversation)
        await self.db_session.commit()
        await self.db_session.refresh(db_chat)
        
        # Initialize chat content in MongoDB
        if self.mongodb_session:
            chat_content = ChatContent(chat_id=db_chat.chat_id, qa_pairs=[])
            await self.mongodb_session.chat_content.insert_one(chat_content.dict())
            
        return db_chat
    
    async def get_chat(self, chat_id: str, account_id: str) -> Optional[Chat]:
        """Get a chat by ID."""
        query = select(Chat).where(Chat.chat_id == chat_id, Chat.account_id == account_id)
        result = await self.db_session.execute(query)
        return result.scalars().first()
    
    async def update_chat(self, chat_id: str, chat_update: ChatUpdate, account_id: str) -> Optional[Chat]:
        """Update an existing chat."""
        update_data = chat_update.dict(exclude_unset=True)
        if not update_data:
            return await self.get_chat(chat_id, account_id)
        
        query = update(Chat).where(
            Chat.chat_id == chat_id, 
            Chat.account_id == account_id
        ).values(**update_data)
        
        await self.db_session.execute(query)
        await self.db_session.commit()
        return await self.get_chat(chat_id, account_id)
    
    async def delete_chat(self, chat_id: str, account_id: str) -> bool:
        """Delete a chat."""
        # Mark conversations as deleted rather than removing them
        conv_query = update(Conversation).where(
            Conversation.chat_id == chat_id,
            Conversation.account_id == account_id
        ).values(deleted=True)
        
        await self.db_session.execute(conv_query)
        
        # Update chat to be inactive
        chat_query = update(Chat).where(
            Chat.chat_id == chat_id,
            Chat.account_id == account_id
        ).values(active=False)
        
        result = await self.db_session.execute(chat_query)
        await self.db_session.commit()
        
        return result.rowcount > 0
    
    async def get_all_chats(self, account_id: str) -> List[Chat]:
        """Get all active chats for a user."""
        query = select(Chat).where(
            Chat.account_id == account_id,
            Chat.active == True
        ).order_by(Chat.updated_at.desc())
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def get_chat_content(self, chat_id: str, account_id: str) -> Optional[ChatContent]:
        """Get chat content from MongoDB."""
        if not self.mongodb_session:
            return None
            
        # First check if user has access to this chat
        chat = await self.get_chat(chat_id, account_id)
        if not chat:
            return None
            
        content = await self.mongodb_session.chat_content.find_one({"chat_id": chat_id})
        if content:
            return ChatContent(**content)
        return None 