from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status, Query
import json
from typing import Dict, List, Any
import asyncio
import uuid
from sqlalchemy.orm import Session
import logging
from jose import jwt

from app.models.models import MessageCreate, User
from app.db.db import Chat
from app.dal.message_dal import MessageDAL
from app.utils.security import get_password_hash, verify_password
from app.services.auth_service import AuthService
from app.db.connection import get_db
from app.config import settings
from app.services.groq_service import GroqService

router = APIRouter(tags=["websockets"])

# Store active connections
class ConnectionManager:
    def __init__(self):
        # chat_id -> list of websocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, chat_id: str, user_id: str):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, chat_id: str):
        if chat_id in self.active_connections:
            if websocket in self.active_connections[chat_id]:
                self.active_connections[chat_id].remove(websocket)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]
    
    async def broadcast(self, chat_id: str, message: dict):
        if chat_id in self.active_connections:
            for connection in self.active_connections[chat_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: str,
    db: Session = Depends(get_db)
):
    try:
        # Get token from query parameters
        query_params = dict(websocket.query_params)
        token = query_params.get("token")
        
        if not token:
            logging.error(f"No token provided for chat {chat_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Add some debugging
        logging.info(f"Processing WebSocket connection for chat {chat_id} with token: {token[:10]}...")
        
        # Verify the token
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            username = payload.get("sub")
            if username is None:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        except jwt.JWTError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Get the user
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Check chat access
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        if chat.account_id != user.id:
            # Check if this is a public chat or the user has access
            # Add your access control logic here
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Accept the connection if all checks pass
        await websocket.accept()
        
        # Register connection with connection manager
        await manager.connect(websocket, chat_id, user.id)
        
        # Handle messages
        groq_service = GroqService()
        
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Create user message with both old and new fields
            user_message = Message(
                id=str(uuid.uuid4()),
                chat_id=chat_id,
                user_id=user.id,
                question=message_data.get("content", ""),  # Old field
                content=message_data.get("content", ""),   # New field
                message_type="text",
                role="user",                              # New field
                sender_id=user.id                         # New field
            )
            
            db.add(user_message)
            db.commit()
            
            # Send user message to all connected clients
            await manager.broadcast(chat_id, {
                "type": "message",
                "data": {
                    "id": user_message.id,
                    "content": user_message.content or user_message.question,
                    "sender_id": user_message.sender_id or user_message.user_id,
                    "role": user_message.role or "user",
                    "timestamp": user_message.timestamp.isoformat() if user_message.timestamp else None,
                    "message_type": user_message.message_type
                }
            })
            
            # Get AI response
            ai_response = await groq_service.generate_response(
                message_data.get("content", "")
            )
            
            # Create AI message with both old and new fields
            ai_message = Message(
                id=str(uuid.uuid4()),
                chat_id=chat_id,
                user_id=None,                  # Old field
                response=ai_response,          # Old field
                content=ai_response,           # New field
                response_id=str(uuid.uuid4()),
                message_type="text",
                role="assistant",              # New field
                sender_id="AI"                 # New field
            )
            
            db.add(ai_message)
            db.commit()
            
            # Send AI message to all connected clients
            await manager.broadcast(chat_id, {
                "type": "message",
                "data": {
                    "id": ai_message.id,
                    "content": ai_message.content or ai_message.response,
                    "sender_id": ai_message.sender_id,
                    "role": ai_message.role or "assistant",
                    "timestamp": ai_message.timestamp.isoformat() if ai_message.timestamp else None,
                    "message_type": ai_message.message_type
                }
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
        await websocket.close() 