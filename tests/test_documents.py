"""Tests for document upload and management endpoints."""
import io
import pytest


# Minimal valid PDF magic bytes
VALID_PDF = b"%PDF-1.4 fake content"
VALID_PNG = b"\x89PNG\r\n\x1a\n fake content"
VALID_JPG = b"\xff\xd8\xff fake content"


def test_upload_pdf(client, auth_headers):
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", io.BytesIO(VALID_PDF), "application/pdf")},
        headers=auth_headers,
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "pending"
    assert data["filename"] == "test.pdf"
    assert "id" in data


def test_upload_png(client, auth_headers):
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.png", io.BytesIO(VALID_PNG), "image/png")},
        headers=auth_headers,
    )
    assert resp.status_code == 202


def test_upload_jpg(client, auth_headers):
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.jpg", io.BytesIO(VALID_JPG), "image/jpeg")},
        headers=auth_headers,
    )
    assert resp.status_code == 202


def test_upload_unsupported_type(client, auth_headers):
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("malware.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")},
        headers=auth_headers,
    )
    assert resp.status_code == 415


def test_upload_empty_file(client, auth_headers):
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_get_document_status(client, auth_headers):
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("status_test.pdf", io.BytesIO(VALID_PDF), "application/pdf")},
        headers=auth_headers,
    )
    doc_id = upload_resp.json()["id"]

    resp = client.get(f"/api/v1/documents/{doc_id}/status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == doc_id
    assert data["status"] in {"pending", "processing", "completed", "failed"}


def test_get_document_unauthorized(client, auth_headers):
    """A second user should not be able to access another user's document."""
    # Register second user
    client.post("/api/v1/auth/register", json={
        "email": "user2@example.com", "password": "Pass123!"
    })
    login_resp = client.post("/api/v1/auth/login", data={
        "username": "user2@example.com", "password": "Pass123!"
    })
    user2_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # Upload with user1
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("secret.pdf", io.BytesIO(VALID_PDF), "application/pdf")},
        headers=auth_headers,
    )
    doc_id = upload_resp.json()["id"]

    # Try to access with user2
    resp = client.get(f"/api/v1/documents/{doc_id}", headers=user2_headers)
    assert resp.status_code == 404


def test_list_documents(client, auth_headers):
    resp = client.get("/api/v1/documents/", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_upload_without_auth(client):
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", io.BytesIO(VALID_PDF), "application/pdf")},
    )
    assert resp.status_code == 401
