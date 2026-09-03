"""Reproducible synthetic evaluation. Offline by default; never reads model credentials offline."""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass

from .engine import capture_workflow
from .model_providers import (
    DeterministicModel, OpenAICompatibleModel, ProviderFailure, ProviderResult, configured_model,
)
from .model_runtime import PROMPT_VERSION, SCHEMA_VERSION, run_model_analysis
from .models import ModelAttempt, ModelUsage, StructuredModelOutput, WorkflowCreate

DATASET_VERSION = "synthetic-workflow-reliability-v1"
SCENARIOS = (
    ("shared-inbox", "Route synthetic inbox requests to the correct service team.", 0.7),
    ("weekly-status", "Prepare a synthetic weekly status draft for owner review.", 0.9),
    ("invoice-exceptions", "Compare synthetic invoices with approved purchase orders.", 0.1),
)


def evaluation_workflow(scenario=SCENARIOS[0]):
    name, summary, ratio = scenario
    return capture_workflow(WorkflowCreate(
        name=f"SYNTHETIC {name}", summary=summary,
        trigger="A synthetic record arrives in the test queue.",
        desired_outcome="A reviewer receives a supported draft.", systems=["Synthetic queue"],
        steps=[{"step_id": "step-review", "actor": "Synthetic reviewer", "action": "review the record",
                "system": "Synthetic queue", "minutes": 8, "is_decision": True}],
        exceptions=["Missing owner"], frequency_per_week=180, minutes_per_run=8,
        error_cost="medium", data_sensitivity="medium", rule_stability=4, reversibility=4,
        unstructured_input_ratio=ratio,
    ), f"wf-evaluation-{name}")


def _output():
    return StructuredModelOutput(
        summary="A person should review the workflow change.", summary_evidence_ids=["ev-risk"],
        observations=[{"claim": "Unstructured inputs represent 70% of the work.",
                       "evidence_ids": ["ev-structure"], "confidence": 0.9}],
        proposed_tools=[{"tool_name": "hold_for_review", "reason": "Review the workflow risk.",
                         "evidence_ids": ["ev-risk"], "requires_approval": True}], abstain=False,
    )


@dataclass
class ScriptedModel:
    """Response fixture, not a live model and not a measure of model intelligence."""
    case: str

    def complete(self, *_):
        output = _output()
        usage = ModelUsage(input_tokens=120, output_tokens=45)
        attempts = []
        if self.case == "missing-usage":
            usage = ModelUsage()
        elif self.case == "zero-usage":
            usage = ModelUsage(input_tokens=0, output_tokens=0)
        elif self.case == "partial-usage":
            usage.output_tokens = None
        elif self.case == "unknown-evidence":
            output.summary_evidence_ids = ["ev-does-not-exist"]
        elif self.case == "unsupported-number":
            output.observations[0].claim = "Unstructured inputs represent 99% of the work."
        elif self.case == "unapproved-action":
            output.proposed_tools[0].requires_approval = False
        elif self.case == "semantic-counterexample":
            output.summary = "The company has eliminated all operational errors."
        elif self.case == "timeout":
            raise ProviderFailure("TimeoutError", [ModelAttempt(
                provider="scripted-fixture", model="fixture-v1", status="transport_error",
            )])
        elif self.case == "schema-rejected":
            raise ProviderFailure("InvalidToolSchema", [ModelAttempt(
                provider="scripted-fixture", model="fixture-v1", status="schema_rejected", usage=usage,
            )])
        elif self.case == "unknown-retry-then-success":
            attempts.append(ModelAttempt(
                provider="scripted-fixture", model="fixture-v1", status="transport_error",
            ))
        attempts.append(ModelAttempt(
            provider="scripted-fixture", model="fixture-v1", status="returned",
            retry_index=len(attempts), usage=usage,
        ))
        return ProviderResult(output, "scripted-fixture", "fixture-v1", usage.input_tokens,
                              usage.output_tokens, len(attempts) - 1, tuple(attempts))


