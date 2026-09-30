from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Dharohar API",
    description="Land Record Digitization System - End-to-end Backend API",
    version="1.0.0",
)

origins = [orig.strip() for orig in settings.CORS_ORIGINS.split(",") if orig.strip()]
if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to Dharohar API",
        "version": "1.0.0",
        "docs_url": "/docs",
    }