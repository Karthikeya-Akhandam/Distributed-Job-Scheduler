"""Aggregated v1 API router — registers all v1 route modules."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router

v1_router = APIRouter(prefix="/api/v1")

# Register route modules
v1_router.include_router(auth_router)
