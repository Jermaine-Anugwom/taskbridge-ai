"""Real PostgreSQL tests, each in its own disposable schema. Never restore over user data."""
from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pytest
from fastapi.testclient import TestClient

from conftest import workflow_payload
from taskbridge.api import create_app
from taskbridge.engine import capture_workflow, simulate_pilot
from taskbridge.model_providers import DeterministicModel
from taskbridge.model_runtime import run_model_analysis, trace_fingerprint
from taskbridge.repository import Repository
from taskbridge.scenarios import load_scenario
from test_auth import production_config

pytestmark = pytest.mark.postgres


@pytest.fixture
def postgres_url():
    url = os.getenv("TASKBRIDGE_TEST_POSTGRES_URL")
    if not url:
        if os.getenv("TASKBRIDGE_REQUIRE_POSTGRES_TESTS") == "true":
            pytest.fail("PostgreSQL integration URL is required in this CI job")
        pytest.skip("Real PostgreSQL not configured; not a passing integration result")
    parsed = urlsplit(url)
    if parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.path != "/taskbridge_test":
        pytest.fail("Integration tests accept only a loopback taskbridge_test database")
    import psycopg
    from psycopg import sql

    schema = f"taskbridge_test_{uuid.uuid4().hex}"
    with psycopg.connect(url) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    # Discard caller search_path options; every Repository connection uses only this new schema.
    query = [(key, value) for key, value in parse_qsl(parsed.query) if key != "options"]
    query.append(("options", f"-csearch_path={schema}"))
    isolated_url = urlunsplit(parsed._replace(query=urlencode(query)))
    try:
        yield isolated_url
    finally:
        with psycopg.connect(url) as connection:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def test_workflow_survives_new_connection(postgres_url):
    record = capture_workflow(workflow_payload(), "wf-pg")
    Repository(postgres_url).save("workflows", record.workflow_id, record)
    assert Repository(postgres_url).get("workflows", record.workflow_id) == record.model_dump(mode="json")


def test_trace_preserves_null_usage_and_attempts(postgres_url):
    class TimeoutModel:
        def complete(self, *_):
            raise TimeoutError("synthetic outage")

    workflow = capture_workflow(workflow_payload(), "wf-pg")
    trace = run_model_analysis(workflow, "Analyze workflow", TimeoutModel())
    repository = Repository(postgres_url)
    repository.save("model_traces", trace.trace_id, trace, workflow_id=workflow.workflow_id,
                    fingerprint=trace_fingerprint(trace))
    result = Repository(postgres_url).list_model_traces()[0]
    assert result["usage"]["input_tokens"] is None
    assert len(result["attempts"]) == 2
    assert result == trace.model_dump(mode="json")


def test_concurrent_upsert_does_not_duplicate_record(postgres_url):
    repository = Repository(postgres_url)
    record = capture_workflow(workflow_payload(), "wf-pg")
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda _: repository.save("workflows", record.workflow_id, record), range(12)))
    with repository._connect() as connection:
        assert connection.execute("SELECT count(*) AS count FROM workflows").fetchone()["count"] == 1


def test_transaction_rolls_back_on_exception(postgres_url):
    repository = Repository(postgres_url)
    with pytest.raises(RuntimeError, match="deliberate"):
        with repository._connect() as connection:
            connection.execute("INSERT INTO workflows VALUES (%s, %s, %s)", ("rollback", "{}", "now"))
            raise RuntimeError("deliberate rollback")
    assert repository.get("workflows", "rollback") is None


def test_pilot_fingerprint_uniqueness(postgres_url):
    import psycopg

    repository = Repository(postgres_url)
    run = simulate_pilot("pilot-pg", "shared-inbox", load_scenario("shared-inbox"))
    repository.save("pilot_runs", run.run_id, run, pilot_id=run.pilot_id, fingerprint=run.fingerprint)
    with pytest.raises(psycopg.errors.UniqueViolation):
        repository.save("pilot_runs", "duplicate", run, pilot_id=run.pilot_id, fingerprint=run.fingerprint)
    assert repository.get_run_by_fingerprint(run.fingerprint) == run.model_dump(mode="json")


def test_production_api_rbac_and_persisted_trace(postgres_url, monkeypatch):
    production_config(monkeypatch)
    monkeypatch.setenv("TASKBRIDGE_MODEL_PROVIDER", "deterministic")
    client = TestClient(create_app(postgres_url))
    payload = workflow_payload().model_dump(mode="json")
    assert client.post("/api/workflows", json=payload).status_code == 401
    viewer = {"Authorization": "Bearer fixture-VIEWER-token"}
    operator = {"Authorization": "Bearer fixture-OPERATOR-token"}
    assert client.post("/api/workflows", json=payload, headers=viewer).status_code == 403
    workflow = client.post("/api/workflows", json=payload, headers=operator).json()
    result = client.post(f"/api/workflows/{workflow['workflow_id']}/model-analysis", json={}, headers=operator)
    assert result.status_code == 200
    restarted = TestClient(create_app(postgres_url))
    traces = restarted.get("/api/operations/model-traces", headers=viewer).json()
    assert traces[0]["trace_id"] == result.json()["trace_id"]
    assert traces[0]["attempts"][0]["provider"] == "deterministic"


def test_trace_order_and_limit(postgres_url):
    repository = Repository(postgres_url)
    workflow = capture_workflow(workflow_payload(), "wf-pg")
    for _ in range(3):
        trace = run_model_analysis(workflow, "Analyze workflow", DeterministicModel())
        repository.save("model_traces", trace.trace_id, trace, workflow_id=workflow.workflow_id,
                        fingerprint=trace_fingerprint(trace))
    assert repository.list_model_traces(1)[0]["trace_id"] == trace.trace_id
    assert len(repository.list_model_traces(2)) == 2
