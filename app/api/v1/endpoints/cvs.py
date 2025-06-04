from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.cv_service import cv_service
from app.core.dependencies import require_candidate
from app.services.auth_service import User
from app.schemas.cv import LastCVUpload

router = APIRouter()


@router.post("/")
async def upload_cv(
        cv_file: UploadFile = File(..., description="CV file (PDF or DOCX)"),
        current_user: User = Depends(require_candidate),
        db: Session = Depends(get_db)
):
    return await cv_service.upload_cv(db, cv_file, current_user.id)

@router.get("/last-upload", response_model=LastCVUpload)
async def get_last_cv_upload(
        current_user: User = Depends(require_candidate),
        db: Session = Depends(get_db)
):
    """
    Récupère la date du dernier CV uploadé par le candidat connecté.
    """
    return cv_service.get_last_cv_upload(db, current_user.id)