OFFLINE_CASES = {
    "supported-output": ("succeeded", 120, 45),
    "missing-usage": ("succeeded", None, None),
    "zero-usage": ("succeeded", 0, 0),
    "partial-usage": ("succeeded", 120, None),
    "unknown-evidence": ("fallback", 120, 45),
    "unsupported-number": ("fallback", 120, 45),
    "unapproved-action": ("fallback", 120, 45),
    "timeout": ("fallback", None, None),
    "schema-rejected": ("fallback", 120, 45),
    "unknown-retry-then-success": ("succeeded", None, None),
    "semantic-counterexample": ("succeeded", 120, 45),
    "deterministic-only": ("succeeded", 0, 0),
}


def evaluate(mode: str = "offline", *, allow_provider_requests: bool = False) -> dict:
    if mode not in {"offline", "live"}:
        raise ValueError("Unknown evaluation mode")
    if mode == "live" and not allow_provider_requests:
        raise ValueError("Live provider requests require explicit --allow-provider-requests; may incur cost")
    corpus = {"version": DATASET_VERSION, "workflows": [
        evaluation_workflow(scenario).model_dump(mode="json", exclude={"created_at"})
        for scenario in SCENARIOS
    ], "offline_cases": OFFLINE_CASES}
    dataset_hash = hashlib.sha256(json.dumps(corpus, sort_keys=True).encode()).hexdigest()
    base = {
        "dataset_version": DATASET_VERSION, "dataset_sha256": dataset_hash,
        "data": "SYNTHETIC", "mode": mode,
        "prompt_version": PROMPT_VERSION, "schema_version": SCHEMA_VERSION,
        "validation_scope": "reference and numeric checks only; not semantic entailment",
        "live_provider_benchmark": "NOT_RUN" if mode == "offline" else "EXECUTED",
    }
    if mode == "live":
        model = configured_model()
        if not isinstance(model, OpenAICompatibleModel):
            raise ValueError("Live evaluation requires an explicitly configured HTTP model provider")
        # Fixed three-case corpus and no retries: at most three provider requests.
        from dataclasses import replace
        model = replace(model, max_retries=0)
        rows = []
        for scenario in SCENARIOS:
            trace = run_model_analysis(evaluation_workflow(scenario),
                "Identify a safe pilot and cite only captured evidence. Do not invent savings.", model)
            rows.append({"scenario": scenario[0], "trace": trace.model_dump(mode="json")})
        return {**base, "results": rows, "semantic_review": "PENDING_HUMAN_REVIEW"}

    rows = []
    for case, expected in OFFLINE_CASES.items():
        model = DeterministicModel() if case == "deterministic-only" else ScriptedModel(case)
        trace = run_model_analysis(evaluation_workflow(), "Analyze the synthetic workflow.", model)
        observed = (trace.status.value, trace.usage.input_tokens, trace.usage.output_tokens)
        rows.append({
            "case": case, "status": trace.status.value,
            "input_tokens": trace.usage.input_tokens, "output_tokens": trace.usage.output_tokens,
            "attempts": len(trace.attempts), "expectation_met": observed == expected,
            "semantic_review_required": trace.semantic_review_required,
        })
    return {**base, "provider_requests": 0, "known_limitations": [
        "A nonnumeric fabricated statement citing existing IDs can pass mechanical validation. Human semantic review remains required.",
        "Offline fixtures validate accounting and controls, not live model quality or provider compatibility.",
    ], "results": rows, "expectations_met": sum(row["expectation_met"] for row in rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["offline", "live"], default="offline")
    parser.add_argument("--allow-provider-requests", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        report = evaluate(args.mode, allow_provider_requests=args.allow_provider_requests)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(report, indent=2))
    if args.check and args.mode == "offline" and report["expectations_met"] != len(OFFLINE_CASES):
        raise SystemExit(1)
    if args.check and args.mode == "live" and any(
        row["trace"]["status"] != "succeeded" for row in report["results"]
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
