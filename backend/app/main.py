"""FastAPI application factory with middleware, CORS, and lifecycle events."""

from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import v1_router
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown events."""
    # ── Startup ──────────────────────────────────────────────
    app.state.redis = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    yield
    # ── Shutdown ─────────────────────────────────────────────
    await app.state.redis.close()


app = FastAPI(
    title=settings.app_name,
    description=(
        "A production-inspired distributed job scheduling platform capable of "
        "reliably executing asynchronous background jobs across multiple workers."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS Middleware ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes ───────────────────────────────────────────────
app.include_router(v1_router)


# ── Health Check ─────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}
