from __future__ import annotations

import json
import os
import socket
import time
import urllib.request
from urllib.error import HTTPError, URLError
from dataclasses import dataclass
from typing import Protocol

from pydantic import ValidationError

from .models import StructuredModelOutput


@dataclass(frozen=True)
class ProviderResult:
    output: StructuredModelOutput
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    retry_count: int = 0


class StructuredModel(Protocol):
    def complete(self, system: str, user: str) -> ProviderResult: ...


class DeterministicModel:
    def complete(self, system: str, user: str) -> ProviderResult:
        del system
        evidence_ids = [token.rstrip(":,.") for token in user.split() if token.startswith("ev-")]
        evidence_ids = list(dict.fromkeys(evidence_ids)) or ["ev-trigger"]
        output = StructuredModelOutput(
            summary="The deterministic fallback preserved the evidence boundary and queued review.",
            summary_evidence_ids=evidence_ids[:2],
            observations=[{
                "claim": "A person should review the proposed workflow change.",
                "evidence_ids": evidence_ids[:2],
                "confidence": 1,
            }],
            proposed_tools=[{
                "tool_name": "hold_for_review",
                "reason": "The external model was unavailable or intentionally disabled.",
                "evidence_ids": evidence_ids[:2],
                "requires_approval": True,
            }],
            abstain=True,
            abstention_reason="No external model result was available.",
        )
        return ProviderResult(
            output=output,
            provider="deterministic",
            model="taskbridge-fallback-v1",
            input_tokens=0,
            output_tokens=0,
        )


@dataclass(frozen=True)
class OpenAICompatibleModel:
    endpoint: str
    model: str
    api_key: str | None = None
    timeout_seconds: int = 20
    max_retries: int = 2
    provider_name: str = "openai_compatible"

    def _request_body(self, system: str, user: str) -> bytes:
        schema = StructuredModelOutput.model_json_schema()
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "tools": [{
                    "type": "function",
                    "function": {
                        "name": "record_workflow_analysis",
                        "description": "Record evidence-bound analysis and approval-gated tool proposals.",
                        "parameters": schema,
                    },
                }],
                "tool_choice": {
                    "type": "function",
                    "function": {"name": "record_workflow_analysis"},
                },
                "stream": False,
            }
        ).encode()
        return body

    def complete(self, system: str, user: str) -> ProviderResult:
        body = self._request_body(system, user)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        for attempt in range(self.max_retries + 1):
            request = urllib.request.Request(self.endpoint, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                    payload = json.loads(response.read())
                message = payload["choices"][0]["message"]
                arguments = message["tool_calls"][0]["function"]["arguments"]
                output = StructuredModelOutput.model_validate_json(arguments)
                usage = payload.get("usage") or {}
                return ProviderResult(
                    output=output,
                    provider=self.provider_name,
                    model=str(payload.get("model") or self.model),
                    input_tokens=int(usage.get("prompt_tokens") or 0),
                    output_tokens=int(usage.get("completion_tokens") or 0),
                    retry_count=attempt,
                )
            except HTTPError as exc:
                if exc.code not in {408, 409, 429, 500, 502, 503, 504} or attempt == self.max_retries:
                    raise
            except (TimeoutError, URLError, socket.timeout):
                if attempt == self.max_retries:
                    raise
            except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValidationError):
                raise ValueError("Model response did not match the required tool schema") from None
            time.sleep(0.25 * (2**attempt))
        raise RuntimeError("Model request retry loop ended unexpectedly")


def configured_model() -> StructuredModel:
    provider = os.getenv("TASKBRIDGE_MODEL_PROVIDER", "deterministic")
    if provider == "deterministic":
        return DeterministicModel()
    if provider == "ollama":
        return OpenAICompatibleModel(
            endpoint=os.getenv("TASKBRIDGE_MODEL_ENDPOINT", "http://127.0.0.1:11434/v1/chat/completions"),
            model=os.getenv("TASKBRIDGE_MODEL_NAME", "qwen2.5:7b"),
            provider_name="ollama",
        )
    if provider in {"generic", "openai_compatible"}:
        endpoint = os.environ["TASKBRIDGE_MODEL_ENDPOINT"]
        return OpenAICompatibleModel(
            endpoint=endpoint,
            model=os.getenv("TASKBRIDGE_MODEL_NAME", "configured-model"),
            api_key=os.getenv("TASKBRIDGE_MODEL_API_KEY"),
            timeout_seconds=int(os.getenv("TASKBRIDGE_MODEL_TIMEOUT_SECONDS", "20")),
            max_retries=int(os.getenv("TASKBRIDGE_MODEL_MAX_RETRIES", "2")),
            provider_name=os.getenv("TASKBRIDGE_MODEL_PROVIDER_NAME", "openai_compatible"),
        )
    raise ValueError(f"Unsupported model provider: {provider}")
