"""Project management API endpoints within an organization."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.core.exceptions import ConflictException, NotFoundException
from app.core.rbac import check_org_permission
from app.dependencies import DbSession, Pagination, get_current_user_dep
from app.models.project import Project
from app.models.queue import Queue
from app.models.user import User
from app.schemas.common import PaginatedResponse, create_pagination_meta
from app.schemas.project import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest

router = APIRouter(tags=["Projects"])


@router.post(
    "/orgs/{org_id}/projects", response_model=ProjectResponse, status_code=201
)
async def create_project(
    org_id: uuid.UUID,
    request: ProjectCreateRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Create a new project within an organization (requires admin+ role)."""
    await check_org_permission(current_user.id, org_id, "manage_projects", db)

    # Check slug uniqueness within org
    existing = await db.execute(
        select(Project).where(Project.org_id == org_id, Project.slug == request.slug)
    )
    if existing.scalar_one_or_none():
        raise ConflictException(
            f"Project with slug '{request.slug}' already exists in this organization"
        )

    project = Project(
        org_id=org_id,
        name=request.name,
        slug=request.slug,
        description=request.description,
    )
    db.add(project)
    await db.flush()

    return ProjectResponse(
        id=project.id,
        org_id=project.org_id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        created_at=project.created_at,
        queue_count=0,
    )


@router.get("/orgs/{org_id}/projects", response_model=PaginatedResponse)
async def list_projects(
    org_id: uuid.UUID,
    db: DbSession,
    pagination: Pagination,
    current_user: User = Depends(get_current_user_dep),
):
    """List projects in an organization."""
    await check_org_permission(current_user.id, org_id, "view", db)

    base_query = select(Project).where(Project.org_id == org_id)

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        base_query.order_by(Project.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    projects = result.scalars().all()

    return PaginatedResponse(
        data=[
            ProjectResponse(
                id=p.id,
                org_id=p.org_id,
                name=p.name,
                slug=p.slug,
                description=p.description,
                created_at=p.created_at,
            )
            for p in projects
        ],
        pagination=create_pagination_meta(pagination.page, pagination.page_size, total),
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Get project details."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundException("Project", str(project_id))

    await check_org_permission(current_user.id, project.org_id, "view", db)

    # Count queues
    count_result = await db.execute(
        select(func.count()).where(Queue.project_id == project_id)
    )
    queue_count = count_result.scalar() or 0

    return ProjectResponse(
        id=project.id,
        org_id=project.org_id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        created_at=project.created_at,
        queue_count=queue_count,
    )


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    request: ProjectUpdateRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Update project details (requires admin+ role)."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundException("Project", str(project_id))

    await check_org_permission(current_user.id, project.org_id, "manage_projects", db)

    if request.name is not None:
        project.name = request.name
    if request.description is not None:
        project.description = request.description

    await db.flush()

    return ProjectResponse(
        id=project.id,
        org_id=project.org_id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        created_at=project.created_at,
    )
