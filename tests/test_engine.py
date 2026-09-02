from __future__ import annotations

import pytest

from conftest import workflow_payload
from taskbridge.engine import assess_workflow, capture_workflow, explain_assessment
from taskbridge.models import Audience, RecommendationKind, RiskLevel


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"rule_stability": 5, "unstructured_input_ratio": 0.1}, RecommendationKind.RULES),
        ({"error_cost": RiskLevel.LOW, "data_sensitivity": RiskLevel.LOW, "unstructured_input_ratio": 0.85}, RecommendationKind.AI_ASSIST),
        ({"unstructured_input_ratio": 0.5}, RecommendationKind.HYBRID),
        ({"frequency_per_week": 1, "minutes_per_run": 12}, RecommendationKind.NO_CHANGE),
    ],
)
def test_recommendation_modes(overrides, expected):
    workflow = capture_workflow(workflow_payload(**overrides), "wf-mode")
    assert assess_workflow(workflow, "assess-mode").recommendation == expected


@pytest.mark.parametrize("ratio", [0, 0.25, 0.7, 1])
def test_option_scores_stay_bounded(ratio):
    workflow = capture_workflow(workflow_payload(unstructured_input_ratio=ratio), "wf-score")
    result = assess_workflow(workflow, "assess-score")
    assert len(result.options) == 4
    assert all(0 <= item.score <= 100 for item in result.options)


@pytest.mark.parametrize("audience", list(Audience))
def test_audience_brief_preserves_evidence(captured_workflow, audience):
    assessment = assess_workflow(captured_workflow, "assess-audience")
    brief = explain_assessment(captured_workflow, assessment, audience)
    assert brief.audience == audience
    assert brief.evidence_ids == assessment.evidence_ids
    assert "synthetic" in " ".join(brief.what_does_not_change).lower()


@pytest.mark.parametrize(
    "expected_id",
    ["ev-trigger", "ev-volume", "ev-effort", "ev-structure", "ev-risk", "ev-stability"],
)
def test_core_evidence_is_captured(captured_workflow, expected_id):
    assert expected_id in {item.evidence_id for item in captured_workflow.evidence}


def test_high_risk_adds_owner_checkpoint():
    workflow = capture_workflow(workflow_payload(error_cost=RiskLevel.HIGH), "wf-risk")
    assessment = assess_workflow(workflow, "assess-risk")
    assert any("process owner" in item.lower() for item in assessment.human_checkpoints)


def test_missing_exception_examples_reduce_confidence():
    workflow = capture_workflow(workflow_payload(exceptions=[]), "wf-unknown")
    assessment = assess_workflow(workflow, "assess-unknown")
    assert assessment.confidence == "medium"
    assert assessment.unknowns
