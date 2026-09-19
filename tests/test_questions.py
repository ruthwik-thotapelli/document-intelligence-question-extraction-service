"""Tests for question retrieval endpoints."""
import io
import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.question import Question
from app.core.database import SessionLocal


VALID_PDF = b"%PDF-1.4 fake content"


def _create_completed_doc_with_questions(client, auth_headers, db: Session, user_id: int):
    """Helper: upload a doc, mark it completed, and insert test questions."""
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("q_test.pdf", io.BytesIO(VALID_PDF), "application/pdf")},
        headers=auth_headers,
    )
    doc_id = upload_resp.json()["id"]

    # Manually mark as completed in DB
    doc = db.query(Document).filter(Document.id == doc_id).first()
    doc.status = "completed"
    db.commit()

    # Insert questions
    q1 = Question(
        document_id=doc_id,
        question_number="1",
        text="What is 2 + 2?",
        options=["A. 3", "B. 4", "C. 5"],
        answer="B",
        confidence=0.97,
        source_pages=[1],
    )
    q2 = Question(
        document_id=doc_id,
        question_number="2",
        text="Describe photosynthesis.",
        options=None,
        answer=None,
        confidence=0.45,
        source_pages=[1, 2],
    )
    db.add_all([q1, q2])
    db.commit()
    db.refresh(q1)
    db.refresh(q2)

    return doc_id, q1.id, q2.id


def test_get_questions_for_completed_doc(client, auth_headers, db):
    doc_id, q1_id, q2_id = _create_completed_doc_with_questions(
        client, auth_headers, db, user_id=1
    )
    resp = client.get(f"/api/v1/documents/{doc_id}/questions", headers=auth_headers)
    assert resp.status_code == 200
    questions = resp.json()
    assert len(questions) >= 2
    texts = [q["text"] for q in questions]
    assert "What is 2 + 2?" in texts


def test_get_single_question(client, auth_headers, db):
    doc_id, q1_id, q2_id = _create_completed_doc_with_questions(
        client, auth_headers, db, user_id=1
    )
    resp = client.get(f"/api/v1/questions/{q1_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == q1_id
    assert data["text"] == "What is 2 + 2?"
    assert data["confidence"] == 0.97
    assert data["options"] == ["A. 3", "B. 4", "C. 5"]


def test_get_warnings_returns_low_confidence(client, auth_headers, db):
    doc_id, q1_id, q2_id = _create_completed_doc_with_questions(
        client, auth_headers, db, user_id=1
    )
    resp = client.get(f"/api/v1/documents/{doc_id}/warnings", headers=auth_headers)
    assert resp.status_code == 200
    warnings = resp.json()
    # q2 has confidence 0.45 and no answer — should appear in warnings
    warning_ids = [w["question_id"] for w in warnings]
    assert q2_id in warning_ids


def test_get_questions_pending_doc_returns_202(client, auth_headers):
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("pending.pdf", io.BytesIO(VALID_PDF), "application/pdf")},
        headers=auth_headers,
    )
    doc_id = upload_resp.json()["id"]
    resp = client.get(f"/api/v1/documents/{doc_id}/questions", headers=auth_headers)
    assert resp.status_code == 202


def test_get_answers(client, auth_headers, db):
    doc_id, q1_id, q2_id = _create_completed_doc_with_questions(
        client, auth_headers, db, user_id=1
    )
    resp = client.get(f"/api/v1/documents/{doc_id}/answers", headers=auth_headers)
    assert resp.status_code == 200
    answers = resp.json()
    assert isinstance(answers, list)
    # q2 has no answer
    q2_answer = next((a for a in answers if a["question_id"] == q2_id), None)
    assert q2_answer is not None
    assert q2_answer["answer"] is None
    assert q2_answer["answer_status"] == "not_found"
