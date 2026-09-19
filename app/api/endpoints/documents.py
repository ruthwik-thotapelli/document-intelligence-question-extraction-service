import logging

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.document import Document
from app.models.question import Question
from app.models.user import User
from app.schemas.document import DocumentResponse, DocumentStatusResponse, DocumentUploadResponse
from app.schemas.question import ExtractionWarning, QuestionResponse
from app.services.storage import save_upload, validate_file
from app.tasks.document_tasks import process_document

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/jpg", "image/png"}
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=202,
    summary="Upload a PDF or image for question extraction",
    description=(
        "Upload a PDF or image file (JPG, PNG). Processing happens asynchronously. "
        "Use the returned document ID to poll /status. "
        "Optionally pass `related_doc_id` to link this document (e.g. an answer key) "
        "to a previously uploaded question paper."
    ),
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    related_doc_id: int | None = Query(
        None, description="ID of a related document (e.g., answer key)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: PDF, JPG, PNG.",
        )

    # Read file and check size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB} MB.",
        )
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # Validate magic bytes (prevent malicious uploads)
    try:
        validate_file(file_bytes, file.content_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # If related doc provided, make sure it belongs to the user
    if related_doc_id:
        related = (
            db.query(Document)
            .filter(
                Document.id == related_doc_id,
                Document.user_id == current_user.id,
            )
            .first()
        )
        if not related:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Related document {related_doc_id} not found or not owned by you.",
            )

    # Save file to disk
    file_path = save_upload(file_bytes, file.filename, current_user.id)

    # Create DB record
    doc = Document(
        filename=file.filename,
        file_path=file_path,
        status="pending",
        user_id=current_user.id,
        related_doc_id=related_doc_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Dispatch Celery task (falls back to FastAPI BackgroundTasks if Redis unavailable)
    try:
        process_document.delay(doc.id)
        logger.info(f"Document {doc.id} queued via Celery by user {current_user.id}.")
    except Exception as celery_err:
        logger.warning(
            f"Celery unavailable ({celery_err}), queuing via FastAPI BackgroundTasks for doc {doc.id}."
        )
        from app.tasks.document_tasks import run_extraction_sync
        background_tasks.add_task(run_extraction_sync, doc.id)

    return DocumentUploadResponse(
        id=doc.id,
        filename=doc.filename,
        status=doc.status,
        message="Document accepted. Processing has started asynchronously.",
    )


@router.get(
    "/{doc_id}/status",
    response_model=DocumentStatusResponse,
    summary="Check document processing status",
    description="Returns the current processing status: pending, processing, completed, or failed.",
)
def get_document_status(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = _get_doc_for_user(doc_id, current_user.id, db)
    return DocumentStatusResponse(
        id=doc.id,
        filename=doc.filename,
        status=doc.status,
        error_message=doc.error_message,
    )


@router.get(
    "/{doc_id}",
    response_model=DocumentResponse,
    summary="Retrieve document details",
)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_doc_for_user(doc_id, current_user.id, db)


@router.get(
    "/{doc_id}/questions",
    response_model=list[QuestionResponse],
    summary="Retrieve all extracted questions for a document",
)
def get_questions(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = _get_doc_for_user(doc_id, current_user.id, db)
    if doc.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Document is not yet processed. Current status: {doc.status}",
        )
    return db.query(Question).filter(Question.document_id == doc_id).all()


@router.get(
    "/{doc_id}/answers",
    response_model=list[dict],
    summary="Retrieve answer-key information for all questions in a document",
    description=(
        "Returns a list of question IDs with their associated answers. "
        "If a related answer-key document was linked, answers from that document are also included."
    ),
)
def get_answers(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = _get_doc_for_user(doc_id, current_user.id, db)
    if doc.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Document is not yet processed. Current status: {doc.status}",
        )

    questions = db.query(Question).filter(Question.document_id == doc_id).all()

    # Also include questions from related docs (e.g. separate answer-key document)
    if doc.related_doc_id:
        related_doc = (
            db.query(Document)
            .filter(
                Document.id == doc.related_doc_id,
                Document.user_id == current_user.id,
            )
            .first()
        )
        if related_doc and related_doc.status == "completed":
            related_questions = (
                db.query(Question).filter(Question.document_id == related_doc.id).all()
            )
            questions = list(questions) + list(related_questions)

    return [
        {
            "question_id": q.id,
            "question_number": q.question_number,
            "answer": q.answer,
            "answer_confidence": q.confidence,
            "answer_status": _answer_status(q.answer, q.confidence),
        }
        for q in questions
    ]


@router.get(
    "/{doc_id}/warnings",
    response_model=list[ExtractionWarning],
    summary="Retrieve questions flagged for human review",
    description=(
        "Returns questions with low confidence scores or missing key information "
        "that require manual verification."
    ),
)
def get_warnings(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = _get_doc_for_user(doc_id, current_user.id, db)
    if doc.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Document is not yet processed. Current status: {doc.status}",
        )

    questions = db.query(Question).filter(Question.document_id == doc_id).all()
    warnings = []
    for q in questions:
        reasons = []
        if q.confidence is not None and q.confidence < 0.7:
            reasons.append(f"Low extraction confidence ({q.confidence:.0%})")
        if not q.question_number:
            reasons.append("Question number could not be identified")
        if q.answer is None:
            reasons.append("No answer found in document")

        if reasons:
            warnings.append(
                ExtractionWarning(
                    question_id=q.id,
                    question_number=q.question_number,
                    text=q.text,
                    confidence=q.confidence or 0.0,
                    reason="; ".join(reasons),
                )
            )
    return warnings


@router.get(
    "/",
    response_model=list[DocumentResponse],
    summary="List all documents uploaded by the current user",
)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )


# ─── Helpers ────────────────────────────────────────────────────────────────


def _get_doc_for_user(doc_id: int, user_id: int, db: Session) -> Document:
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found.",
        )
    return doc


def _answer_status(answer: str | None, confidence: float | None) -> str:
    if answer is None:
        return "not_found"
    if confidence is not None and confidence < 0.6:
        return "uncertain"
    return "found"
