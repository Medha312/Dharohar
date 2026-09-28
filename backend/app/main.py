from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(
    title="Dharohar API",
    description="Land Record Digitization System",
    version="0.1.0",
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to Dharohar API",
        "version": "0.1.0",
    }