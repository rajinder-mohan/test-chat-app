from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models.models import Token, User, UserCreate
from app.services.auth_service import AuthService
from app.utils.security import get_current_active_user
from app.config import settings

router = APIRouter(
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["authentication"]
)

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Get an access token for authentication."""
    token = await AuthService.get_login_token(form_data.username, form_data.password)
    return token

@router.post("/register", response_model=User)
async def register_user(user: UserCreate):
    """Register a new user."""
    new_user = await AuthService.create_user(user)
    return new_user

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get information about the currently authenticated user."""
    return current_user 