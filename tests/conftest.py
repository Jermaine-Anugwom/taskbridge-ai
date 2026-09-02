from __future__ import annotations

import pytest

from taskbridge.engine import capture_workflow
from taskbridge.models import RiskLevel, WorkflowCreate, WorkflowStep


def workflow_payload(**overrides) -> WorkflowCreate:
    data = {
        "name": "Shared inbox routing",
        "summary": "The operations team reads requests and routes each message to the right queue.",
        "trigger": "A request arrives in the shared service inbox.",
        "desired_outcome": "A complete request reaches the correct owner.",
        "systems": ["Email", "Ticket queue"],
        "steps": [
            WorkflowStep(
                step_id="step-read",
                actor="Coordinator",
                action="read the request and identify the account",
                system="Email",
                minutes=4,
            ),
            WorkflowStep(
                step_id="step-route",
                actor="Coordinator",
                action="select a service queue or hold the request",
                system="Ticket queue",
                minutes=3,
                is_decision=True,
            ),
        ],
        "exceptions": ["Missing account number", "Request spans two service teams"],
        "frequency_per_week": 180,
        "minutes_per_run": 8,
        "error_cost": RiskLevel.MEDIUM,
        "data_sensitivity": RiskLevel.MEDIUM,
        "rule_stability": 4,
        "reversibility": 4,
        "unstructured_input_ratio": 0.7,
    }
    data.update(overrides)
    return WorkflowCreate.model_validate(data)


@pytest.fixture
def captured_workflow():
    return capture_workflow(workflow_payload(), "wf-test")
