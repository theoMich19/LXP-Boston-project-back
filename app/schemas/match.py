from datetime import datetime

from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal


class MatchedSkill(BaseModel):
    """Schema for a matched skill"""
    skill: str
    weight: float = 1.0


class JobMatch(BaseModel):
    """Schema for a job match result"""
    id: int  # Changé de job_id à id
    title: str
    company_name: str
    company_id: int
    compatibility_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    description: str
    created_at: datetime


class MatchResponse(BaseModel):
    """Schema for matches response"""
    data: List[JobMatch]
    total: int
    user_skills: List[str]
    message: str


class MatchStats(BaseModel):
    """Schema for match statistics"""
    total_jobs_analyzed: int
    matches_found: int
    average_score: float
    top_score: int
    user_cv_id: int
    analysis_date: str