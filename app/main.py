from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.core.config import settings
from app.api.v1.router import api_router

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for TalentBridge platform",
    debug=settings.DEBUG,
    # Configuration pour l'authentification dans Swagger
    openapi_tags=[
        {
            "name": "authentication",
            "description": "Authentication endpoints for login, register, logout"
        },
        {
            "name": "cvs",
            "description": "CV upload and management (requires authentication)"
        },
        {
            "name": "candidates",
            "description": "Candidate management endpoints (HR only)"
        },
        {
            "name": "jobs",
            "description": "Job offers management"
        },
        {
            "name": "matching",
            "description": "Job matching and statistics"
        }
    ]
)


# Custom OpenAPI schema with security
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],  # Ajouter l'URL du frontend
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to TalentBridge API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "features": ["CV upload and parsing", "User authentication"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }