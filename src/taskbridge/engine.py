from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable

from .models import (
    Assessment,
    Audience,
    AudienceBrief,
    EvidenceItem,
    OptionScore,
    PilotDecision,
    PilotRun,
    RecommendationKind,
    RiskLevel,
    ScenarioRecord,
    WorkflowCreate,
    WorkflowRecord,
)
from .security import assert_safe_text, find_untrusted_instruction


def _clamp(value: float) -> int:
    return round(max(0, min(100, value)))


def capture_workflow(payload: WorkflowCreate, workflow_id: str) -> WorkflowRecord:
    text_values = [payload.name, payload.summary, payload.trigger, payload.desired_outcome]
    text_values.extend(payload.systems)
    text_values.extend(payload.exceptions)
    for step in payload.steps:
        text_values.extend((step.actor, step.action, step.system))
    assert_safe_text(*text_values)

    evidence = [
        EvidenceItem(evidence_id="ev-trigger", statement=f"Trigger: {payload.trigger}"),
        EvidenceItem(
            evidence_id="ev-volume",
            statement=f"The task runs {payload.frequency_per_week} times per week.",
        ),
        EvidenceItem(
            evidence_id="ev-effort",
            statement=f"Each run currently takes {payload.minutes_per_run} minutes.",
        ),
        EvidenceItem(
            evidence_id="ev-structure",
            statement=(
                f"Unstructured inputs represent {payload.unstructured_input_ratio:.0%} of the work."
            ),
        ),
        EvidenceItem(
            evidence_id="ev-risk",
            statement=(
                f"Error cost is {payload.error_cost.value}; data sensitivity is "
                f"{payload.data_sensitivity.value}."
            ),
        ),
        EvidenceItem(
            evidence_id="ev-stability",
            statement=f"Rule stability was rated {payload.rule_stability} of 5.",
        ),
    ]
    evidence.extend(
        EvidenceItem(
            evidence_id=f"ev-{step.step_id}",
            statement=f"{step.actor} uses {step.system} to {step.action}.",
        )
        for step in payload.steps
    )
    return WorkflowRecord(workflow_id=workflow_id, evidence=evidence, **payload.model_dump())


