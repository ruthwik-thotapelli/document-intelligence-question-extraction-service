from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Returns errors in RFC 7807 Problem Details format.
    This is highly recommended for production REST APIs.
    """
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


async def generic_exception_handler(request: Request, exc: Exception):
    """Fallback handler for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred processing your request.",
            "instance": str(request.url.path),
        },
    )
