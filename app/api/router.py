from fastapi import APIRouter
from app.api.endpoints import auth, documents, questions

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(questions.router, prefix="/questions", tags=["Questions"])