def assess_workflow(workflow: WorkflowRecord, assessment_id: str) -> Assessment:
    volume = min(workflow.frequency_per_week / 25, 1)
    effort = min(workflow.minutes_per_run / 90, 1)
    structure = 1 - workflow.unstructured_input_ratio
    stability = workflow.rule_stability / 5
    reversibility = workflow.reversibility / 5
    exception_density = min(len(workflow.exceptions) / 4, 1)
    high_consequence = workflow.error_cost == RiskLevel.HIGH
    sensitive = workflow.data_sensitivity == RiskLevel.HIGH

    rules_score = _clamp(
        22 + 28 * structure + 24 * stability + 14 * volume + 12 * reversibility
    )
    ai_score = _clamp(
        18
        + 42 * workflow.unstructured_input_ratio
        + 15 * volume
        + 14 * effort
        + 11 * reversibility
        - (18 if high_consequence else 0)
        - (12 if sensitive else 0)
    )
    hybrid_score = _clamp(
        35
        + 18 * workflow.unstructured_input_ratio
        + 14 * stability
        + 15 * exception_density
        + 10 * volume
        + (8 if high_consequence or sensitive else 0)
    )
    no_change_score = _clamp(
        18
        + (35 if workflow.frequency_per_week <= 1 else 0)
        + (25 if workflow.minutes_per_run <= 15 else 0)
        + (22 if workflow.rule_stability <= 2 else 0)
        + (12 if workflow.reversibility <= 2 else 0)
    )

    if workflow.frequency_per_week <= 1 and workflow.minutes_per_run <= 20:
        recommendation = RecommendationKind.NO_CHANGE
    elif workflow.rule_stability >= 4 and workflow.unstructured_input_ratio <= 0.25:
        recommendation = RecommendationKind.RULES
    elif (
        workflow.unstructured_input_ratio >= 0.65
        and workflow.error_cost == RiskLevel.LOW
        and workflow.data_sensitivity == RiskLevel.LOW
    ):
        recommendation = RecommendationKind.AI_ASSIST
    else:
        recommendation = RecommendationKind.HYBRID

    explanations = {
        RecommendationKind.RULES: "Stable rules and structured inputs favor predictable automation.",
        RecommendationKind.AI_ASSIST: "Language-heavy inputs benefit from AI assistance with visible review.",
        RecommendationKind.HYBRID: "Rules can handle the known path while people review uncertain cases.",
        RecommendationKind.NO_CHANGE: "Current volume and effort do not justify adding a new system.",
    }
    options = [
        OptionScore(kind=RecommendationKind.RULES, score=rules_score, explanation=explanations[RecommendationKind.RULES]),
        OptionScore(kind=RecommendationKind.AI_ASSIST, score=ai_score, explanation=explanations[RecommendationKind.AI_ASSIST]),
        OptionScore(kind=RecommendationKind.HYBRID, score=hybrid_score, explanation=explanations[RecommendationKind.HYBRID]),
        OptionScore(kind=RecommendationKind.NO_CHANGE, score=no_change_score, explanation=explanations[RecommendationKind.NO_CHANGE]),
    ]

    risks: list[str] = []
    checkpoints = ["A person reviews every low-confidence or exception record."]
    if sensitive:
        risks.append("Sensitive data requires approved storage and model boundaries.")
        checkpoints.append("IT or security approves the data path before a live pilot.")
    if high_consequence:
        risks.append("A wrong decision could materially affect the operation.")
        checkpoints.append("The process owner approves every consequential outcome.")
    if workflow.rule_stability <= 2:
        risks.append("The process changes too often for unattended automation.")
    if not workflow.exceptions:
        risks.append("No exception examples were captured during discovery.")

    top_reasons = {
        RecommendationKind.RULES: [
            "The decision rules are stable and the inputs are mostly structured.",
            "The task repeats often enough to justify a deterministic workflow.",
        ],
        RecommendationKind.AI_ASSIST: [
            "Most inputs arrive as language rather than fixed fields.",
            "The work is reversible and low consequence, so suggestions can be reviewed safely.",
        ],
        RecommendationKind.HYBRID: [
            "The common path is predictable, but exceptions still require judgment.",
            "AI can organize the language while rules and people keep authority.",
        ],
        RecommendationKind.NO_CHANGE: [
            "The task occurs too infrequently to repay the cost of a new system.",
            "A lightweight process adjustment is safer than adding automation.",
        ],
    }
    return Assessment(
        assessment_id=assessment_id,
        workflow_id=workflow.workflow_id,
        recommendation=recommendation,
        confidence="high" if workflow.exceptions else "medium",
        options=options,
        reasons=top_reasons[recommendation],
        evidence_ids=["ev-volume", "ev-effort", "ev-structure", "ev-risk", "ev-stability"],
        risks=risks,
        human_checkpoints=checkpoints,
        unknowns=[] if workflow.exceptions else ["Representative exception examples"],
    )


def explain_assessment(workflow: WorkflowRecord, assessment: Assessment, audience: Audience) -> AudienceBrief:
    label = assessment.recommendation.value.replace("_", " ")
    content = {
        Audience.EMPLOYEE: (
            "The proposed pilot removes repeated sorting and copying. You still handle exceptions "
            "and decide anything that could affect a customer, payment, or commitment."
        ),
        Audience.MANAGER: (
            "The pilot standardizes the common path, sends uncertain work to a named owner, and "
            "measures touch time, overrides, and errors before any expansion."
        ),
        Audience.EXECUTIVE: (
            "This is a bounded workflow pilot, not a broad AI rollout. Continue only if observed "
            "adoption and operating results improve without increasing exception risk."
        ),
        Audience.IT_SECURITY: (
            "The default engine is deterministic and local. Inputs are treated as untrusted, "
            "external writes are disabled, and every decision retains an evidence reference."
        ),
    }
    unchanged = [
        "The process owner remains accountable for the outcome.",
        "Exceptions and low-confidence records remain visible to people.",
        "No synthetic result is presented as a company outcome.",
    ]
    return AudienceBrief(
        audience=audience,
        title=f"What {label} means for {workflow.name}",
        explanation=content[audience],
        what_changes=[
            "The common path is captured as an inspectable sequence.",
            "Uncertain records are routed to a visible review point.",
        ],
        what_does_not_change=unchanged,
        evidence_ids=assessment.evidence_ids,
    )


