from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.models.models import Token, UserCreate, UserResponse, User as UserSchema
from app.services.auth_service import AuthService
from app.utils.security import get_current_active_user, get_password_hash, verify_password, create_access_token
from app.config import settings
from app.db.db import get_db, User as UserModel

router = APIRouter(
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["authentication"]
)

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Get an access token for authentication."""
    token = await AuthService.get_login_token(form_data.username, form_data.password)
    return token

@router.post("/register", response_model=UserResponse)
def register_user(user_create: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user with this username already exists
    existing_user = db.query(UserModel).filter(UserModel.username == user_create.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Check if email is already used
    existing_email = db.query(UserModel).filter(UserModel.email == user_create.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user with hashed password
    hashed_password = get_password_hash(user_create.password)
    db_user = UserModel(
        id=str(uuid.uuid4()),
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed_password,
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(current_user: UserSchema = Depends(get_current_active_user)):
    """Get information about the currently authenticated user."""
    return current_user 