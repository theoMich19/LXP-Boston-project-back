from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.match import MatchResponse, MatchStats
from app.services.matching_service import matching_service
from app.core.dependencies import require_candidate
from app.services.auth_service import User

router = APIRouter()


@router.get("/", response_model=MatchResponse)
async def get_job_matches(
        limit: int = Query(10, ge=1, le=50, description="Number of matches to return (1-50)"),
        current_user: User = Depends(require_candidate),
        db: Session = Depends(get_db)
):
    """
    Get job matches for authenticated candidate user

    - **limit**: Number of matches to return (default: 10, max: 50)

    Returns top job matches based on CV analysis and compatibility scoring.
    Only candidates can access this endpoint.

    The matching algorithm analyzes:
    - Technical skills from your CV
    - Job requirements and descriptions
    - Salary ranges and experience level
    - Company preferences

    Compatibility score is calculated from 0-100% based on:
    - Matched skills (weighted by importance)
    - Experience level alignment
    - Technology stack overlap
    """
    return matching_service.get_job_matches(db, current_user.id, limit)


@router.get("/stats", response_model=MatchStats)
async def get_match_statistics(
        current_user: User = Depends(require_candidate),
        db: Session = Depends(get_db)
):
    """
    Get matching statistics for the authenticated candidate

    Returns detailed statistics about job matching performance:
    - Total jobs analyzed
    - Number of matches found
    - Average compatibility score
    - Best match score
    - Analysis metadata
    """
    return matching_service.get_match_stats(db, current_user.id)
