import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Returns errors in RFC 7807 Problem Details format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "about:blank",
            "title": exc.detail if isinstance(exc.detail, str) else "An error occurred",
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": str(request.url.path),
        },
    )


from fastapi.exceptions import RequestValidationError

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Returns validation errors in RFC 7807 format."""
    return JSONResponse(
        status_code=422,
        content={
            "type": "about:blank",
            "title": "Validation Error",
            "status": 422,
            "detail": exc.errors(),
            "instance": str(request.url.path),
        },
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Fallback handler for unhandled exceptions — logs the real error."""
    logger.exception(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": str(exc),  # Show real error in dev — mask in prod via ENVIRONMENT check
            "instance": str(request.url.path),
        },
    )
