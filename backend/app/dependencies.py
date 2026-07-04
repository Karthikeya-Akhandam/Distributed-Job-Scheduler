"""Shared FastAPI dependencies for injection into route handlers."""

from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


class PaginationParams:
    """Common pagination parameters for list endpoints."""

    def __init__(
        self,
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        page_size: Annotated[
            int, Query(ge=1, le=100, alias="pageSize", description="Items per page")
        ] = 20,
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size


Pagination = Annotated[PaginationParams, Depends()]
