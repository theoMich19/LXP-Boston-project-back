from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.cv_service import cv_service

router = APIRouter()


@router.post("/")
async def upload_cv(
        cv_file: UploadFile = File(..., description="CV file (PDF or DOCX)"),
        user_id: str = Form(..., description="User UUID"),
        db: Session = Depends(get_db)
):
    """
    Upload and parse a CV file

    - **cv_file**: PDF or DOCX file (max 10MB)
    - **user_id**: UUID of the user uploading the CV
    """
    return await cv_service.upload_cv(db, cv_file, user_id)