from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    status: str
    message: str


class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    user_id: int
    related_doc_id: int | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    id: int
    filename: str
    status: str
    error_message: str | None = None
