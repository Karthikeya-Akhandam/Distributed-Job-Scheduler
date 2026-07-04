"""Role-based access control (RBAC) helpers and permission checking."""

import uuid
from functools import wraps
from typing import Callable

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.database import get_db
from app.dependencies import get_current_user_dep
from app.models.organization import OrgMember
from app.models.project import Project
from app.models.user import User

# ── Permission Matrix ────────────────────────────────────────
# Role hierarchy: owner > admin > member > viewer

ROLE_HIERARCHY = {
    "owner": 4,
    "admin": 3,
    "member": 2,
    "viewer": 1,
}

# Minimum role required for each action category
PERMISSION_MAP = {
    "manage_org_settings": "admin",
    "manage_projects": "admin",
    "manage_queues": "member",
    "manage_jobs": "member",
    "manage_members": "admin",
    "view": "viewer",
}


def has_permission(user_role: str, required_action: str) -> bool:
    """Check if a user role has permission for the given action.

    Args:
        user_role: The user's role (owner, admin, member, viewer).
        required_action: The action key from PERMISSION_MAP.

    Returns:
        True if the user has sufficient permissions.
    """
    required_role = PERMISSION_MAP.get(required_action, "owner")
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 99)


async def get_org_member(
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    db: AsyncSession,
) -> OrgMember:
    """Get the OrgMember record for a user in an organization.

    Raises NotFoundException if the user is not a member.
    """
    stmt = select(OrgMember).where(
        OrgMember.user_id == user_id,
        OrgMember.org_id == org_id,
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()
    if not member:
        raise ForbiddenException("You are not a member of this organization")
    return member


async def check_org_permission(
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    action: str,
    db: AsyncSession,
) -> OrgMember:
    """Verify a user has permission for an action within an organization.

    Args:
        user_id: The user's UUID.
        org_id: The organization's UUID.
        action: The action key from PERMISSION_MAP.
        db: Database session.

    Returns:
        The OrgMember record if authorized.

    Raises:
        ForbiddenException if the user lacks permission.
    """
    member = await get_org_member(user_id, org_id, db)
    if not has_permission(member.role, action):
        raise ForbiddenException(
            f"Role '{member.role}' does not have permission for '{action}'"
        )
    return member


async def get_project_with_org_check(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    action: str,
    db: AsyncSession,
) -> Project:
    """Fetch a project and verify the user has permission in its organization.

    Args:
        project_id: The project's UUID.
        user_id: The user's UUID.
        action: The required action permission.
        db: Database session.

    Returns:
        The Project if authorized.

    Raises:
        NotFoundException if the project doesn't exist.
        ForbiddenException if the user lacks permission.
    """
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundException("Project", str(project_id))

    await check_org_permission(user_id, project.org_id, action, db)
    return project
