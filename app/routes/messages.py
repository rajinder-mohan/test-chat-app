from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.models import MessageCreate, QAPair, User
from app.dal.message_dal import MessageDAL
from app.dal.chat_dal import ChatDAL
from app.utils.security import get_current_active_user
from app.db.connection import get_db
from app.config import settings

router = APIRouter(
    prefix=f"{settings.API_V1_STR}/messages",
    tags=["messages"]
)

@router.post("/add-message", response_model=QAPair)
async def add_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a message to a chat."""
    # First verify user has access to the chat
    chat_dal = ChatDAL(db)
    chat = await chat_dal.get_chat(message.chat_id, current_user.id)
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have permission to add messages"
        )
    
    message_dal = MessageDAL(db)
    message_result = await message_dal.add_message(message.chat_id, message, current_user.id)
    
    if not message_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add message"
        )
    
    return message_result

@router.get("/get-messages", response_model=List[QAPair])
async def get_messages(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all messages for a chat."""
    # First verify user has access to the chat
    chat_dal = ChatDAL(db)
    chat = await chat_dal.get_chat(chat_id, current_user.id)
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have permission to view messages"
        )
    
    message_dal = MessageDAL(db)
    messages = await message_dal.get_chat_messages(chat_id)
    
    return messages

@router.get("/search", response_model=List[QAPair])
async def search_messages(
    chat_id: str,
    query: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search for messages in a chat."""
    # First verify user has access to the chat
    chat_dal = ChatDAL(db)
    chat = await chat_dal.get_chat(chat_id, current_user.id)
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have permission"
        )
    
    message_dal = MessageDAL(db)
    messages = await message_dal.search_messages(chat_id, query)
    
    return messages 