from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

from app.db.model import JobOffer

Base = declarative_base()


class JobOfferService:
    """Service for job offer management"""

    def __init__(self):
        pass

    def _validate_hr_user(self, user) -> None:
        """Validate that user is HR and has a company"""
        if user.role != 'hr':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only HR users can create job offers"
            )

        if not user.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="HR user must be associated with a company to create job offers"
            )

    def _create_job_offer_record(self, db: Session, job_data, user) -> JobOffer:
        """Create job offer record in database"""
        try:
            job_offer = JobOffer(
                title=job_data.title,
                description=job_data.description,
                company_id=user.company_id,
                created_by=user.id,
                salary_min=job_data.salary_min,
                salary_max=job_data.salary_max,
                status="active"
            )

            db.add(job_offer)
            db.commit()
            db.refresh(job_offer)

            return job_offer

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create job offer: {str(e)}"
            )

    def create_job_offer(self, db: Session, job_data, user) -> Dict[str, Any]:
        """
        Create a new job offer

        Args:
            db: Database session
            job_data: Job offer data from request
            user: Current authenticated user (must be HR)

        Returns:
            Dictionary with job offer creation result
        """

        # Validate user permissions
        self._validate_hr_user(user)

        # Create job offer
        job_offer = self._create_job_offer_record(db, job_data, user)

        # Return response
        return {
            "id": job_offer.id,
            "title": job_offer.title,
            "description": job_offer.description,
            "company_id": job_offer.company_id,
            "created_by": job_offer.created_by,
            "salary_min": job_offer.salary_min,
            "salary_max": job_offer.salary_max,
            "status": job_offer.status,
            "created_at": job_offer.created_at,
            "message": f"Job offer '{job_offer.title}' created successfully"
        }

    def get_all_job_offers(self, db: Session) -> Dict[str, Any]:
        """
        Get all active job offers

        Args:
            db: Database session

        Returns:
            Dictionary with job offers list
        """
        try:
            # Récupérer toutes les offres actives
            job_offers = db.query(JobOffer).filter(
                JobOffer.status == "active"
            ).order_by(JobOffer.created_at.desc()).all()

            # Convertir en format de réponse
            job_offers_list = []
            for job in job_offers:
                job_offers_list.append({
                    "id": job.id,
                    "title": job.title,
                    "description": job.description,
                    "company_id": job.company_id,
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "status": job.status,
                    "created_at": job.created_at
                })

            return {
                "total": len(job_offers_list),
                "data": job_offers_list,
                "message": f"Found {len(job_offers_list)} active job offers"
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve job offers: {str(e)}"
            )


# Service instance
job_offer_service = JobOfferService()