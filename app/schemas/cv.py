from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class CVBase(BaseModel):
    """Schéma de base pour un CV"""
    file_name: str
    file_path: str


class CVCreate(CVBase):
    """Schéma pour la création d'un CV"""
    user_id: uuid.UUID


class CVUploadResponse(BaseModel):
    """Schéma de réponse pour l'upload d'un CV"""
    id: uuid.UUID
    user_id: uuid.UUID
    original_filename: str
    file_size: int
    file_type: str
    upload_date: datetime
    parsing_status: str = Field(description="success, partial, failed")
    message: str = Field(description="Message décrivant le résultat du parsing")

    class Config:
        from_attributes = True


class CVDetails(BaseModel):
    """Schéma détaillé d'un CV avec données parsées"""
    id: uuid.UUID
    user_id: uuid.UUID
    file_path: str
    original_filename: str
    file_size: int
    file_type: str
    parsed_data: Optional[Dict[str, Any]] = None
    upload_date: datetime

    class Config:
        from_attributes = True


class CVList(BaseModel):
    """Schéma pour lister les CVs"""
    id: uuid.UUID
    original_filename: str
    file_type: str
    upload_date: datetime
    has_parsed_data: bool = Field(description="Indique si le CV a été parsé avec succès")

    class Config:
        from_attributes = True


class ParsedCVData(BaseModel):
    """Structure des données parsées d'un CV"""
    raw_text: str = Field(description="Texte brut extrait du CV")
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[list[str]] = None
    experience: Optional[list[str]] = None
    education: Optional[list[str]] = None
    languages: Optional[list[str]] = None
    summary: Optional[str] = None

    class Config:
        from_attributes = True


class CVInDBBase(CVBase):
    id: int
    candidate_id: int
    upload_date: datetime

    class Config:
        from_attributes = True


class CV(CVInDBBase):
    pass


class LastCVUpload(BaseModel):
    last_upload_date: Optional[datetime] = None
    file_name: Optional[str] = None
    has_cv: bool = False