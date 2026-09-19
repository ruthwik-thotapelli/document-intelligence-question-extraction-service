from datetime import datetime
from typing import Any

from pydantic import BaseModel


class QuestionResponse(BaseModel):
    id: int
    document_id: int
    question_number: str | None = None
    text: str
    options: list[Any] | None = None
    answer: str | None = None
    confidence: float | None = None
    source_pages: list[int] | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractionWarning(BaseModel):
    question_id: int
    question_number: str | None
    text: str
    confidence: float
    reason: str
