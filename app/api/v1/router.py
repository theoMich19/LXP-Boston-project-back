from fastapi import APIRouter
from app.api.v1.endpoints import cvs, auth, job_offers, match, candidates

# Create main API router
api_router = APIRouter()

# Include authentication endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

# Include CV endpoints
api_router.include_router(
    cvs.router,
    prefix="/cvs",
    tags=["cvs"]
)

# Include job offers endpoints
api_router.include_router(
    job_offers.router,
    prefix="/jobs",
    tags=["jobs"]
)

# Include matching endpoints
api_router.include_router(
    match.router,
    prefix="/matches",
    tags=["matching"]
)

# Include candidates endpoints
api_router.include_router(
    candidates.router,
    prefix="/candidates",
    tags=["candidates"]
)