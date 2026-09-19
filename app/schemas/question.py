from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class QuestionResponse(BaseModel):
    id: int
    document_id: int
    question_number: Optional[str] = None
    text: str
    options: Optional[List[Any]] = None
    answer: Optional[str] = None
    confidence: Optional[float] = None
    source_pages: Optional[List[int]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractionWarning(BaseModel):
    question_id: int
    question_number: Optional[str]
    text: str
    confidence: float
    reason: str
