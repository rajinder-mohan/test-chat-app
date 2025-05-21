from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import uuid

from app.models.models import MessageCreate, QAPair, ChatContent
from app.constants import ErrorMessages

class MessageDAL:
    def __init__(self, db_session: AsyncSession, mongodb_session=None):
        self.db_session = db_session
        self.mongodb_session = mongodb_session
    
    async def add_message(self, message: MessageCreate, user_id: str, is_user_message: bool = True) -> Optional[QAPair]:
        """Add a message to a chat."""
        if not self.mongodb_session:
            return None
            
        # Find the chat content document
        chat_content = await self.mongodb_session.chat_content.find_one({"chat_id": message.chat_id})
        
        if not chat_content:
            # Initialize a new chat content document if it doesn't exist
            chat_content = ChatContent(chat_id=message.chat_id, qa_pairs=[]).dict()
            await self.mongodb_session.chat_content.insert_one(chat_content)
        
        # Create a new QA pair or update the existing one
        response_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        if is_user_message:
            # This is a user question
            qa_pair = QAPair(
                question=message.content,
                response="",  # Empty response initially
                response_id=response_id,
                timestamp=timestamp,
                branches=[]
            )
            
            # Add to qa_pairs array
            await self.mongodb_session.chat_content.update_one(
                {"chat_id": message.chat_id},
                {"$push": {"qa_pairs": qa_pair.dict()}}
            )
            
            return qa_pair
        else:
            # This is an AI response to the last question
            # Find the last QA pair and update the response
            await self.mongodb_session.chat_content.update_one(
                {"chat_id": message.chat_id, "qa_pairs.response": ""},
                {"$set": {"qa_pairs.$.response": message.content}}
            )
            
            # Get the updated QA pair
            updated_content = await self.mongodb_session.chat_content.find_one(
                {"chat_id": message.chat_id}
            )
            
            if updated_content and updated_content.get("qa_pairs"):
                qa_pairs = updated_content["qa_pairs"]
                for pair in qa_pairs:
                    if pair.get("response") == message.content:
                        return QAPair(**pair)
            
            return None
    
    async def get_message(self, chat_id: str, message_id: str) -> Optional[QAPair]:
        """Get a specific message from a chat."""
        if not self.mongodb_session:
            return None
            
        chat_content = await self.mongodb_session.chat_content.find_one(
            {"chat_id": chat_id, "qa_pairs.response_id": message_id},
            {"qa_pairs.$": 1}
        )
        
        if chat_content and chat_content.get("qa_pairs") and len(chat_content["qa_pairs"]) > 0:
            return QAPair(**chat_content["qa_pairs"][0])
        
        return None
    
    async def get_chat_messages(self, chat_id: str) -> List[QAPair]:
        """Get all messages for a chat."""
        if not self.mongodb_session:
            return []
            
        chat_content = await self.mongodb_session.chat_content.find_one({"chat_id": chat_id})
        
        if chat_content and chat_content.get("qa_pairs"):
            return [QAPair(**pair) for pair in chat_content["qa_pairs"]]
        
        return []
    
    async def search_messages(self, chat_id: str, query: str) -> List[QAPair]:
        """Search for messages containing the query within a chat."""
        if not self.mongodb_session:
            return []
        
        # Perform text search on MongoDB
        cursor = self.mongodb_session.chat_content.aggregate([
            {"$match": {"chat_id": chat_id}},
            {"$unwind": "$qa_pairs"},
            {"$match": {
                "$or": [
                    {"qa_pairs.question": {"$regex": query, "$options": "i"}},
                    {"qa_pairs.response": {"$regex": query, "$options": "i"}}
                ]
            }},
            {"$project": {"qa_pair": "$qa_pairs", "_id": 0}}
        ])
        
        results = []
        async for doc in cursor:
            if "qa_pair" in doc:
                results.append(QAPair(**doc["qa_pair"]))
        
        return results 