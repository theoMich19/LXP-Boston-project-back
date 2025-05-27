from fastapi import APIRouter, Depends, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse,
    LogoutResponse, MessageResponse, UserResponse
)
from app.services.auth_service import auth_service
from app.core.dependencies import get_current_active_user
from app.services.auth_service import User

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
        user_data: UserRegister,
        db: Session = Depends(get_db)
):
    """Register a new user and return access token"""
    return await auth_service.register_and_login_user(db, user_data)


@router.post("/login", response_model=TokenResponse)
async def login_user(
        user_credentials: UserLogin,
        db: Session = Depends(get_db)
):
    """Login user with email and password"""
    return auth_service.login_user(db, user_credentials.email, user_credentials.password)


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(
        current_user: User = Depends(get_current_active_user)
):
    """Logout current user"""
    return auth_service.logout_user(current_user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information

    🔒 Requires authentication: Bearer token in Authorization header
    """
    return auth_service.get_user_response(current_user)


@router.get("/debug")
async def debug_auth(
        authorization: Optional[str] = Header(None),
        db: Session = Depends(get_db)
):
    """Debug endpoint to check authorization header"""
    if not authorization:
        return {"error": "No Authorization header found"}

    if not authorization.startswith("Bearer "):
        return {"error": "Authorization header must start with 'Bearer '"}

    token = authorization.replace("Bearer ", "")

    try:
        # Verify token
        payload = auth_service.verify_token(token)
        if not payload:
            return {"error": "Invalid token"}

        # Get user
        user = auth_service.get_user_by_email(db, payload.get("sub"))
        if not user:
            return {"error": "User not found"}

        return {
            "success": True,
            "token_payload": payload,
            "user_id": user.id,
            "user_email": user.email,
            "user_role": user.role
        }
    except Exception as e:
        return {"error": f"Token verification failed: {str(e)}"}


@router.get("/", response_model=MessageResponse)
async def auth_info():
    """Authentication API information"""
    return MessageResponse(
        message="TalentBridge Authentication API - Available endpoints: /register, /login, /logout, /me"
    )