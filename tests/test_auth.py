from __future__ import annotations

import hashlib
import pytest

from fastapi.testclient import TestClient

from conftest import workflow_payload
from taskbridge.api import create_app
from taskbridge.auth import auth_required, validate_runtime_config


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


def production_config(monkeypatch):
    monkeypatch.setenv("TASKBRIDGE_ENV", "production")
    monkeypatch.setenv("TASKBRIDGE_REQUIRE_AUTH", "true")
    for role in ("VIEWER", "OPERATOR", "ADMIN"):
        monkeypatch.setenv(f"TASKBRIDGE_{role}_TOKEN_SHA256", digest(f"fixture-{role}-token"))


@pytest.mark.parametrize("value", ["false", "", "yes", "tru"])
def test_production_cannot_disable_auth(tmp_path, monkeypatch, value):
    production_config(monkeypatch)
    monkeypatch.setenv("TASKBRIDGE_REQUIRE_AUTH", value)
    assert auth_required()
    with pytest.raises(ValueError, match="AUTH"):
        create_app(tmp_path / "must-not-exist.db")
    assert not (tmp_path / "must-not-exist.db").exists()


@pytest.mark.parametrize("value", ["", "invalid", "A" * 64, digest("")])
def test_production_rejects_missing_or_bad_digests(monkeypatch, value):
    production_config(monkeypatch)
    monkeypatch.setenv("TASKBRIDGE_OPERATOR_TOKEN_SHA256", value)
    with pytest.raises(ValueError, match="digest|tokens"):
        validate_runtime_config("postgresql://user:strong-fixture-password@127.0.0.1/test")


def test_production_rejects_role_escalation_through_reused_digest(monkeypatch):
    production_config(monkeypatch)
    monkeypatch.setenv("TASKBRIDGE_VIEWER_TOKEN_SHA256", digest("fixture-ADMIN-token"))
    with pytest.raises(ValueError, match="distinct"):
        validate_runtime_config("postgresql://user:strong-fixture-password@127.0.0.1/test")


@pytest.mark.parametrize("database", [
    "local.db", "postgresql://localhost/test",
    "postgresql://taskbridge:taskbridge@localhost/test",
    "postgresql://user:short@localhost/test",
])
def test_production_rejects_demo_database_settings(monkeypatch, database):
    production_config(monkeypatch)
    with pytest.raises(ValueError, match="Production requires"):
        validate_runtime_config(database)


def test_valid_production_configuration_passes_without_network(monkeypatch):
    production_config(monkeypatch)
    validate_runtime_config("postgresql://user:strong-fixture-password@127.0.0.1/test")


def test_misspelled_environment_is_not_silently_demo(monkeypatch):
    monkeypatch.setenv("TASKBRIDGE_ENV", "prodution")
    with pytest.raises(ValueError, match="ENV"):
        validate_runtime_config("local.db")
