from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base schema for user"""
    email: EmailStr
    first_name: str
    last_name: str
    role: str

    @validator('role')
    def validate_role(cls, v):
        valid_roles = {'visitor', 'candidate', 'hr'}
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v


class UserRegister(UserBase):
    """Schema for user registration"""
    password: str
    company_id: Optional[int] = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip()


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response (without password)"""
    id: int
    company_id: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse
    message: str = "Login successful"


class LogoutResponse(BaseModel):
    """Schema for logout response"""
    message: str


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str