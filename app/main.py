from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings

from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import http_exception_handler, generic_exception_handler

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "A scalable Document Intelligence & Question Extraction Service. "
        "Upload PDF or image examination documents and receive structured, "
        "machine-readable questions via a secure, authenticated REST API."
    ),
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
)

# Register RFC 7807 Exception Handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount versioned API
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"], summary="Root health check")
def root():
    return {"status": "ok", "service": settings.PROJECT_NAME, "version": "1.0.0"}


@app.get("/health", tags=["Health"], summary="Liveness probe")
def health():
    return {"status": "healthy"}
