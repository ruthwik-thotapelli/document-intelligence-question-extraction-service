"""Tests for authentication endpoints."""
import pytest


def test_register_success(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "TestPass123!"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert "id" in data


def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "TestPass123!"}
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_login_success(client):
    client.post("/api/v1/auth/register", json={
        "email": "loginuser@example.com",
        "password": "TestPass123!"
    })
    resp = client.post("/api/v1/auth/login", data={
        "username": "loginuser@example.com",
        "password": "TestPass123!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "email": "wrongpass@example.com",
        "password": "CorrectPass123!"
    })
    resp = client.post("/api/v1/auth/login", data={
        "username": "wrongpass@example.com",
        "password": "WrongPass!"
    })
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    resp = client.post("/api/v1/auth/login", data={
        "username": "nobody@example.com",
        "password": "anypass"
    })
    assert resp.status_code == 401


def test_protected_endpoint_without_token(client):
    resp = client.get("/api/v1/documents/")
    assert resp.status_code == 401
