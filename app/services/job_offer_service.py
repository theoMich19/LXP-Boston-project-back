from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

from app.db.model import JobOffer, JobOfferTag

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

    def _validate_tags(self, db: Session, tag_ids: List[int]) -> List[int]:
        """Validate that all tag IDs exist"""
        if not tag_ids:
            return []

        # Check if all tags exist
        existing_tags = db.execute(
            "SELECT id FROM tags WHERE id = ANY(%s)",
            (tag_ids,)
        ).fetchall()

        existing_tag_ids = [tag[0] for tag in existing_tags]
        invalid_tags = set(tag_ids) - set(existing_tag_ids)

        if invalid_tags:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tag IDs: {', '.join(map(str, invalid_tags))}"
            )

        return existing_tag_ids

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

    def _add_job_offer_tags(self, db: Session, job_offer_id: int, tag_ids: List[int]) -> int:
        """Add tags to job offer"""
        if not tag_ids:
            return 0

        try:
            for tag_id in tag_ids:
                job_tag = JobOfferTag(
                    job_offer_id=job_offer_id,
                    tag_id=tag_id
                )
                db.add(job_tag)

            db.commit()
            return len(tag_ids)

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add tags to job offer: {str(e)}"
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

        # Validate tags if provided
        validated_tag_ids = self._validate_tags(db, job_data.tags or [])

        # Create job offer
        job_offer = self._create_job_offer_record(db, job_data, user)

        # Add tags
        tags_added = self._add_job_offer_tags(db, job_offer.id, validated_tag_ids)

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
            "tags_added": tags_added,
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
