from __future__ import annotations

import pytest
import json
from pathlib import Path

from taskbridge.evaluate import OFFLINE_CASES, evaluate


def test_offline_evaluation_never_configures_or_calls_provider(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Offline evaluation attempted provider access")

    monkeypatch.setattr("taskbridge.evaluate.configured_model", forbidden)
    monkeypatch.setattr("urllib.request.urlopen", forbidden)
    report = evaluate()
    assert report["expectations_met"] == len(OFFLINE_CASES)
    assert report["provider_requests"] == 0
    assert report["live_provider_benchmark"] == "NOT_RUN"
    assert len(report["known_limitations"]) == 2


def test_offline_report_is_reproducible():
    assert evaluate() == evaluate()


def test_committed_report_matches_current_evaluation():
    committed = Path(__file__).resolve().parents[1] / "evaluations" / "offline-results.json"
    assert evaluate() == json.loads(committed.read_text())


def test_live_evaluation_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setattr("taskbridge.evaluate.configured_model", lambda: pytest.fail("Provider loaded before consent"))
    with pytest.raises(ValueError, match="explicit"):
        evaluate("live")


def test_deterministic_provider_cannot_masquerade_as_live(monkeypatch):
    from taskbridge.model_providers import DeterministicModel
    monkeypatch.setattr("taskbridge.evaluate.configured_model", DeterministicModel)
    with pytest.raises(ValueError, match="HTTP model"):
        evaluate("live", allow_provider_requests=True)


def test_semantic_counterexample_is_visible_not_presented_as_proof():
    report = evaluate()
    row = next(item for item in report["results"] if item["case"] == "semantic-counterexample")
    assert row["semantic_review_required"]
    assert "not semantic entailment" in report["validation_scope"]
