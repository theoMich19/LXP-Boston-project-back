from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.cv_service import cv_service
from app.core.dependencies import require_candidate
from app.services.auth_service import User

router = APIRouter()


@router.post("/")
async def upload_cv(
        cv_file: UploadFile = File(..., description="CV file (PDF or DOCX)"),
        current_user: User = Depends(require_candidate),
        db: Session = Depends(get_db)
):
    return await cv_service.upload_cv(db, cv_file, current_user.id)