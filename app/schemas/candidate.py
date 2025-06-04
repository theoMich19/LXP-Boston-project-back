from pydantic import BaseModel, EmailStr
from typing import Optional

class CandidateBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None

class CandidateCreate(CandidateBase):
    pass

class CandidateUpdate(CandidateBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class CandidateInDBBase(CandidateBase):
    id: int
    user_id: int
    is_active: bool

    class Config:
        from_attributes = True

class Candidate(CandidateInDBBase):
    pass

class CandidateInDB(CandidateInDBBase):
    pass 