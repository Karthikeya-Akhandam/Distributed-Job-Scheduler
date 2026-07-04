"""Authentication service — user registration, login, and token management."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.organization import OrgMember
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    """Handles user authentication: registration, login, token refresh."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, request: RegisterRequest) -> User:
        """Register a new user account.

        Raises ConflictException if the email is already taken.
        """
        # Check for existing user
        stmt = select(User).where(User.email == request.email)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            raise ConflictException(f"User with email '{request.email}' already exists")

        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            name=request.name,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate a user and return JWT tokens.

        Raises UnauthorizedException if credentials are invalid.
        """
        stmt = select(User).where(User.email == request.email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(request.password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        return self._create_tokens(user)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh an access token using a valid refresh token.

        Raises UnauthorizedException if the refresh token is invalid or expired.
        """
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid or expired refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid refresh token payload")

        stmt = select(User).where(User.id == uuid.UUID(user_id))
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedException("User not found or deactivated")

        return self._create_tokens(user)

    async def get_current_user(self, token: str) -> User:
        """Extract and return the authenticated user from a JWT access token.

        Raises UnauthorizedException if the token is invalid.
        """
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            raise UnauthorizedException("Invalid or expired access token")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")

        stmt = select(User).where(User.id == uuid.UUID(user_id))
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedException("User not found or deactivated")

        return user

    async def get_user_org_role(self, user_id: uuid.UUID, org_id: uuid.UUID) -> str | None:
        """Get the user's role within a specific organization.

        Returns None if the user is not a member.
        """
        stmt = select(OrgMember.role).where(
            OrgMember.user_id == user_id,
            OrgMember.org_id == org_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _create_tokens(user: User) -> TokenResponse:
        """Generate access and refresh tokens for a user."""
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )
