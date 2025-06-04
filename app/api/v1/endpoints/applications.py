from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.services.application_service import application_service
from app.core.dependencies import require_candidate, require_hr
from app.services.auth_service import User
from app.schemas.applications import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationList,
    ApplicationStatusUpdate
)

router = APIRouter()


@router.get("", response_model=List[ApplicationList])
async def get_my_applications(
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les candidatures du candidat connecté
    """
    return await application_service.get_candidate_applications(db, current_user.id)


@router.post("", response_model=ApplicationResponse)
async def apply_to_job(
    application_data: ApplicationCreate,
    current_user: User = Depends(require_candidate),
    db: Session = Depends(get_db)
):
    """
    Postuler à une offre d'emploi
    """
    return await application_service.create_application(db, application_data, current_user.id)


@router.put("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: int,
    status_update: ApplicationStatusUpdate,
    current_user: User = Depends(require_hr),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour le statut d'une candidature (RH uniquement)
    """
    return await application_service.update_application_status(
        db, application_id, status_update.status, current_user
    )


@router.get("/job/{job_offer_id}", response_model=List[ApplicationList])
async def get_job_applications(
    job_offer_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(require_hr),
    db: Session = Depends(get_db)
):
    """
    Récupérer toutes les candidatures pour une offre spécifique (RH uniquement)
    """
    return await application_service.get_job_applications(db, job_offer_id, current_user, status)