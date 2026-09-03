from __future__ import annotations

import hashlib

from fastapi.testclient import TestClient

from conftest import workflow_payload
from taskbridge.api import create_app


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def test_auth_required_rejects_missing_token(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKBRIDGE_REQUIRE_AUTH", "true")
    monkeypatch.setenv("TASKBRIDGE_OPERATOR_TOKEN_SHA256", digest("operator-secret"))
    client = TestClient(create_app(tmp_path / "auth.db"))
    result = client.post("/api/workflows", json=workflow_payload().model_dump(mode="json"))
    assert result.status_code == 401


def test_operator_token_can_create_workflow(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKBRIDGE_REQUIRE_AUTH", "true")
    monkeypatch.setenv("TASKBRIDGE_OPERATOR_TOKEN_SHA256", digest("operator-secret"))
    client = TestClient(create_app(tmp_path / "auth.db"))
    result = client.post(
        "/api/workflows",
        json=workflow_payload().model_dump(mode="json"),
        headers={"Authorization": "Bearer operator-secret"},
    )
    assert result.status_code == 201


def test_viewer_cannot_create_workflow(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKBRIDGE_REQUIRE_AUTH", "true")
    monkeypatch.setenv("TASKBRIDGE_VIEWER_TOKEN_SHA256", digest("viewer-secret"))
    client = TestClient(create_app(tmp_path / "auth.db"))
    result = client.post(
        "/api/workflows",
        json=workflow_payload().model_dump(mode="json"),
        headers={"Authorization": "Bearer viewer-secret"},
    )
    assert result.status_code == 403


def test_invalid_token_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKBRIDGE_REQUIRE_AUTH", "true")
    monkeypatch.setenv("TASKBRIDGE_OPERATOR_TOKEN_SHA256", digest("operator-secret"))
    client = TestClient(create_app(tmp_path / "auth.db"))
    result = client.post(
        "/api/workflows",
        json=workflow_payload().model_dump(mode="json"),
        headers={"Authorization": "Bearer wrong"},
    )
    assert result.status_code == 401
