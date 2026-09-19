from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


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
    related_doc_id: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    id: int
    filename: str
    status: str
    error_message: Optional[str] = None
