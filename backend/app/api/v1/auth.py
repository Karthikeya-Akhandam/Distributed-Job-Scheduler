"""Auth API endpoints — register, login, refresh, and current user."""

from fastapi import APIRouter, Depends

from app.dependencies import DbSession
from app.schemas.auth import LoginRequest, RefreshTokenRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.dependencies import get_current_user_dep

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(request: RegisterRequest, db: DbSession):
    """Register a new user account."""
    service = AuthService(db)
    user = await service.register(request)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: DbSession):
    """Authenticate and receive JWT tokens."""
    service = AuthService(db)
    return await service.login(request)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: DbSession):
    """Refresh an expired access token."""
    service = AuthService(db)
    return await service.refresh_token(request.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user=Depends(get_current_user_dep)):
    """Get the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)
