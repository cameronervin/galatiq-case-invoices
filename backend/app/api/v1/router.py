from fastapi import APIRouter

from backend.app.api.v1 import health, runs

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(runs.router, tags=["runs"])
