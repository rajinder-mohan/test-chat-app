from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
import json
from jose import jwt, JWTError

from app.config import settings
from app.models.models import Token, User, UserCreate, User as UserSchema
from app.db.db import User as UserModel
from app.db.connection import get_db
from app.utils.security import verify_password, get_password_hash, create_access_token

# In a real app, you'd store this in a database
USERS_DB = {}

class AuthService:
    @staticmethod
    async def authenticate_user(username: str, password: str, db: Session) -> Optional[UserModel]:
        """Authenticate a user using database"""
        user = db.query(UserModel).filter(UserModel.username == username).first()
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    @staticmethod
    async def create_user(user_create: UserCreate) -> User:
        if user_create.username in USERS_DB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        hashed_password = get_password_hash(user_create.password)
        user_dict = {
            "id": f"user_{len(USERS_DB) + 1}",
            "username": user_create.username,
            "email": user_create.email,
            "hashed_password": hashed_password,
            "is_active": True
        }
        
        USERS_DB[user_create.username] = user_dict
        
        return User(
            id=user_dict["id"],
            username=user_dict["username"],
            email=user_dict["email"],
            is_active=user_dict["is_active"]
        )
    
    @staticmethod
    async def get_login_token(username: str, password: str) -> Token:
        user = await AuthService.authenticate_user(username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        )
        
        return Token(access_token=access_token, token_type="bearer")

    @staticmethod
    async def create_access_token_for_user(user: UserModel) -> str:
        """Create access token for authenticated user"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        return access_token 