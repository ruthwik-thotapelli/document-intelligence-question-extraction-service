from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.document import Document
from app.models.question import Question
from app.models.user import User
from app.schemas.question import QuestionResponse

router = APIRouter()


@router.get(
    "/{question_id}",
    response_model=QuestionResponse,
    summary="Retrieve a single question by ID",
    description="Returns full details of a single extracted question including options, answer, source pages, and confidence.",
)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found.",
        )

    # Ensure user owns the parent document
    doc = (
        db.query(Document)
        .filter(
            Document.id == question.document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this question.",
        )

    return question
