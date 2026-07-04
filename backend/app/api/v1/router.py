"""Aggregated v1 API router — registers all v1 route modules."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.organizations import router as orgs_router
from app.api.v1.projects import router as projects_router
from app.api.v1.queues import router as queues_router
from app.api.v1.workers import router as workers_router

v1_router = APIRouter(prefix="/api/v1")

# Register route modules
v1_router.include_router(auth_router)
v1_router.include_router(orgs_router)
v1_router.include_router(projects_router)
v1_router.include_router(queues_router)
v1_router.include_router(jobs_router)
v1_router.include_router(workers_router)
