from fastapi import APIRouter
from app.api.v1.endpoints import cvs

# Create main API router
api_router = APIRouter()

# Include CV endpoints
api_router.include_router(
    cvs.router,
    prefix="/cvs",
    tags=["cvs"]
)