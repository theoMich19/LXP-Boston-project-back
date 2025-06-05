from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.db.model import Company, JobOffer


class CompanyService:
    """Service for company management"""

    def __init__(self):
        pass

    def get_all_companies(self, db: Session) -> Dict[str, Any]:
        """
        Get all companies

        Args:
            db: Database session

        Returns:
            Dictionary with companies list
        """
        try:
            # Get all companies
            companies = db.query(Company).order_by(Company.created_at.desc()).all()

            # Convert to response format
            companies_list = []
            for company in companies:
                companies_list.append({
                    "id": company.id,
                    "name": company.name,
                    "city": company.city,
                    "country": company.country,
                    "email": company.email,
                    "phone": company.phone,
                    "created_at": company.created_at,
                    "updated_at": company.updated_at
                })

            return {
                "total": len(companies_list),
                "data": companies_list,
                "message": f"Found {len(companies_list)} companies"
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve companies: {str(e)}"
            )

    def get_company_by_id(self, db: Session, company_id: int) -> Dict[str, Any]:
        """
        Get company by ID with job offers

        Args:
            db: Database session
            company_id: Company ID (integer)

        Returns:
            Dictionary with company information and job offers
        """
        try:
            # Get company by ID
            company = db.query(Company).filter(Company.id == company_id).first()

            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found"
                )

            # Get all job offers for this company
            job_offers = db.query(JobOffer).filter(
                JobOffer.company_id == company_id
            ).order_by(JobOffer.created_at.desc()).all()

            # Convert job offers to response format
            job_offers_list = []
            for job in job_offers:
                job_offers_list.append({
                    "id": job.id,
                    "title": job.title,
                    "description": job.description,
                    "salary_min": float(job.salary_min) if job.salary_min else None,
                    "salary_max": float(job.salary_max) if job.salary_max else None,
                    "status": job.status,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at,
                    "created_by": job.created_by
                })

            return {
                "id": company.id,
                "name": company.name,
                "city": company.city,
                "country": company.country,
                "email": company.email,
                "phone": company.phone,
                "created_at": company.created_at,
                "updated_at": company.updated_at,
                "job_offers": job_offers_list,
                "message": f"Company retrieved successfully with {len(job_offers_list)} job offers"
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve company: {str(e)}"
            )

    def get_company_job_offers(self, db: Session, company_id: int) -> Dict[str, Any]:
        """
        Get all job offers for a specific company

        Args:
            db: Database session
            company_id: Company ID (integer)

        Returns:
            Dictionary with company job offers
        """
        try:
            # Verify company exists
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found"
                )

            # Get all job offers for this company
            job_offers = db.query(JobOffer).filter(
                JobOffer.company_id == company_id
            ).order_by(JobOffer.created_at.desc()).all()

            # Convert to response format
            job_offers_list = []
            for job in job_offers:
                job_offers_list.append({
                    "id": job.id,
                    "title": job.title,
                    "description": job.description,
                    "salary_min": float(job.salary_min) if job.salary_min else None,
                    "salary_max": float(job.salary_max) if job.salary_max else None,
                    "status": job.status,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at,
                    "created_by": job.created_by
                })

            return {
                "company_id": company_id,
                "company_name": company.name,
                "total": len(job_offers_list),
                "data": job_offers_list,
                "message": f"Found {len(job_offers_list)} job offers for {company.name}"
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve company job offers: {str(e)}"
            )


# Service instance
company_service = CompanyService()