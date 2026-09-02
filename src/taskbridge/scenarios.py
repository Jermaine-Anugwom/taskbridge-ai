from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .models import ScenarioRecord


@lru_cache(maxsize=1)
def load_all_records() -> list[ScenarioRecord]:
    path = Path(__file__).resolve().parents[2] / "fixtures" / "records.json"
    return [ScenarioRecord.model_validate(item) for item in json.loads(path.read_text())]


def load_scenario(scenario_id: str, limit: int = 12) -> list[ScenarioRecord]:
    records = [item for item in load_all_records() if item.fields.get("scenario_id") == scenario_id]
    if not records:
        raise KeyError(f"unknown scenario: {scenario_id}")
    return records[:limit]
