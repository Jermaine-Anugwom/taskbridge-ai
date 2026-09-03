from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecommendationKind(StrEnum):
    RULES = "deterministic_automation"
    AI_ASSIST = "ai_assistance"
    HYBRID = "hybrid_workflow"
    NO_CHANGE = "leave_unchanged"


class Audience(StrEnum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    EXECUTIVE = "executive"
    IT_SECURITY = "it_security"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModelRunStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FALLBACK = "fallback"
    BLOCKED = "blocked"


class WorkflowStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(pattern=r"^step-[a-z0-9-]+$")
    actor: str = Field(min_length=2, max_length=80)
    action: str = Field(min_length=3, max_length=240)
    system: str = Field(min_length=2, max_length=80)
    minutes: int = Field(ge=0, le=480)
    is_decision: bool = False


class WorkflowCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=100)
    summary: str = Field(min_length=10, max_length=800)
    trigger: str = Field(min_length=3, max_length=240)
    desired_outcome: str = Field(min_length=3, max_length=240)
    systems: list[str] = Field(min_length=1, max_length=12)
    steps: list[WorkflowStep] = Field(min_length=1, max_length=30)
    exceptions: list[str] = Field(default_factory=list, max_length=20)
    frequency_per_week: int = Field(ge=0, le=10000)
    minutes_per_run: int = Field(ge=1, le=1440)
    error_cost: RiskLevel
    data_sensitivity: RiskLevel
    rule_stability: int = Field(ge=1, le=5)
    reversibility: int = Field(ge=1, le=5)
    unstructured_input_ratio: float = Field(ge=0, le=1)

    @field_validator("systems", "exceptions")
    @classmethod
    def clean_list(cls, values: list[str]) -> list[str]:
        cleaned = [item.strip() for item in values if item.strip()]
        if len(cleaned) != len(set(item.casefold() for item in cleaned)):
            raise ValueError("duplicate values are not allowed")
        return cleaned


class EvidenceItem(BaseModel):
    evidence_id: str
    statement: str
    source: str = "workflow_interview"


class WorkflowRecord(WorkflowCreate):
    workflow_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    evidence: list[EvidenceItem]


class OptionScore(BaseModel):
    kind: RecommendationKind
    score: int = Field(ge=0, le=100)
    explanation: str


class Assessment(BaseModel):
    assessment_id: str
    workflow_id: str
    recommendation: RecommendationKind
    confidence: str
    options: list[OptionScore]
    reasons: list[str]
    evidence_ids: list[str]
    risks: list[str]
    human_checkpoints: list[str]
    unknowns: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PilotCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    scenario_id: str = Field(pattern=r"^(shared-inbox|weekly-status|invoice-exceptions)$")


class PilotRecord(PilotCreate):
    pilot_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScenarioRecord(BaseModel):
    record_id: str
    adapter: str
    subject: str
    body: str
    fields: dict[str, Any] = Field(default_factory=dict)


class PilotDecision(BaseModel):
    record_id: str
    disposition: str
    explanation: str
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str]
    human_checkpoint: str | None = None


class PilotRun(BaseModel):
    run_id: str
    pilot_id: str
    fingerprint: str
    status: str
    decisions: list[PilotDecision]
    processed: int
    automated: int
    held_for_review: int
    blocked: int
    synthetic_baseline_minutes: int
    synthetic_pilot_minutes: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AudienceBrief(BaseModel):
    audience: Audience
    title: str
    explanation: str
    what_changes: list[str]
    what_does_not_change: list[str]
    evidence_ids: list[str]


class ModelAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: str = Field(
        default="Identify the safest useful role for AI in this workflow.",
        min_length=12,
        max_length=300,
    )


class EvidenceBoundObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim: str = Field(min_length=3, max_length=600)
    evidence_ids: list[str] = Field(min_length=1, max_length=12)
    confidence: float = Field(ge=0, le=1)


class ProposedToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(pattern=r"^(hold_for_review|draft_pilot_note)$")
    reason: str = Field(min_length=3, max_length=300)
    evidence_ids: list[str] = Field(min_length=1, max_length=12)
    requires_approval: bool = True


class StructuredModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=3, max_length=800)
    summary_evidence_ids: list[str] = Field(min_length=1, max_length=12)
    observations: list[EvidenceBoundObservation] = Field(min_length=1, max_length=8)
    proposed_tools: list[ProposedToolCall] = Field(default_factory=list, max_length=4)
    abstain: bool
    abstention_reason: str | None = Field(default=None, max_length=400)


class ModelUsage(BaseModel):
    input_tokens: int | None = Field(default=None, ge=0, strict=True)
    output_tokens: int | None = Field(default=None, ge=0, strict=True)
    estimated_cost_usd: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class ModelAttempt(BaseModel):
    phase: str = "primary"
    provider: str
    model: str
    status: str
    retry_index: int = Field(default=0, ge=0)
    latency_ms: int = Field(default=0, ge=0)
    usage: ModelUsage = Field(default_factory=ModelUsage)
    error_category: str | None = None


class ModelTrace(BaseModel):
    trace_id: str
    workflow_id: str
    provider: str
    model: str
    prompt_version: str
    prompt_hash: str
    schema_version: str
    status: ModelRunStatus
    latency_ms: int = Field(ge=0)
    retry_count: int = Field(ge=0)
    usage: ModelUsage
    # Total usage is null if any attempt is unknown. Reported usage is only a subtotal.
    reported_usage: ModelUsage | None = None
    attempts: list[ModelAttempt] = Field(default_factory=list)
    # Reference/numeric validation is not a semantic entailment proof.
    semantic_review_required: Literal[True] = True
    output: StructuredModelOutput
    error_category: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