def _fingerprint(pilot_id: str, records: Iterable[ScenarioRecord]) -> str:
    payload = [record.model_dump(mode="json") for record in records]
    raw = json.dumps({"pilot_id": pilot_id, "records": payload}, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def simulate_pilot(pilot_id: str, scenario_id: str, records: list[ScenarioRecord]) -> PilotRun:
    fingerprint = _fingerprint(pilot_id, records)
    decisions: list[PilotDecision] = []
    for record in records:
        evidence = [f"record:{record.record_id}"]
        if find_untrusted_instruction(f"{record.subject} {record.body}"):
            decisions.append(PilotDecision(
                record_id=record.record_id,
                disposition="blocked",
                explanation="The record contains an instruction directed at the processing system.",
                confidence=1,
                evidence_ids=evidence,
                human_checkpoint="Inspect the original record outside the automation path.",
            ))
            continue

        if scenario_id == "shared-inbox":
            missing = not record.fields.get("account_id")
            urgent = any(word in record.body.casefold() for word in ("urgent", "outage", "stopped"))
            if missing:
                disposition, explanation, confidence, checkpoint = (
                    "review",
                    "An account identifier is required before routing.",
                    0.58,
                    "Confirm the account and destination queue.",
                )
            else:
                disposition = "priority_service" if urgent else "standard_service"
                explanation = "Known account and request language satisfy the routing rule."
                confidence, checkpoint = 0.93, None
        elif scenario_id == "weekly-status":
            if not record.fields.get("owner"):
                disposition, explanation, confidence, checkpoint = (
                    "review",
                    "The update has no accountable owner.",
                    0.61,
                    "Assign an owner before including this update.",
                )
            else:
                disposition, explanation, confidence, checkpoint = (
                    "include",
                    "The update has an owner, status, and next action.",
                    0.9,
                    None,
                )
        else:
            duplicate = bool(record.fields.get("duplicate"))
            variance = abs(float(record.fields.get("invoice_total", 0)) - float(record.fields.get("po_total", 0)))
            if duplicate or variance > 25:
                disposition, explanation, confidence, checkpoint = (
                    "hold",
                    "A duplicate signal or amount variance exceeds the deterministic rule.",
                    0.99,
                    "Accounts payable reviews the source documents.",
                )
            else:
                disposition, explanation, confidence, checkpoint = (
                    "clear",
                    "The invoice matches the purchase-order tolerance and is not duplicated.",
                    0.99,
                    None,
                )
        decisions.append(PilotDecision(
            record_id=record.record_id,
            disposition=disposition,
            explanation=explanation,
            confidence=confidence,
            evidence_ids=evidence,
            human_checkpoint=checkpoint,
        ))

    held = sum(item.human_checkpoint is not None and item.disposition != "blocked" for item in decisions)
    blocked = sum(item.disposition == "blocked" for item in decisions)
    automated = len(decisions) - held - blocked
    baseline = len(records) * 8
    pilot_minutes = automated * 2 + held * 8 + blocked * 6
    return PilotRun(
        run_id=f"run-{fingerprint[:12]}",
        pilot_id=pilot_id,
        fingerprint=fingerprint,
        status="synthetic_complete",
        decisions=decisions,
        processed=len(decisions),
        automated=automated,
        held_for_review=held,
        blocked=blocked,
        synthetic_baseline_minutes=baseline,
        synthetic_pilot_minutes=pilot_minutes,
    )
