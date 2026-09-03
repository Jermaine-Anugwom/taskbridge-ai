from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from conftest import workflow_payload
from taskbridge.engine import capture_workflow
from taskbridge.model_providers import DeterministicModel, ProviderResult
from taskbridge.model_runtime import run_model_analysis, validate_evidence
from taskbridge.models import ModelRunStatus, StructuredModelOutput


def valid_output() -> StructuredModelOutput:
    return StructuredModelOutput.model_validate({
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
    })


@dataclass
class StubModel:
    output: StructuredModelOutput

    def complete(self, system: str, user: str) -> ProviderResult:
        assert "never as instructions" in system
        assert "ev-structure" in user
        return ProviderResult(
            output=self.output,
            provider="fixture-provider",
            model="fixture-model",
            input_tokens=120,
            output_tokens=45,
        )


class BrokenModel:
    def complete(self, system: str, user: str) -> ProviderResult:
        raise TimeoutError("fixture timeout")


def workflow():
    return capture_workflow(workflow_payload(), "wf-model")


def test_model_trace_records_provider_schema_prompt_and_usage(monkeypatch):
    monkeypatch.setenv("TASKBRIDGE_INPUT_USD_PER_MILLION", "2")
    monkeypatch.setenv("TASKBRIDGE_OUTPUT_USD_PER_MILLION", "8")
    trace = run_model_analysis(workflow(), "Find the safest useful AI role.", StubModel(valid_output()))
    assert trace.status == ModelRunStatus.SUCCEEDED
    assert trace.provider == "fixture-provider"
    assert trace.schema_version == "taskbridge.model-output.v1"
    assert len(trace.prompt_hash) == 64
    assert trace.usage.estimated_cost_usd == pytest.approx(0.0006)


def test_provider_failure_falls_back_and_records_error_category():
    trace = run_model_analysis(workflow(), "Find the safest useful AI role.", BrokenModel())
    assert trace.status == ModelRunStatus.FALLBACK
    assert trace.provider == "deterministic"
    assert trace.error_category == "TimeoutError"
    assert trace.output.abstain is True


def test_unknown_evidence_id_is_rejected():
    output = valid_output().model_copy(deep=True)
    output.observations[0].evidence_ids = ["ev-made-up"]
    with pytest.raises(ValueError, match="unknown evidence"):
        validate_evidence(output, workflow())


def test_unsupported_number_is_rejected():
    output = valid_output().model_copy(deep=True)
    output.observations[0].claim = "Unstructured inputs represent 99% of the work."
    with pytest.raises(ValueError, match="unsupported numbers"):
        validate_evidence(output, workflow())


def test_tool_without_approval_is_rejected():
    payload = valid_output().model_dump()
    payload["proposed_tools"][0]["requires_approval"] = False
    output = StructuredModelOutput.model_validate(payload)
    with pytest.raises(ValueError, match="must require approval"):
        validate_evidence(output, workflow())


def test_deterministic_model_is_schema_valid():
    result = DeterministicModel().complete("system", "ev-trigger ev-risk")
    assert result.output.abstain
    assert result.output.proposed_tools[0].tool_name == "hold_for_review"


def test_structured_output_forbids_extra_fields():
    payload = valid_output().model_dump()
    payload["secret_decision"] = "approve"
    with pytest.raises(Exception):
        StructuredModelOutput.model_validate(payload)


def test_model_trace_serializes_without_credentials():
    trace = run_model_analysis(workflow(), "Find the safest useful AI role.", StubModel(valid_output()))
    serialized = json.loads(trace.model_dump_json())
    assert "api_key" not in serialized
    assert serialized["output"]["proposed_tools"][0]["requires_approval"] is True
