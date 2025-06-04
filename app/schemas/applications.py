from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ApplicationStatus(str, Enum):
    """Énumération des statuts de candidature"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    REJECTED = "rejected"
    ACCEPTED = "accepted"


class ApplicationBase(BaseModel):
    """Schéma de base pour une candidature"""
    pass


class ApplicationCreate(BaseModel):
    """Schéma pour créer une candidature"""
    job_offer_id: int = Field(description="ID de l'offre d'emploi")

    class Config:
        from_attributes = True


class ApplicationStatusUpdate(BaseModel):
    """Schéma pour mettre à jour le statut d'une candidature"""
    status: ApplicationStatus = Field(description="Nouveau statut de la candidature")

    class Config:
        from_attributes = True


class ApplicationResponse(BaseModel):
    """Schéma de réponse pour une candidature"""
    id: int
    user_id: int
    job_offer_id: int
    status: ApplicationStatus
    applied_at: datetime
    message: str = Field(description="Message de confirmation")

    class Config:
        from_attributes = True


class ApplicationList(BaseModel):
    """Schéma pour lister les candidatures avec informations de l'offre"""
    id: int
    user_id: int
    job_offer_id: int
    status: ApplicationStatus
    applied_at: datetime

    # Informations de l'offre d'emploi
    job_title: str = Field(description="Titre de l'offre d'emploi")
    company_name: str = Field(description="Nom de l'entreprise")
    job_salary_min: Optional[float] = None
    job_salary_max: Optional[float] = None

    # Informations du candidat (pour les RH)
    candidate_first_name: Optional[str] = None
    candidate_last_name: Optional[str] = None
    candidate_email: Optional[str] = None

    class Config:
        from_attributes = True


class ApplicationWithCandidate(BaseModel):
    """Schéma détaillé d'une candidature avec informations du candidat (pour RH)"""
    id: int
    user_id: int
    job_offer_id: int
    status: ApplicationStatus
    applied_at: datetime

    # Informations du candidat
    candidate_first_name: str
    candidate_last_name: str
    candidate_email: str

    # Informations du CV si disponible
    cv_id: Optional[int] = None
    cv_filename: Optional[str] = None

    class Config:
        from_attributes = True


class ApplicationStats(BaseModel):
    """Schéma pour les statistiques de candidatures"""
    total_applications: int
    pending_applications: int
    reviewed_applications: int
    accepted_applications: int
    rejected_applications: int
    applications_this_week: int
    applications_this_month: int

    class Config:
        from_attributes = True