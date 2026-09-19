from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import settings
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import generic_exception_handler, http_exception_handler, validation_exception_handler

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
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS — allow all origins for evaluation purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_tables():
    """Auto-create all tables on startup (SQLite local dev + failsafe for Docker)."""
    from app.core.database import engine
    from app.models.base import Base
    import app.models.user  # noqa: F401
    import app.models.document  # noqa: F401
    import app.models.question  # noqa: F401

    Base.metadata.create_all(bind=engine)


# Mount versioned API
app.include_router(api_router, prefix="/api/v1")


from fastapi.responses import HTMLResponse
import os

@app.get("/", response_class=HTMLResponse, tags=["Dashboard"], summary="Document Intelligence Dashboard")
def root():
    """Serves the frontend Vue.js dashboard."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    index_path = os.path.join(static_dir, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/health", tags=["Health"], summary="Liveness probe")
def health():
    return {"status": "healthy"}
