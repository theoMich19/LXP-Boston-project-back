from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.company_service import company_service
from app.schemas.compagnies import CompanyResponse, CompanyList

router = APIRouter()


@router.get("/", response_model=CompanyList)
async def get_all_companies(
    db: Session = Depends(get_db)
):
    """
    Get all companies
    """
    return company_service.get_all_companies(db)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company_by_id(
    company_id: int,  # Changé de str à int
    db: Session = Depends(get_db)
):
    """
    Get company by ID
    """
    return company_service.get_company_by_id(db, company_id)