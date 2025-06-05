from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class JobOfferBase(BaseModel):
    """Base schema for a job offer"""
    id: int = Field(description="Unique job offer ID")
    title: str = Field(description="Job title")
    description: Optional[str] = Field(None, description="Job description")
    salary_min: Optional[float] = Field(None, description="Minimum salary")
    salary_max: Optional[float] = Field(None, description="Maximum salary")
    status: str = Field(description="Job offer status")
    created_at: datetime = Field(description="Creation date")
    updated_at: datetime = Field(description="Last update date")
    created_by: Optional[int] = Field(None, description="User ID who created the offer")

    class Config:
        from_attributes = True


class CompanyBase(BaseModel):
    """Base schema for a company"""
    name: str = Field(description="Company name")
    city: Optional[str] = Field(None, description="Company city")
    country: Optional[str] = Field(None, description="Company country")
    email: Optional[str] = Field(None, description="Company email")
    phone: Optional[str] = Field(None, description="Company phone")


class CompanyResponse(CompanyBase):
    """Response schema for a company with job offers"""
    id: int = Field(description="Unique company ID")
    created_at: datetime = Field(description="Creation date")
    updated_at: datetime = Field(description="Last update date")
    job_offers: List[JobOfferBase] = Field(default=[], description="List of job offers")
    message: str = Field(description="Confirmation message")

    class Config:
        from_attributes = True


class CompanyListItem(BaseModel):
    """Schema for a company list item"""
    id: int = Field(description="Unique company ID")
    name: str = Field(description="Company name")
    city: Optional[str] = Field(None, description="Company city")
    country: Optional[str] = Field(None, description="Company country")
    email: Optional[str] = Field(None, description="Company email")
    phone: Optional[str] = Field(None, description="Company phone")
    created_at: datetime = Field(description="Creation date")
    updated_at: datetime = Field(description="Last update date")

    class Config:
        from_attributes = True


class CompanyList(BaseModel):
    """Schema for companies list"""
    total: int = Field(description="Total number of companies")
    data: List[CompanyListItem] = Field(description="List of companies")
    message: str = Field(description="Informational message")

    class Config:
        from_attributes = True