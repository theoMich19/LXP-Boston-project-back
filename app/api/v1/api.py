from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, candidates, companies, job_offers, cvs, match

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(job_offers.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(cvs.router, prefix="/cvs", tags=["cvs"])
api_router.include_router(match.router, prefix="/matches", tags=["matching"]) 