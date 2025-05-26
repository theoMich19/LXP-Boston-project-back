import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple
import PyPDF2
from docx import Document
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

# Configuration
UPLOAD_DIR = "uploads/cvs"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
SUPPORTED_FORMATS = {".pdf", ".docx"}

# Créer le dossier d'upload
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Modèle CV
Base = declarative_base()


class CV(Base):
    __tablename__ = "cvs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(String(50))
    file_type = Column(String(50))
    parsed_data = Column(JSONB)
    upload_date = Column(DateTime, default=datetime.utcnow)


class CVService:
    """Service for CV management"""

    def __init__(self):
        pass

    def _validate_user_id(self, user_id: str) -> int:
        """Validate and convert user ID to integer"""
        try:
            return int(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

    def _validate_file(self, file: UploadFile) -> str:
        """Validate uploaded file and return extension"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="Missing filename")

        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format. Accepted: {', '.join(SUPPORTED_FORMATS)}"
            )

        return file_extension

    def _generate_unique_filename(self, user_id: int, original_filename: str) -> str:
        """Generate unique filename for storage"""
        file_extension = Path(original_filename).suffix.lower()
        unique_filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
        return os.path.join(UPLOAD_DIR, unique_filename)

    def _save_file(self, file_content: bytes, file_path: str) -> int:
        """Save file content to disk and return file size"""
        file_size = len(file_content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            return file_size
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")

    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {str(e)}")

    def _parse_cv_content(self, file_path: str, file_extension: str) -> Tuple[Dict[str, Any], str]:
        """Parse CV content and return parsed data with status"""
        try:
            # Extract text based on file type
            if file_extension == ".pdf":
                text = self._extract_text_from_pdf(file_path)
            else:  # .docx
                text = self._extract_text_from_docx(file_path)

            # Validate extracted text
            if not text or len(text.strip()) < 10:
                return {
                    "error": "File appears to be empty or unreadable",
                    "raw_text": ""
                }, "failed"

            # Create parsed data structure
            parsed_data = {
                "raw_text": text,
                "extracted_at": datetime.utcnow().isoformat(),
                "text_length": len(text)
            }

            return parsed_data, "success"

        except Exception as e:
            return {
                "error": str(e),
                "raw_text": ""
            }, "failed"

    def _cleanup_file(self, file_path: str) -> None:
        """Remove file from disk if it exists"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass  # Ignore cleanup errors

    def _save_cv_to_database(self, db: Session, user_id: int, file_path: str,
                             original_filename: str, file_size: int, file_extension: str,
                             parsed_data: Dict[str, Any]) -> CV:
        """Save CV record to database"""
        try:
            cv_record = CV(
                user_id=user_id,
                file_path=file_path,
                original_filename=original_filename,
                file_size=str(file_size),
                file_type=file_extension.replace(".", ""),
                parsed_data=parsed_data
            )

            db.add(cv_record)
            db.commit()
            db.refresh(cv_record)

            return cv_record

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def upload_cv(self, db: Session, file: UploadFile, user_id: str) -> Dict[str, Any]:
        """
        Upload and parse a CV file

        Args:
            db: Database session
            file: Uploaded file
            user_id: User ID as string

        Returns:
            Dictionary with upload result
        """
        # Validate inputs
        user_id_int = self._validate_user_id(user_id)
        file_extension = self._validate_file(file)

        # Generate file path
        file_path = self._generate_unique_filename(user_id_int, file.filename)

        try:
            # Read and save file
            file_content = await file.read()
            file_size = self._save_file(file_content, file_path)

            # Parse CV content
            parsed_data, parsing_status = self._parse_cv_content(file_path, file_extension)

            # Save to database
            cv_record = self._save_cv_to_database(
                db, user_id_int, file_path, file.filename,
                file_size, file_extension, parsed_data
            )

            # Return response
            return {
                "id": cv_record.id,
                "user_id": cv_record.user_id,
                "original_filename": cv_record.original_filename,
                "file_size": file_size,
                "file_type": cv_record.file_type,
                "upload_date": cv_record.upload_date,
                "parsing_status": parsing_status,
                "message": "CV uploaded successfully"
            }

        except HTTPException:
            # Cleanup and re-raise HTTP exceptions
            self._cleanup_file(file_path)
            raise
        except Exception as e:
            # Cleanup and raise new HTTP exception for unexpected errors
            self._cleanup_file(file_path)
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# Service instance
cv_service = CVService()