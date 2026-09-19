"""
Test configuration and fixtures.
Uses an in-memory SQLite database for fast, isolated tests.
Mocks the Celery task to prevent actual background processing during tests.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_db
from app.main import app
from app.models.base import Base

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with patch("app.tasks.document_tasks.process_document.delay") as mock_task:
        mock_task.return_value = MagicMock()
        with TestClient(app) as c:
            yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Register a user and return auth headers."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "testuser@example.com", "password": "StrongPass123!"},
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser@example.com", "password": "StrongPass123!"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
