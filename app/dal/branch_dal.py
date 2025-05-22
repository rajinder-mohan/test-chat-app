import json
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dal.chat_dal import ChatDAL
from app.dal.message_dal import MessageDAL
from app.db.db import Chat, Conversation, Message
from app.models.models import BranchCreate


class BranchDAL:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.chat_dal = ChatDAL(db_session)
        self.message_dal = MessageDAL(db_session)

    async def create_branch(self, branch: BranchCreate, account_id: str) -> Optional[Chat]:
        """Create a new branch from a specific message."""
        # Verify parent chat exists and user has access
        parent_chat = await self.chat_dal.get_chat(branch.parent_chat_id, account_id)
        if not parent_chat:
            return None

        # Verify parent message exists
        parent_message = await self.message_dal.get_message(
            branch.parent_chat_id, branch.parent_message_id
        )
        if not parent_message:
            return None

        # Create a new chat for the branch
        db_chat = Chat(
            id=str(uuid.uuid4()),
            account_id=account_id,
            chat_type="branch",
            name=branch.name,
        )

        # Create conversation record for the branch
        db_conversation = Conversation(
            id=str(uuid.uuid4()),
            chat_id=db_chat.id,
            account_id=account_id,
            name=branch.name,
            parent_chat_id=branch.parent_chat_id,
            parent_message_id=branch.parent_message_id,
        )

        self.db_session.add(db_chat)
        self.db_session.add(db_conversation)

        # Update parent message to add reference to this branch
        parent_msg = self.db_session.query(Message).filter(
            Message.chat_id == branch.parent_chat_id,
            Message.response_id == branch.parent_message_id,
        ).first()

        if parent_msg:
            branches = parent_msg.branches or []
            branches.append(db_chat.id)
            parent_msg.branches = branches

        # Copy messages up to the branching point
        messages = (
            self.db_session.query(Message)
            .filter(Message.chat_id == branch.parent_chat_id)
            .order_by(Message.timestamp)
            .all()
        )

        found_branch_point = False
        for msg in messages:
            if msg.response_id == branch.parent_message_id:
                found_branch_point = True

            if found_branch_point:
                break

            # Copy this message to the new branch
            new_message = Message(
                id=str(uuid.uuid4()),
                chat_id=db_chat.id,
                user_id=msg.user_id,
                question=msg.question,
                response=msg.response,
                response_id=str(uuid.uuid4()),  # Generate new response ID
                message_type=msg.message_type,
                timestamp=msg.timestamp,
                branches=[],
            )
            self.db_session.add(new_message)

        self.db_session.commit()
        self.db_session.refresh(db_chat)

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
            Conversation.deleted == False,
        )

        # Remove await - standard SQLAlchemy session is not async
        result = self.db_session.execute(query)
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
                    sub_branches = await build_branch_tree(branch_chat.id)
                    branches.append(
                        {
                            "chat_id": branch_chat.id,
                            "name": branch_chat.name,
                            "parent_message_id": branch_conv.parent_message_id,
                            "branches": sub_branches,
                        }
                    )

            return branches

        # Verify user has access to the chat
        chat = await self.chat_dal.get_chat(chat_id, account_id)
        if not chat:
            return {"chat_id": chat_id, "branches": []}

        branches = await build_branch_tree(chat_id)
        return {
            "chat_id": chat_id,
            "name": chat.name,
            "branches": branches,
        }
