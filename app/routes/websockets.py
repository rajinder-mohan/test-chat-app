from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
import json
from typing import Dict, List, Any
import asyncio

from app.models.models import MessageCreate, User
from app.dal.message_dal import MessageDAL
from app.utils.security import get_password_hash, verify_password
from app.services.auth_service import AuthService
from app.db.connection import get_db, get_mongodb_db
from app.config import settings

router = APIRouter(tags=["websockets"])

# Store active connections
class ConnectionManager:
    def __init__(self):
        # chat_id -> list of websocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, chat_id: str):
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

@router.websocket("/ws/{chat_id}/{token}")
async def websocket_endpoint(
    websocket: WebSocket, 
    chat_id: str, 
    token: str
):
    # Authenticate the user based on the token
    try:
        # Decode JWT token - simplified for example
        payload = {}
        try:
            from jose import jwt
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username = payload.get("sub")
            if not username:
                await websocket.close(code=1008)
                return
        except Exception as e:
            await websocket.close(code=1008)
            return
            
        # Connect to the chat
        await manager.connect(websocket, chat_id)
        
        try:
            while True:
                # Receive message from WebSocket
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Get necessary sessions
                db = next(get_db())
                mongodb = await get_mongodb_db()
                
                # Create message in database
                message = MessageCreate(
                    chat_id=chat_id,
                    content=message_data.get("content", ""),
                    message_type=message_data.get("message_type", "text")
                )
                
                message_dal = MessageDAL(db, mongodb)
                saved_message = await message_dal.add_message(message, payload.get("user_id"))
                
                # Broadcast to all connected clients
                await manager.broadcast(
                    chat_id, 
                    {
                        "type": "message", 
                        "data": {
                            "question": saved_message.question,
                            "response": saved_message.response,
                            "response_id": saved_message.response_id,
                            "timestamp": saved_message.timestamp.isoformat()
                        }
                    }
                )
                
                # Free resources
                await db.close()
                
        except WebSocketDisconnect:
            manager.disconnect(websocket, chat_id)
            # Notify other clients
            await manager.broadcast(
                chat_id,
                {"type": "notification", "data": {"message": "A user has left the chat"}}
            )
            
    except Exception as e:
        manager.disconnect(websocket, chat_id)
        await websocket.close(code=1011) 