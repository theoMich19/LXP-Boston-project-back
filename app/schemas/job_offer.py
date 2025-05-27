from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class JobOfferBase(BaseModel):
    """Base schema for job offer"""
    title: str
    description: str

    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Title must be at least 5 characters long')
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        if len(v.strip()) < 20:
            raise ValueError('Description must be at least 20 characters long')
        return v.strip()


class JobOfferCreate(JobOfferBase):
    """Schema for job offer creation"""
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    tags: Optional[List[int]] = []

    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        if v is not None and values.get('salary_min') is not None:
            if v < values['salary_min']:
                raise ValueError('Maximum salary must be greater than minimum salary')
        return v


class JobOfferResponse(JobOfferBase):
    """Schema for job offer response"""
    id: int
    company_id: int
    created_by: int
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobOfferCreateResponse(BaseModel):
    """Schema for job offer creation response"""
    id: int
    title: str
    description: str
    company_id: int
    created_by: int
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    status: str
    tags_added: int
    created_at: datetime
    message: str


class JobOfferList(BaseModel):
    """Schema for job offer list item"""
    id: int
    title: str
    description: str
    company_id: int
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class JobOfferListResponse(BaseModel):
    """Schema for job offers list response"""
    total: int
    job_offers: List[JobOfferList]
    message: str