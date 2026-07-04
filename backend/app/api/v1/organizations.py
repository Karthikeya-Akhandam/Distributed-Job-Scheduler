"""Organization and project management API endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.core.rbac import check_org_permission, get_org_member
from app.database import get_db
from app.dependencies import DbSession, Pagination, get_current_user_dep
from app.models.organization import OrgMember, Organization
from app.models.project import Project
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse, create_pagination_meta
from app.schemas.organization import (
    AddMemberRequest,
    OrgCreateRequest,
    OrgMemberResponse,
    OrgResponse,
    UpdateMemberRoleRequest,
)

router = APIRouter(prefix="/orgs", tags=["Organizations"])


# ── Organizations ────────────────────────────────────────────


@router.post("", response_model=OrgResponse, status_code=201)
async def create_organization(
    request: OrgCreateRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Create a new organization. The creator becomes the owner."""
    # Check slug uniqueness
    existing = await db.execute(
        select(Organization).where(Organization.slug == request.slug)
    )
    if existing.scalar_one_or_none():
        raise ConflictException(f"Organization with slug '{request.slug}' already exists")

    org = Organization(name=request.name, slug=request.slug)
    db.add(org)
    await db.flush()

    # Add creator as owner
    membership = OrgMember(user_id=current_user.id, org_id=org.id, role="owner")
    db.add(membership)
    await db.flush()

    return OrgResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        created_at=org.created_at,
        member_count=1,
    )


@router.get("", response_model=PaginatedResponse)
async def list_organizations(
    db: DbSession,
    pagination: Pagination,
    current_user: User = Depends(get_current_user_dep),
):
    """List organizations the current user is a member of."""
    base_query = (
        select(Organization)
        .join(OrgMember, OrgMember.org_id == Organization.id)
        .where(OrgMember.user_id == current_user.id)
    )

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar() or 0

    # Fetch page
    result = await db.execute(
        base_query.offset(pagination.offset).limit(pagination.page_size)
    )
    orgs = result.scalars().all()

    return PaginatedResponse(
        data=[
            OrgResponse(
                id=org.id, name=org.name, slug=org.slug, created_at=org.created_at
            )
            for org in orgs
        ],
        pagination=create_pagination_meta(pagination.page, pagination.page_size, total),
    )


@router.get("/{org_id}", response_model=OrgResponse)
async def get_organization(
    org_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Get organization details."""
    await get_org_member(current_user.id, org_id, db)

    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundException("Organization", str(org_id))

    # Count members
    count_result = await db.execute(
        select(func.count()).where(OrgMember.org_id == org_id)
    )
    member_count = count_result.scalar() or 0

    return OrgResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        created_at=org.created_at,
        member_count=member_count,
    )


# ── Members ──────────────────────────────────────────────────


@router.post("/{org_id}/members", response_model=OrgMemberResponse, status_code=201)
async def add_member(
    org_id: uuid.UUID,
    request: AddMemberRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Add a member to an organization (requires admin+ role)."""
    await check_org_permission(current_user.id, org_id, "manage_members", db)

    # Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User", request.email)

    # Check for existing membership
    existing = await db.execute(
        select(OrgMember).where(
            OrgMember.user_id == user.id, OrgMember.org_id == org_id
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException("User is already a member of this organization")

    member = OrgMember(user_id=user.id, org_id=org_id, role=request.role)
    db.add(member)
    await db.flush()

    return OrgMemberResponse(
        id=member.id,
        user_id=member.user_id,
        org_id=member.org_id,
        role=member.role,
        joined_at=member.joined_at,
        user_email=user.email,
        user_name=user.name,
    )


@router.get("/{org_id}/members", response_model=list[OrgMemberResponse])
async def list_members(
    org_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """List all members of an organization."""
    await get_org_member(current_user.id, org_id, db)

    result = await db.execute(
        select(OrgMember, User)
        .join(User, User.id == OrgMember.user_id)
        .where(OrgMember.org_id == org_id)
    )
    rows = result.all()

    return [
        OrgMemberResponse(
            id=member.id,
            user_id=member.user_id,
            org_id=member.org_id,
            role=member.role,
            joined_at=member.joined_at,
            user_email=user.email,
            user_name=user.name,
        )
        for member, user in rows
    ]


@router.patch("/{org_id}/members/{user_id}", response_model=OrgMemberResponse)
async def update_member_role(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    request: UpdateMemberRoleRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Update a member's role (requires admin+ role)."""
    await check_org_permission(current_user.id, org_id, "manage_members", db)

    result = await db.execute(
        select(OrgMember).where(
            OrgMember.user_id == user_id, OrgMember.org_id == org_id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundException("Member")

    member.role = request.role
    await db.flush()

    return OrgMemberResponse(
        id=member.id,
        user_id=member.user_id,
        org_id=member.org_id,
        role=member.role,
        joined_at=member.joined_at,
    )
