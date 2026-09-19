"""
Document Processing Celery Tasks
==================================
Handles asynchronous document extraction pipeline:
  1. Fetch document record from DB
  2. Update status → processing
  3. Call AI extraction service
  4. Save extracted questions to DB
  5. Update status → completed (or failed)

Idempotent: Re-queuing a completed document will be a no-op.
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.document import Document
from app.models.question import Question
from app.services.extraction import extract_questions
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="app.tasks.document_tasks.process_document",
)
def process_document(self, document_id: int):
    """
    Celery task: extract questions from a document.
    Retries up to 3 times on transient errors (e.g. API rate limits).
    """
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found in DB. Task aborted.")
            return

        # Idempotency check
        if doc.status == "completed":
            logger.info(f"Document {document_id} already completed. Skipping.")
            return

        # Mark as processing
        doc.status = "processing"
        doc.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"[Task] Starting extraction for document {document_id}: {doc.filename}")

        # Run AI extraction
        extracted = extract_questions(doc.file_path)

        if not extracted:
            logger.warning(f"No questions extracted from document {document_id}.")

        # Persist each question
        for item in extracted:
            question = Question(
                document_id=document_id,
                question_number=item.get("question_number"),
                text=item.get("text", ""),
                options=item.get("options"),
                answer=item.get("answer"),
                confidence=item.get("confidence"),
                source_pages=item.get("source_pages"),
            )
            db.add(question)

        # Mark completed
        doc.status = "completed"
        doc.error_message = None
        doc.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"[Task] Document {document_id} completed. {len(extracted)} question(s) saved.")

    except Exception as exc:
        db.rollback()
        logger.error(f"[Task] Extraction failed for document {document_id}: {exc}", exc_info=True)

        # Update document status to failed
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "failed"
                doc.error_message = str(exc)[:512]
                doc.updated_at = datetime.utcnow()
                db.commit()
        except Exception as inner:
            logger.error(f"Failed to update document status: {inner}")

        # Retry on transient errors
        raise self.retry(exc=exc, countdown=30)

    finally:
        db.close()
