"""Custom exception classes for structured error handling."""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception with structured error detail."""

    def __init__(
        self,
        status_code: int,
        error: str,
        message: str,
        details: list[dict] | None = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "error": error,
                "message": message,
                "details": details or [],
                "status_code": status_code,
            },
        )


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str | None = None):
        msg = f"{resource} not found"
        if identifier:
            msg = f"{resource} '{identifier}' not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error="not_found",
            message=msg,
        )


class ConflictException(AppException):
    """Resource already exists or conflicts."""

    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error="conflict",
            message=message,
        )


class ForbiddenException(AppException):
    """User lacks permission for this action."""

    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error="forbidden",
            message=message,
        )


class BadRequestException(AppException):
    """Invalid request data."""

    def __init__(self, message: str, details: list[dict] | None = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="bad_request",
            message=message,
            details=details,
        )


class UnauthorizedException(AppException):
    """Authentication required or failed."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error="unauthorized",
            message=message,
        )
