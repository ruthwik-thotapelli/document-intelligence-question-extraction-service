from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    question_number = Column(String, nullable=True)
    text = Column(String, nullable=False)
    options = Column(JSON, nullable=True)        # list of strings — works on SQLite & PostgreSQL
    answer = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    source_pages = Column(JSON, nullable=True)  # list of page numbers
    question_type = Column(String, nullable=True)
    has_image = Column(Integer, default=0)       # boolean as int for SQLite compat
    review_notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="questions")
