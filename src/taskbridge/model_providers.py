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

from .models import ModelAttempt, ModelUsage, StructuredModelOutput


@dataclass(frozen=True)
class ProviderResult:
    output: StructuredModelOutput
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    retry_count: int = 0
    attempts: tuple[ModelAttempt, ...] = ()


class ProviderFailure(ValueError):
    """Safe error carrying accounting metadata, never raw responses or credentials."""

    def __init__(self, category: str, attempts: list[ModelAttempt]):
        super().__init__("Model response did not match the required tool schema or transport failed")
        self.category = category
        self.attempts = tuple(attempts)


def reported_usage(payload: object) -> ModelUsage:
    usage = payload.get("usage") if isinstance(payload, dict) else None
    if not isinstance(usage, dict):
        return ModelUsage()

    def tokens(key: str) -> int | None:
        value = usage.get(key)
        return value if type(value) is int and value >= 0 else None

    return ModelUsage(input_tokens=tokens("prompt_tokens"), output_tokens=tokens("completion_tokens"))


class StructuredModel(Protocol):
    def complete(self, system: str, user: str) -> ProviderResult: ...


class DeterministicModel:
    def complete(self, system: str, user: str) -> ProviderResult:
        del system
        evidence_ids = [token.rstrip(":,.") for token in user.split() if token.startswith("ev-")]
        evidence_ids = list(dict.fromkeys(evidence_ids)) or ["ev-trigger"]
        output = StructuredModelOutput(
            summary="The deterministic runtime preserved the evidence boundary and queued review.",
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

    def __post_init__(self) -> None:
        if not 0 <= self.max_retries <= 5 or not 1 <= self.timeout_seconds <= 120:
            raise ValueError("Provider retries or timeout are outside allowed bounds")

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
                "max_tokens": 1600,
            }
        ).encode()
        return body

    def complete(self, system: str, user: str) -> ProviderResult:
        body = self._request_body(system, user)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        attempts: list[ModelAttempt] = []
        for attempt in range(self.max_retries + 1):
            request = urllib.request.Request(self.endpoint, data=body, headers=headers, method="POST")
            started = time.perf_counter()
            record = ModelAttempt(
                provider=self.provider_name, model=self.model, status="started", retry_index=attempt,
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                    payload = json.loads(response.read())
                # Capture usage before any schema or evidence validation can reject the response.
                record.usage = reported_usage(payload)
                if isinstance(payload, dict) and isinstance(payload.get("model"), str):
                    record.model = payload["model"]
                message = payload["choices"][0]["message"]
                calls = message["tool_calls"]
                if len(calls) != 1 or calls[0]["function"]["name"] != "record_workflow_analysis":
                    raise ValueError("Unexpected tool contract")
                arguments = calls[0]["function"]["arguments"]
                output = StructuredModelOutput.model_validate_json(arguments)
                record.status = "returned"
                record.latency_ms = max(1, round((time.perf_counter() - started) * 1000))
                attempts.append(record)
                return ProviderResult(
                    output=output,
                    provider=self.provider_name,
                    model=record.model,
                    input_tokens=record.usage.input_tokens,
                    output_tokens=record.usage.output_tokens,
                    retry_count=attempt,
                    attempts=tuple(attempts),
                )
            except HTTPError as exc:
                record.status = "transport_error"
                record.error_category = f"HTTP{exc.code}"
                # Some providers include usage even in non-2xx JSON responses.
                try:
                    record.usage = reported_usage(json.loads(exc.read()))
                except (ValueError, TypeError, AttributeError):
                    pass
                retry = exc.code in {408, 409, 429, 500, 502, 503, 504}
            except (TimeoutError, URLError, socket.timeout) as exc:
                record.status = "transport_error"
                record.error_category = type(exc).__name__
                retry = True
            except (KeyError, IndexError, TypeError, ValueError, ValidationError):
                record.status = "schema_rejected"
                record.error_category = "InvalidToolSchema"
                retry = False
            record.latency_ms = max(1, round((time.perf_counter() - started) * 1000))
            attempts.append(record)
            if not retry or attempt == self.max_retries:
                raise ProviderFailure(record.error_category or "ProviderError", attempts) from None
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
