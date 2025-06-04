from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CompanyBase(BaseModel):
    """Base schema for a company"""
    name: str = Field(description="Company name")
    city: Optional[str] = Field(None, description="Company city")
    country: Optional[str] = Field(None, description="Company country")
    email: Optional[str] = Field(None, description="Company email")
    phone: Optional[str] = Field(None, description="Company phone")


class CompanyResponse(CompanyBase):
    """Response schema for a company"""
    id: int = Field(description="Unique company ID")  # Changé de str à int
    created_at: datetime = Field(description="Creation date")
    updated_at: datetime = Field(description="Last update date")
    message: str = Field(description="Confirmation message")

    class Config:
        from_attributes = True


class CompanyListItem(BaseModel):
    """Schema for a company list item"""
    id: int = Field(description="Unique company ID")  # Changé de str à int
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