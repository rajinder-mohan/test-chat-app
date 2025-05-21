from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import uuid

from app.db.db import Chat, Conversation
from app.models.models import BranchCreate, QAPair, ChatContent
from app.constants import ChatType, ErrorMessages
from app.dal.chat_dal import ChatDAL
from app.dal.message_dal import MessageDAL

class BranchDAL:
    def __init__(self, db_session: AsyncSession, mongodb_session=None):
        self.db_session = db_session
        self.mongodb_session = mongodb_session
        self.chat_dal = ChatDAL(db_session, mongodb_session)
        self.message_dal = MessageDAL(db_session, mongodb_session)
    
    async def create_branch(self, branch: BranchCreate, account_id: str) -> Optional[Chat]:
        """Create a new branch from a specific message."""
        # Verify parent chat exists and user has access
        parent_chat = await self.chat_dal.get_chat(branch.parent_chat_id, account_id)
        if not parent_chat:
            return None
        
        # Verify parent message exists
        parent_message = await self.message_dal.get_message(
            branch.parent_chat_id, 
            branch.parent_message_id
        )
        if not parent_message:
            return None
        
        # Create a new chat for the branch
        db_chat = Chat(
            chat_id=str(uuid.uuid4()),
            account_id=account_id,
            chat_type=ChatType.BRANCH,
            name=branch.name
        )
        
        # Create conversation record for the branch
        db_conversation = Conversation(
            chat_id=db_chat.chat_id,
            account_id=account_id,
            name=branch.name,
            parent_chat_id=branch.parent_chat_id,
            parent_message_id=branch.parent_message_id
        )
        
        self.db_session.add(db_chat)
        self.db_session.add(db_conversation)
        await self.db_session.commit()
        await self.db_session.refresh(db_chat)
        
        # Initialize chat content in MongoDB by copying parent chat content up to the branching point
        if self.mongodb_session:
            # Get parent chat content
            parent_content = await self.mongodb_session.chat_content.find_one({"chat_id": branch.parent_chat_id})
            
            if parent_content and parent_content.get("qa_pairs"):
                # Get messages up to the branching point
                branch_index = -1
                for i, pair in enumerate(parent_content["qa_pairs"]):
                    if pair.get("response_id") == branch.parent_message_id:
                        branch_index = i
                        break
                
                if branch_index >= 0:
                    # Copy messages up to and including the branch point
                    qa_pairs = parent_content["qa_pairs"][:branch_index + 1]
                    
                    # Update the branched message to add reference to this branch
                    await self.mongodb_session.chat_content.update_one(
                        {
                            "chat_id": branch.parent_chat_id,
                            "qa_pairs.response_id": branch.parent_message_id
                        },
                        {
                            "$push": {"qa_pairs.$.branches": db_chat.chat_id}
                        }
                    )
                    
                    # Create new chat content document for the branch
                    branch_content = ChatContent(
                        chat_id=db_chat.chat_id,
                        qa_pairs=[QAPair(**pair) for pair in qa_pairs]
                    )
                    
                    await self.mongodb_session.chat_content.insert_one(branch_content.dict())
            
        return db_chat
    
    async def get_branches(self, chat_id: str, account_id: str) -> List[Conversation]:
        """Get all branches for a chat."""
        # Verify user has access to the chat
        chat = await self.chat_dal.get_chat(chat_id, account_id)
        if not chat:
            return []
        
        # Get all conversations that have this chat as parent
        query = select(Conversation).where(
            Conversation.parent_chat_id == chat_id,
            Conversation.account_id == account_id,
            Conversation.deleted == False
        )
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def get_branch_tree(self, chat_id: str, account_id: str) -> dict:
        """Get complete tree of branches for a chat."""
        async def build_branch_tree(current_chat_id):
            branches = []
            branch_convs = await self.get_branches(current_chat_id, account_id)
            
            for branch_conv in branch_convs:
                branch_chat = await self.chat_dal.get_chat(branch_conv.chat_id, account_id)
                if branch_chat:
                    # Recursively get sub-branches
                    sub_branches = await build_branch_tree(branch_chat.chat_id)
                    branches.append({
                        "chat_id": branch_chat.chat_id,
                        "name": branch_chat.name,
                        "parent_message_id": branch_conv.parent_message_id,
                        "branches": sub_branches
                    })
            
            return branches
        
        # Verify user has access to the chat
        chat = await self.chat_dal.get_chat(chat_id, account_id)
        if not chat:
            return {"chat_id": chat_id, "branches": []}
        
        branches = await build_branch_tree(chat_id)
        return {
            "chat_id": chat_id,
            "name": chat.name,
            "branches": branches
        }
