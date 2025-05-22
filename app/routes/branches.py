from app.dal.chat_dal import ChatDAL
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict

from app.models.models import BranchCreate, ChatResponse, User
from app.dal.branch_dal import BranchDAL
from app.utils.security import get_current_active_user
from app.db.connection import get_db
from app.config import settings

router = APIRouter(
    prefix="/api/v1/branches",
    tags=["branches"],
    responses={404: {"description": "Not found"}},
)

@router.post("/create-branch", response_model=ChatResponse)
async def create_branch(
    branch: BranchCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new branch from a specific message."""
    branch_dal = BranchDAL(db)
    new_branch = await branch_dal.create_branch(branch, current_user.id)
    
    if not new_branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to create branch. Parent chat or message not found."
        )
    
    return new_branch

@router.get("/{chat_id}", response_model=List[dict])
async def get_branches(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all branches for a chat."""
    branch_dal = BranchDAL(db)
    branches = await branch_dal.get_branches(chat_id, current_user.id)
    
    # Convert ORM objects to dict for response
    result = []
    for branch in branches:
        # Get the chat for this branch
        chat_dal = ChatDAL(db)
        chat = await chat_dal.get_chat(branch.chat_id, current_user.id)
        
        if chat:
            result.append({
                "chat_id": branch.chat_id,
                "name": chat.name,
                "parent_message_id": branch.parent_message_id,
                "created_at": chat.created_at
            })
    
    return result

@router.get("/tree/{chat_id}")
async def get_branch_tree(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get complete tree of branches for a chat."""
    branch_dal = BranchDAL(db)
    tree = await branch_dal.get_branch_tree(chat_id, current_user.id)
    return tree

@router.put("/set-active-branch", response_model=dict)
async def set_active_branch(
    chat_id: str,
    branch_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Set a specific branch as the active branch for a chat.
    
    In a real application, this might update user preferences or session state.
    For this example, we just validate that the user has access to both chats.
    """
    chat_dal = ChatDAL(db)
    
    # Verify user has access to both the main chat and branch
    main_chat = await chat_dal.get_chat(chat_id, current_user.id)
    branch_chat = await chat_dal.get_chat(branch_id, current_user.id)
    
    if not main_chat or not branch_chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat or branch not found, or you don't have permission"
        )
    
    # In a real application, you would update user preferences or session state here
    
    return {
        "success": True,
        "active_chat_id": chat_id,
        "active_branch_id": branch_id
    } 