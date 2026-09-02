from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class StructuredModel(Protocol):
    def complete(self, system: str, user: str) -> dict: ...


class DeterministicModel:
    def complete(self, system: str, user: str) -> dict:
        return {
            "mode": "deterministic",
            "summary": "No external model was called.",
            "input_characters": len(user),
        }


@dataclass(frozen=True)
class JsonEndpointModel:
    endpoint: str
    model: str
    api_key: str | None = None
    timeout_seconds: int = 20

    def complete(self, system: str, user: str) -> dict:
        body = json.dumps(
            {"model": self.model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "stream": False}
        ).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(self.endpoint, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
            return json.loads(response.read())


def configured_model() -> StructuredModel:
    provider = os.getenv("TASKBRIDGE_MODEL_PROVIDER", "deterministic")
    if provider == "deterministic":
        return DeterministicModel()
    if provider == "ollama":
        return JsonEndpointModel(
            endpoint=os.getenv("TASKBRIDGE_MODEL_ENDPOINT", "http://127.0.0.1:11434/api/chat"),
            model=os.getenv("TASKBRIDGE_MODEL_NAME", "qwen2.5:7b"),
        )
    if provider == "generic":
        endpoint = os.environ["TASKBRIDGE_MODEL_ENDPOINT"]
        return JsonEndpointModel(
            endpoint=endpoint,
            model=os.getenv("TASKBRIDGE_MODEL_NAME", "configured-model"),
            api_key=os.getenv("TASKBRIDGE_MODEL_API_KEY"),
        )
    raise ValueError(f"Unsupported model provider: {provider}")
