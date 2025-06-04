from fastapi import APIRouter
from app.api.v1.endpoints import cvs, auth, job_offers, match, applications, companies

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

# Include matching endpoints
api_router.include_router(
    applications.router,
    prefix="/applications",
    tags=["applications"]
)

# Include matching endpoints
api_router.include_router(
    companies.router,
    prefix="/companies",
    tags=["companies"]
)