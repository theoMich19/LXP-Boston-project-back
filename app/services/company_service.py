from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.db.model import Company


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
                    "id": company.id,  # Retourner l'ID comme entier
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
        Get company by ID

        Args:
            db: Database session
            company_id: Company ID (integer)

        Returns:
            Dictionary with company information
        """
        try:
            # Get company by ID
            company = db.query(Company).filter(Company.id == company_id).first()

            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found"
                )

            return {
                "id": company.id,  # Retourner l'ID comme entier
                "name": company.name,
                "city": company.city,
                "country": company.country,
                "email": company.email,
                "phone": company.phone,
                "created_at": company.created_at,
                "updated_at": company.updated_at,
                "message": "Company retrieved successfully"
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve company: {str(e)}"
            )


# Service instance
company_service = CompanyService()