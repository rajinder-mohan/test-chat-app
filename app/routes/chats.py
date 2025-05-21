from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.models import ChatCreate, ChatResponse, ChatUpdate, User, QAPair
from app.dal.chat_dal import ChatDAL
from app.utils.security import get_current_active_user
from app.db.connection import get_db
from app.config import settings
from app.services.cache_service import CacheService

router = APIRouter(
    prefix=f"{settings.API_V1_STR}/chats",
    tags=["chats"]
)

@router.post("/create-chat", response_model=ChatResponse)
async def create_chat(
    chat: ChatCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new chat."""
    chat_dal = ChatDAL(db)
    db_chat = await chat_dal.create_chat(chat, current_user.id)
    return db_chat

@router.get("/get-chat", response_model=ChatResponse)
@CacheService.cache_response(expire=300)  # Cache for 5 minutes
async def get_chat(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get chat details."""
    chat_dal = ChatDAL(db)
    chat = await chat_dal.get_chat(chat_id, current_user.id)
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    return chat

@router.get("/get-chat-content", response_model=List[QAPair])
async def get_chat_content(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get chat content including messages."""
    chat_dal = ChatDAL(db)
    content = await chat_dal.get_chat_content(chat_id, current_user.id)
    
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat content not found or you don't have permission"
        )
    
    return content

@router.put("/update-chat", response_model=ChatResponse)
async def update_chat(
    chat_id: str,
    chat_update: ChatUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update chat metadata."""
    chat_dal = ChatDAL(db)
    updated_chat = await chat_dal.update_chat(chat_id, chat_update, current_user.id)
    
    if not updated_chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have permission to update it"
        )
    
    return updated_chat

@router.delete("/delete-chat", response_model=dict)
async def delete_chat(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a chat."""
    chat_dal = ChatDAL(db)
    success = await chat_dal.delete_chat(chat_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have permission to delete it"
        )
    
    return {"success": True, "message": "Chat deleted successfully"}

@router.get("/list-chats", response_model=List[ChatResponse])
async def list_chats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all active chats for the current user."""
    chat_dal = ChatDAL(db)
    chats = await chat_dal.get_all_chats(current_user.id)
    return chats 