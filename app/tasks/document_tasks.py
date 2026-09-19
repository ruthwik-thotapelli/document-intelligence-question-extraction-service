"""
Document Processing Tasks
==========================
Handles the document extraction pipeline:
  1. Fetch document record from DB
  2. Update status → processing
  3. Call AI extraction service
  4. Save extracted questions to DB
  5. Update status → completed (or failed)

Works in two modes:
  - Celery async mode (when Redis is available — production/Docker)
  - Synchronous mode (when Redis is unavailable — local dev fallback)

Idempotent: Re-queuing a completed document is a no-op.
"""

import logging
from datetime import datetime

from app.core.database import SessionLocal
from app.models.document import Document
from app.models.question import Question
from app.services.extraction import extract_questions
from app.worker import celery_app

logger = logging.getLogger(__name__)


def _run_extraction(document_id: int):
    """
    Core extraction logic — used by both Celery task and sync fallback.
    Separated so it can be called directly without Celery infrastructure.
    """
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found in DB. Aborting.")
            return

        # Idempotency guard
        if doc.status == "completed":
            logger.info(f"Document {document_id} already completed. Skipping.")
            return

        # Mark as processing
        doc.status = "processing"
        doc.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Starting extraction for document {document_id}: {doc.filename}")

        # Run AI extraction
        extracted = extract_questions(doc.file_path)

        if not extracted:
            logger.warning(f"No questions extracted from document {document_id}.")

        # Persist each extracted question
        for item in extracted:
            question = Question(
                document_id=document_id,
                question_number=item.get("question_number"),
                text=item.get("text", ""),
                options=item.get("options"),
                answer=item.get("answer"),
                confidence=item.get("confidence"),
                source_pages=item.get("source_pages"),
                question_type=item.get("question_type"),
                has_image=1 if item.get("has_image") else 0,
                review_notes=item.get("review_notes"),
            )
            db.add(question)

        # Mark completed
        doc.status = "completed"
        doc.error_message = None
        doc.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Document {document_id} completed. {len(extracted)} question(s) saved.")

    except Exception as exc:
        db.rollback()
        logger.error(f"Extraction failed for document {document_id}: {exc}", exc_info=True)

        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "failed"
                doc.error_message = str(exc)[:512]
                doc.updated_at = datetime.utcnow()
                db.commit()
        except Exception as inner:
            logger.error(f"Failed to update document status: {inner}")
        raise

    finally:
        db.close()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name="app.tasks.document_tasks.process_document",
)
def process_document(self, document_id: int):
    """Celery task wrapper — retries up to 3 times on transient errors."""
    try:
        _run_extraction(document_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


def run_extraction_sync(document_id: int):
    """
    Synchronous fallback for local development when Redis/Celery is unavailable.
    Called directly from the upload endpoint if Celery dispatch fails.
    """
    logger.info(f"Running synchronous extraction for document {document_id}")
    _run_extraction(document_id)
