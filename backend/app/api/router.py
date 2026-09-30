from fastapi import APIRouter

from app.api.routes import (
    admin,
    auth,
    dashboard,
    documents,
    gis,
    health,
    land_records,
    processing,
    results,
    users,
    verification,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, tags=["Auth"])
api_router.include_router(users.router, tags=["Users"])
api_router.include_router(documents.router, tags=["Documents"])
api_router.include_router(processing.router, tags=["Processing"])
api_router.include_router(results.router, tags=["Results"])
api_router.include_router(verification.router, tags=["Verification"])
api_router.include_router(land_records.router, tags=["Land Records"])
api_router.include_router(gis.router, tags=["GIS"])
api_router.include_router(dashboard.router, tags=["Dashboard"])
api_router.include_router(admin.router, tags=["Admin"])