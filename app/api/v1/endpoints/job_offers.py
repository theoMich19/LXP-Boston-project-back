from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.job_offer import JobOfferCreate, JobOfferCreateResponse, JobOfferListResponse
from app.services.job_offer_service import job_offer_service
from app.core.dependencies import require_hr
from app.services.auth_service import User

router = APIRouter()


@router.get("/", response_model=JobOfferListResponse)
async def get_job_offers(
        db: Session = Depends(get_db)
):
    """
    Get all active job offers

    No authentication required - accessible to everyone.
    Returns all active job offers ordered by creation date (newest first).
    """
    return job_offer_service.get_all_job_offers(db)


@router.post("/", response_model=JobOfferCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_job_offer(
        job_data: JobOfferCreate,
        current_user: User = Depends(require_hr),
        db: Session = Depends(get_db)
):
    return job_offer_service.create_job_offer(db, job_data, current_user)
