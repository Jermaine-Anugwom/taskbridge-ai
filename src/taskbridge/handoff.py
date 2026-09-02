from __future__ import annotations

from .models import Assessment, WorkflowRecord


def render_handoff(workflow: WorkflowRecord, assessment: Assessment) -> str:
    recommendation = assessment.recommendation.value.replace("_", " ").title()
    risks = "\n".join(f"- {item}" for item in assessment.risks) or "- No additional risks recorded."
    checkpoints = "\n".join(f"- {item}" for item in assessment.human_checkpoints)
    return f"""# TaskBridge pilot handoff: {workflow.name}

> Synthetic planning artifact. This is not evidence of a company deployment or outcome.

## Pilot charter

Test **{recommendation}** against the captured workflow without enabling external writes.

## Current workflow

- Trigger: {workflow.trigger}
- Desired outcome: {workflow.desired_outcome}
- Frequency: {workflow.frequency_per_week} times per week
- Current touch time: {workflow.minutes_per_run} minutes per run

## Updated operating procedure

1. Admit the source record as untrusted input.
2. Apply the deterministic common-path rules.
3. Route missing, contradictory, or low-confidence information to review.
4. Preserve the source evidence with the decision.
5. Measure touch time, overrides, holds, and errors before expanding the pilot.

## Human checkpoints

{checkpoints}

## Risk register

{risks}

## Success measures

- Observed touch time compared with an observed baseline
- Exception and override rate
- Unsupported decision count
- Employee-reported clarity and usefulness

## Rollback

Disable the pilot path, retain the audit records, and return every new item to the documented manual procedure.

## Training guide

Show employees what the system reads, what it recommends, when it stops, and who remains responsible for the final decision.
"""
