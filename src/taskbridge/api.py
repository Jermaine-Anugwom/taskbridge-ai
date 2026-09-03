from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from .engine import assess_workflow, capture_workflow, explain_assessment, simulate_pilot
from .auth import Role, auth_required, require_role, validate_runtime_config
from .handoff import render_handoff
from .models import (
    Assessment,
    Audience,
    AudienceBrief,
    ModelAnalysisRequest,
    ModelTrace,
    PilotCreate,
    PilotRecord,
    PilotRun,
    WorkflowCreate,
    WorkflowRecord,
)
from .model_providers import configured_model
from .model_runtime import run_model_analysis, trace_fingerprint
from .repository import Repository
from .scenarios import load_scenario
from .security import UntrustedInstructionError


def create_app(database_path: str | Path | None = None) -> FastAPI:
    database = str(database_path
        or os.getenv("TASKBRIDGE_DATABASE_URL")
        or os.getenv("TASKBRIDGE_DB", "taskbridge.db")
    )
    validate_runtime_config(database)
    repository = Repository(database)
    app = FastAPI(title="TaskBridge AI", version="0.2.1")

    @app.get("/health")
    def health() -> dict[str, str | bool]:
        return {
            "status": "healthy",
            "mode": os.getenv("TASKBRIDGE_MODEL_PROVIDER", "deterministic"),
            "database": repository.backend,
            "auth_required": auth_required(),
        }

    @app.post("/api/workflows", response_model=WorkflowRecord, status_code=201)
    def create_workflow(
        payload: WorkflowCreate, _: Role = Depends(require_role(Role.OPERATOR))
    ) -> WorkflowRecord:
        try:
            record = capture_workflow(payload, f"wf-{uuid.uuid4().hex[:12]}")
        except UntrustedInstructionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        repository.save("workflows", record.workflow_id, record)
        return record

    @app.post("/api/workflows/{workflow_id}/assess", response_model=Assessment)
    def assess(
        workflow_id: str, _: Role = Depends(require_role(Role.OPERATOR))
    ) -> Assessment:
        data = repository.get("workflows", workflow_id)
        if not data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        workflow = WorkflowRecord.model_validate(data)
        digest = hashlib.sha256(workflow.model_dump_json().encode()).hexdigest()[:12]
        result = assess_workflow(workflow, f"assess-{digest}")
        repository.save("assessments", result.assessment_id, result, workflow_id=workflow_id)
        return result

    @app.post("/api/pilots", response_model=PilotRecord, status_code=201)
    def create_pilot(
        payload: PilotCreate, _: Role = Depends(require_role(Role.OPERATOR))
    ) -> PilotRecord:
        if not repository.get("workflows", payload.workflow_id):
            raise HTTPException(status_code=404, detail="Workflow not found")
        record = PilotRecord(pilot_id=f"pilot-{uuid.uuid4().hex[:12]}", **payload.model_dump())
        repository.save(
            "pilots",
            record.pilot_id,
            record,
            workflow_id=record.workflow_id,
            scenario_id=record.scenario_id,
        )
        return record

    @app.post("/api/pilots/{pilot_id}/run", response_model=PilotRun)
    def run_pilot(
        pilot_id: str, _: Role = Depends(require_role(Role.OPERATOR))
    ) -> PilotRun:
        data = repository.get("pilots", pilot_id)
        if not data:
            raise HTTPException(status_code=404, detail="Pilot not found")
        pilot = PilotRecord.model_validate(data)
        records = load_scenario(pilot.scenario_id)
        result = simulate_pilot(pilot.pilot_id, pilot.scenario_id, records)
        if existing := repository.get_run_by_fingerprint(result.fingerprint):
            return PilotRun.model_validate(existing)
        repository.save(
            "pilot_runs",
            result.run_id,
            result,
            pilot_id=pilot.pilot_id,
            fingerprint=result.fingerprint,
        )
        return result

    def _workflow_and_assessment(pilot_id: str) -> tuple[WorkflowRecord, Assessment]:
        pilot_data = repository.get("pilots", pilot_id)
        if not pilot_data:
            raise HTTPException(status_code=404, detail="Pilot not found")
        pilot = PilotRecord.model_validate(pilot_data)
        workflow_data = repository.get("workflows", pilot.workflow_id)
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        workflow = WorkflowRecord.model_validate(workflow_data)
        assessment = assess_workflow(workflow, f"assess-{workflow.workflow_id}")
        return workflow, assessment

    @app.get("/api/pilots/{pilot_id}/explanations", response_model=AudienceBrief)
    def explanations(
        pilot_id: str,
        audience: Audience,
        _: Role = Depends(require_role(Role.VIEWER)),
    ) -> AudienceBrief:
        workflow, assessment = _workflow_and_assessment(pilot_id)
        return explain_assessment(workflow, assessment, audience)

    @app.get("/api/pilots/{pilot_id}/handoff", response_class=PlainTextResponse)
    def handoff(
        pilot_id: str, _: Role = Depends(require_role(Role.VIEWER))
    ) -> str:
        workflow, assessment = _workflow_and_assessment(pilot_id)
        return render_handoff(workflow, assessment)

    @app.post("/api/workflows/{workflow_id}/model-analysis", response_model=ModelTrace)
    def model_analysis(
        workflow_id: str,
        payload: ModelAnalysisRequest,
        _: Role = Depends(require_role(Role.OPERATOR)),
    ) -> ModelTrace:
        data = repository.get("workflows", workflow_id)
        if not data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        workflow = WorkflowRecord.model_validate(data)
        result = run_model_analysis(workflow, payload.task, configured_model())
        repository.save(
            "model_traces",
            result.trace_id,
            result,
            workflow_id=workflow_id,
            fingerprint=trace_fingerprint(result),
        )
        return result

    @app.get("/api/operations/model-traces", response_model=list[ModelTrace])
    def model_traces(
        limit: int = 20, _: Role = Depends(require_role(Role.VIEWER))
    ) -> list[ModelTrace]:
        return [ModelTrace.model_validate(item) for item in repository.list_model_traces(limit)]

    return app


app = create_app()
