from __future__ import annotations

import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from taskbridge.model_providers import OpenAICompatibleModel


def tool_output() -> dict:
    return {
        "summary": "Language-heavy work needs review.",
        "summary_evidence_ids": ["ev-structure", "ev-risk"],
        "observations": [{
            "claim": "Unstructured inputs represent 70% of the work.",
            "evidence_ids": ["ev-structure"],
            "confidence": 0.92,
        }],
        "proposed_tools": [{
            "tool_name": "hold_for_review",
            "reason": "Medium error cost requires review.",
            "evidence_ids": ["ev-risk"],
            "requires_approval": True,
        }],
        "abstain": False,
        "abstention_reason": None,
    }


class Response(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def response_payload() -> bytes:
    return json.dumps({
        "model": "fixture-model-2026-09",
        "choices": [{
            "message": {
                "tool_calls": [{
                    "function": {
                        "name": "record_workflow_analysis",
                        "arguments": json.dumps(tool_output()),
                    },
                }],
            },
        }],
        "usage": {"prompt_tokens": 612, "completion_tokens": 184},
    }).encode()


def test_openai_compatible_provider_forces_tool_schema(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return Response(response_payload())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    model = OpenAICompatibleModel("https://models.example.test/v1/chat/completions", "fixture")
    result = model.complete("system", "user")
    assert captured["body"]["tool_choice"]["function"]["name"] == "record_workflow_analysis"
    assert captured["body"]["tools"][0]["function"]["parameters"]["additionalProperties"] is False
    assert result.model == "fixture-model-2026-09"
    assert result.input_tokens == 612
    assert result.output_tokens == 184


def test_provider_adds_bearer_header_without_persisting_it(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["authorization"] = request.headers["Authorization"]
        return Response(response_payload())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    model = OpenAICompatibleModel(
        "https://models.example.test/v1/chat/completions", "fixture", api_key="secret"
    )
    result = model.complete("system", "user")
    assert captured["authorization"] == "Bearer secret"
    assert "secret" not in repr(result)


def test_provider_retries_transient_http_failure(monkeypatch):
    attempts = 0

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise HTTPError(request.full_url, 429, "rate limited", {}, None)
        return Response(response_payload())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    monkeypatch.setattr("time.sleep", lambda _: None)
    result = OpenAICompatibleModel("https://models.example.test", "fixture").complete(
        "system", "user"
    )
    assert attempts == 2
    assert result.retry_count == 1


def test_provider_rejects_non_schema_response(monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: Response(json.dumps({"choices": []}).encode()),
    )
    with pytest.raises(ValueError, match="required tool schema"):
        OpenAICompatibleModel("https://models.example.test", "fixture").complete(
            "system", "user"
        )
