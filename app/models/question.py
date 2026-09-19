from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    question_number = Column(String, nullable=True)
    text = Column(String, nullable=False)
    options = Column(JSONB, nullable=True) # list of options
    answer = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    source_pages = Column(JSONB, nullable=True) # list of page numbers
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="questions")
