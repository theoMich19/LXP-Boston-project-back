from fastapi import APIRouter
from app.api.v1.endpoints import cvs, auth

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